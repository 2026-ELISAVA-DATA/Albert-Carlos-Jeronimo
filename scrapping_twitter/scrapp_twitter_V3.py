from playwright.sync_api import sync_playwright
import time
import json
import csv

SEARCH_QUERIES = [
    "MACBA skate",
    "MACBA skateboarding",
    "MACBA barcelona",
    "skate MACBA",
    "MACBA skaters",
    "MACBA skating",
    "museo MACBA skate",
    "MACBA spot",
    "patinaje MACBA",
    "skate barcelona MACBA",
    "MACBA plaza skate",
    "barcelona skate plaza",
    "macba sk8",
    "macba skatepark",
]

def build_search_url(query):
    encoded = query.replace(" ", "%20")
    return f"https://x.com/search?q={encoded}&f=live"

def close_grok_if_open(page):
    try:
        close_btn = page.query_selector("[aria-label='Close']")
        if close_btn:
            close_btn.click()
            print("  Closed Grok panel")
            time.sleep(1)
        dismiss = page.query_selector("[data-testid='app-bar-close']")
        if dismiss:
            dismiss.click()
            time.sleep(1)
    except Exception:
        pass

def extract_tweet_data(article, query=""):
    try:
        user_el = article.query_selector("div[data-testid='User-Name']")
        title = user_el.inner_text().replace("\n", " ").strip() if user_el else ""

        text_el = article.query_selector("div[data-testid='tweetText']")
        description = text_el.inner_text().strip() if text_el else ""

        url = ""
        time_el = article.query_selector("time")
        if time_el:
            parent = time_el.evaluate_handle("el => el.closest('a')")
            if parent:
                href = parent.get_attribute("href")
                if href:
                    url = f"https://x.com{href}" if href.startswith("/") else href

        date = ""
        if time_el:
            date = time_el.get_attribute("datetime") or ""

        return {
            "title": title,
            "url": url,
            "date": date,
            "description": description,
            "query": query,
        }
    except Exception as e:
        print(f"  Error parsing tweet: {e}")
        return None

def wait_for_tweets(page, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        articles = page.query_selector_all("article[role='article']")
        if len(articles) > 0:
            return True
        time.sleep(1)
    return False

def retry_if_empty(page, url, max_retries=3):
    for attempt in range(max_retries):
        print(f"  Loading attempt {attempt + 1}/{max_retries}...")
        page.goto(url)
        time.sleep(6)

        close_grok_if_open(page)

        try:
            refresh_btn = page.query_selector("[data-testid='cellInnerDiv'] [role='button']")
            if refresh_btn:
                refresh_btn.click()
                print("  Clicked Twitter refresh button")
                time.sleep(3)
        except Exception:
            pass

        if wait_for_tweets(page, timeout=15):
            print(f"  Tweets loaded on attempt {attempt + 1}")
            return True

        print(f"  No tweets yet, retrying in 5s...")
        time.sleep(5)

    return False

def scroll_and_collect(page, query, scroll_times=30, scroll_pause=2.5):
    close_grok_if_open(page)

    seen_urls = set()
    results = []
    empty_scroll_streak = 0

    for i in range(scroll_times):
        # Check and close Grok every 5 scrolls
        if i % 5 == 0:
            close_grok_if_open(page)

        articles = page.query_selector_all("article[role='article']")
        print(f"  Scroll {i+1}: {len(articles)} tweets visible")

        new_this_scroll = 0
        for article in articles:
            item = extract_tweet_data(article, query=query)
            if not item:
                continue

            key = item["url"] or item["description"]
            if key and key not in seen_urls:
                seen_urls.add(key)
                results.append(item)
                new_this_scroll += 1

        if new_this_scroll == 0:
            empty_scroll_streak += 1
            print(f"  No new tweets this scroll ({empty_scroll_streak} in a row)")
        else:
            empty_scroll_streak = 0

        if empty_scroll_streak == 3:
            print("  Stuck — scrolling up to trigger reload...")
            close_grok_if_open(page)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(2)
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
            empty_scroll_streak = 0

        if empty_scroll_streak == 6:
            print("  Still stuck, stopping this query.")
            break

        wall = page.query_selector("[data-testid='LoginForm']") or \
               page.query_selector("[data-testid='signupButton']")
        if wall:
            print("  Login wall detected, stopping.")
            break

        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(scroll_pause)

    return results

# --- Main ---
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")

    context = browser.contexts[0]
    page = context.pages[0]

    # Close Grok at the very start
    close_grok_if_open(page)

    all_data = []
    seen_keys = set()

    for query in SEARCH_QUERIES:
        print(f"\n{'='*50}")
        print(f"Searching: {query}")
        print(f"{'='*50}")

        search_url = build_search_url(query)

        loaded = retry_if_empty(page, search_url, max_retries=3)
        if not loaded:
            print(f"  Could not load tweets for '{query}', skipping.")
            time.sleep(5)
            continue

        results = scroll_and_collect(page, query=query, scroll_times=30, scroll_pause=2.5)

        new_count = 0
        for item in results:
            key = item["url"] or item["description"]
            if key and key not in seen_keys:
                seen_keys.add(key)
                all_data.append(item)
                new_count += 1

        print(f"  -> {new_count} new unique tweets (total so far: {len(all_data)})")
        print("  Pausing 10s before next query...")
        time.sleep(10)

    print(f"\nTotal unique tweets: {len(all_data)}")

    # --- Save JSON ---
    json_path = "tweets_macba_skate.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"JSON saved -> {json_path}")

    # --- Save CSV ---
    csv_path = "tweets_macba_skate.csv"
    fieldnames = ["title", "url", "date", "description", "query"]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    print(f"CSV saved -> {csv_path}")
    print(f"Final dataset: {len(all_data)} unique tweets")
