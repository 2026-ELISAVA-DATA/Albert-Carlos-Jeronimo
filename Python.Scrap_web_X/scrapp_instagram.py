from playwright.sync_api import sync_playwright
import time
import json
import csv

HASHTAGS = [
    "MACBAskate",
    "MACBAskateboarding",
    "MACBAbarcelona",
    "skateMACBA",
    "MACBAskaters",
    "MACBAskating",
    "MACBAspot",
    "skatebarcelonaMACBA",
    "MACBAplaza",
    "barcelonaskate",
    "macbask8",
    "saveMACBA",
    "MACBAskatepark",
    "patinajeMACBA",
]

def build_hashtag_url(hashtag):
    return f"https://www.instagram.com/explore/tags/{hashtag}/"

def wait_for_posts(page, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        posts = page.query_selector_all("article a[href*='/p/']")
        if len(posts) > 0:
            return True
        time.sleep(1)
    return False

def check_and_reload_if_error(page):
    try:
        error = page.query_selector("span:has-text('Something went wrong')")
        if not error:
            error = page.query_selector("span:has-text('Try again')")
        if error:
            print("  Instagram error detected — reloading...")
            page.reload()
            time.sleep(6)
            return True
    except Exception:
        pass
    return False

def close_popup_if_open(page):
    """Close login popups or notification prompts."""
    try:
        # "Not now" button for notifications
        not_now = page.query_selector("button:has-text('Not Now')")
        if not_now:
            not_now.click()
            print("  Closed notification popup")
            time.sleep(1)
        # Close login modal if appears
        close = page.query_selector("[aria-label='Close']")
        if close:
            close.click()
            time.sleep(1)
    except Exception:
        pass

def get_post_description(page, url):
    """Visit a post URL and extract the caption."""
    try:
        page.goto(url, timeout=15000, wait_until="domcontentloaded")
        time.sleep(3)
        close_popup_if_open(page)

        # Try multiple selectors for the caption
        for selector in [
            "div[data-testid='post-comment-root'] span",
            "article div:nth-child(1) span",
            "h1",
            "div._a9zs span",
        ]:
            el = page.query_selector(selector)
            if el:
                text = el.inner_text().strip()
                if text and len(text) > 5:
                    return text
    except Exception as e:
        print(f"  Could not get description: {e}")
    return ""

def get_post_date(page):
    """Extract post date from the post page."""
    try:
        time_el = page.query_selector("time[datetime]")
        if time_el:
            return time_el.get_attribute("datetime") or ""
    except Exception:
        pass
    return ""

def scroll_and_collect_links(page, hashtag, scroll_times=20, scroll_pause=3.0):
    """Scroll through hashtag page and collect post links."""
    seen_urls = set()
    results = []
    empty_scroll_streak = 0

    for i in range(scroll_times):
        check_and_reload_if_error(page)
        close_popup_if_open(page)

        # Get all post links visible on page
        post_links = page.query_selector_all("a[href*='/p/']")
        print(f"  Scroll {i+1}: {len(post_links)} posts visible")

        new_this_scroll = 0
        for link in post_links:
            href = link.get_attribute("href")
            if href:
                full_url = f"https://www.instagram.com{href}" if href.startswith("/") else href
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    results.append(full_url)
                    new_this_scroll += 1

        if new_this_scroll == 0:
            empty_scroll_streak += 1
            print(f"  No new posts this scroll ({empty_scroll_streak} in a row)")
        else:
            empty_scroll_streak = 0

        if empty_scroll_streak == 3:
            print("  Still stuck, stopping this hashtag.")
            break

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(scroll_pause)

    return results

# --- Main ---
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")

    context = browser.contexts[0]
    
    # Page for scrolling hashtags
    scroll_page = context.pages[0]
    
    # Separate page for visiting individual posts
    post_page = context.new_page()

    all_links = []
    seen_links = set()

    # Step 1: Collect all post links from hashtag pages
    for hashtag in HASHTAGS:
        print(f"\n{'='*50}")
        print(f"Hashtag: #{hashtag}")
        print(f"{'='*50}")

        url = build_hashtag_url(hashtag)
        scroll_page.goto(url)
        time.sleep(5)
        close_popup_if_open(scroll_page)

        if not wait_for_posts(scroll_page, timeout=15):
            print(f"  No posts found for #{hashtag}, skipping.")
            time.sleep(5)
            continue

        links = scroll_and_collect_links(scroll_page, hashtag, scroll_times=20, scroll_pause=3.0)

        new_count = 0
        for link in links:
            if link not in seen_links:
                seen_links.add(link)
                all_links.append({"url": link, "query": f"#{hashtag}"})
                new_count += 1

        print(f"  -> {new_count} new posts (total so far: {len(all_links)})")
        print("  Pausing 15s before next hashtag...")
        time.sleep(15)

    print(f"\nTotal unique posts found: {len(all_links)}")
    print("Now visiting each post to get description and date...")

    # Step 2: Visit each post to get description and date
    all_data = []
    for i, item in enumerate(all_links):
        print(f"[{i+1}/{len(all_links)}] Fetching: {item['url']}")
        
        description = get_post_description(post_page, item["url"])
        date = get_post_date(post_page)

        all_data.append({
            "title": "",
            "url": item["url"],
            "date": date,
            "description": description,
            "query": item["query"],
        })

        # Save progress every 50 posts in case it crashes
        if (i + 1) % 50 == 0:
            print(f"  Saving progress at {i+1} posts...")
            with open("instagram_macba_skate_progress.json", "w", encoding="utf-8") as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)

        time.sleep(2)

    print(f"\nTotal posts with data: {len(all_data)}")

    # --- Save JSON ---
    json_path = "instagram_macba_skate.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"JSON saved -> {json_path}")

    # --- Save CSV ---
    csv_path = "instagram_macba_skate.csv"
    fieldnames = ["title", "url", "date", "description", "query"]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    print(f"CSV saved -> {csv_path}")
    print(f"Final dataset: {len(all_data)} unique posts")
