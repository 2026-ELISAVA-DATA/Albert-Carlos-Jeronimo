from playwright.sync_api import sync_playwright
import time
import json
import csv

SEARCH_QUERIES = [
    "MACBA skate",
    "MACBA skateboarding",
    "MACBA barcelona skate",
    "skate MACBA plaza",
    "MACBA skaters",
    "MACBA barcelona skating",
    "museo MACBA skate",
    "MACBA skate barcelona street",
    "MACBA spot skate",
    "patinaje MACBA barcelona",
]

def build_search_url(query):
    encoded = query.replace(" ", "%20")
    return f"https://x.com/search?q={encoded}&f=live"

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
    """Wait until at least 1 tweet is visible, return False if timeout."""
    start = time.time()
    while time.time() - start < timeout:
        articles = page.query_selector_all("article[role='article']")
        if len(articles) > 0:
            return True
        time.sleep(1)
    return False

def retry_if_empty(page, url, max_retries=3):
    """Reload the page up to max_retries times if no tweets appear."""
    for attempt in range(max_retries):
        print(f"  Loading attempt {attempt + 1}/{max_retries}...")
        page.goto(url)
        time.sleep(5)

        # Click refresh button if Twitter shows it
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

def scroll_and_collect(page, query, scroll_times=30, scroll_pause=2.0):
    seen_urls = set()
    results = []
    empty_scroll_streak = 0  # track consecutive scrolls with no new tweets

    for i in range(scroll_times):
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

        # Track if we're stuck
        if new_this_scroll == 0:
            empty_scroll_streak += 1
            print(f"  No new tweets this scroll ({empty_scroll_streak} in a row)")
        else:
            empty_scroll_streak = 0

        # If 5 scrolls in a row yield nothing, try clicking Twitter's refresh button
        if empty_scroll_streak == 5:
            print("  Stuck — trying to click Twitter refresh button...")
            try:
                refresh_btn = page.query_selector("[data-testid='cellInnerDiv'] [role='button']")
                if refresh_btn:
                    refresh_btn.click()
                    time.sleep(4)
                    empty_scroll_streak = 0
                else:
                    print("  No refresh button found, stopping this query.")
                    break
            except Exception:
                print("  Could not click refresh, stopping this query.")
                break

        # Login wall check
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
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.new_page()

    all_data = []
    seen_keys = set()

    for query in SEARCH_QUERIES:
        print(f"\n{'='*50}")
        print(f"Searching: {query}")
        print(f"{'='*50}")

        search_url = build_search_url(query)

        # Try loading the page, retry if empty
        loaded = retry_if_empty(page, search_url, max_retries=3)
        if not loaded:
            print(f"  Could not load tweets for '{query}', skipping.")
            time.sleep(5)
            continue

        results = scroll_and_collect(page, query=query, scroll_times=30, scroll_pause=2)

        new_count = 0
        for item in results:
            key = item["url"] or item["description"]
            if key and key not in seen_keys:
                seen_keys.add(key)
                all_data.append(item)
                new_count += 1

        print(f"  -> {new_count} new unique tweets (total so far: {len(all_data)})")

        # Longer pause between queries to avoid throttling
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
