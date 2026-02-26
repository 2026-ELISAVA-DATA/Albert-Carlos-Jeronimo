from playwright.sync_api import sync_playwright
import time
import json
import csv
from datetime import datetime
import re

SEARCH_URL = "https://duckduckgo.com/?q=skate+macba&t=chromentp&ia=web"

def extract_date_from_page(page):
    """Try to extract a publication date from the actual article page."""
    date = ""

    # 1. Try common meta tags first (fastest, most reliable)
    for selector in [
        "meta[property='article:published_time']",
        "meta[name='pubdate']",
        "meta[name='publishdate']",
        "meta[name='date']",
        "meta[itemprop='datePublished']",
        "meta[property='og:updated_time']",
    ]:
        el = page.query_selector(selector)
        if el:
            content = el.get_attribute("content")
            if content:
                return content.strip()

    # 2. Try common HTML elements
    for selector in [
        "time[datetime]",
        "time[pubdate]",
        "[itemprop='datePublished']",
        "[class*='date']",
        "[class*='Date']",
        "[class*='published']",
        "[class*='timestamp']",
        "[id*='date']",
    ]:
        el = page.query_selector(selector)
        if el:
            candidate = el.get_attribute("datetime") or el.inner_text().strip()
            # Basic check that it looks like a date
            if candidate and re.search(r'\d{4}', candidate):
                return candidate[:50]  # cap length

    # 3. JSON-LD structured data
    scripts = page.query_selector_all("script[type='application/ld+json']")
    for script in scripts:
        try:
            ld = json.loads(script.inner_text())
            # Handle both single object and list
            if isinstance(ld, list):
                ld = ld[0]
            for key in ["datePublished", "dateCreated", "dateModified"]:
                if key in ld:
                    return ld[key]
        except Exception:
            continue

    return date

def extract_result_data(r):
    """Extract title, URL, date, and description from a DDG result element."""
    title_link = r.query_selector("a[data-testid='result-title-a']")
    url = title_link.get_attribute("href") if title_link else None
    title = title_link.inner_text().strip() if title_link else ""

    snippet = ""
    for selector in [
        "div[data-result='snippet']",
        "[data-testid='result-snippet']",
        ".result__snippet",
    ]:
        el = r.query_selector(selector)
        if el:
            snippet = el.inner_text().strip()
            break

    # Try to get date directly from DDG result
    date = ""
    for selector in [
        "span[data-testid='result-extras-url-date']",
        "time",
    ]:
        el = r.query_selector(selector)
        if el:
            candidate = el.get_attribute("datetime") or el.inner_text().strip()
            if candidate and any(c.isdigit() for c in candidate):
                date = candidate
                break

    return {
        "title": title,
        "url": url,
        "date": date,
        "description": snippet,
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def click_more_and_collect(page, max_clicks=10, pause=2.0):
    seen_ids = set()
    all_results = []

    for i in range(max_clicks):
        results = page.query_selector_all("article[data-testid='result']")
        print(f"Click {i+1}: {len(results)} results visible")

        for r in results:
            try:
                box = r.bounding_box()
                key = (round(box["x"]), round(box["y"])) if box else None
            except Exception:
                key = None

            if key and key not in seen_ids:
                seen_ids.add(key)
                all_results.append(r)

        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        more_btn = page.query_selector("#more-results")
        if more_btn and more_btn.is_enabled():
            try:
                more_btn.click()
                print("Clicked 'More Results'")
            except Exception as e:
                print(f"Could not click More Results: {e}")
                break
            time.sleep(pause)
        else:
            print("No more results or button unavailable.")
            break

    return all_results

# --- Main ---
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0] if browser.contexts else browser.new_context()

    # Page 1: DDG search results
    search_page = context.new_page()
    search_page.goto(SEARCH_URL)
    time.sleep(5)

    raw_results = click_more_and_collect(search_page, max_clicks=10, pause=2)
    print(f"Total raw results collected: {len(raw_results)}")

    # Extract basic data first
    data = []
    seen_urls = set()

    for r in raw_results:
        try:
            item = extract_result_data(r)
        except Exception as e:
            print(f"Error extracting result: {e}")
            continue

        if item["url"] and item["url"] not in seen_urls:
            data.append(item)
            seen_urls.add(item["url"])

    print(f"Unique results: {len(data)}")

    # Page 2: visit each URL to get the date if missing
    article_page = context.new_page()

    for i, item in enumerate(data):
        if item["date"]:
            # Already have a date from DDG, skip
            continue
        try:
            print(f"[{i+1}/{len(data)}] Fetching date from: {item['url']}")
            article_page.goto(item["url"], timeout=10000, wait_until="domcontentloaded")
            time.sleep(1)
            item["date"] = extract_date_from_page(article_page)
        except Exception as e:
            print(f"  Could not fetch page: {e}")
            item["date"] = ""

    article_page.close()

    # --- Save JSON ---
    json_path = "Scrapduck_chrome_datesfixed.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON saved -> {json_path}")

    # --- Save CSV ---
    csv_path = "Scrapduck_chrome_datesfixed.csv"
    fieldnames = ["title", "url", "date", "description", "scraped_at"]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"CSV saved -> {csv_path}")
