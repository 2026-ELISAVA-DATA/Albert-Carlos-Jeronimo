from playwright.sync_api import sync_playwright
import time
import json
import csv
from datetime import datetime

SEARCH_URL = "https://duckduckgo.com/?q=skate+macba&t=chromentp&ia=web"

def extract_result_data(r):
    """Extract title, URL, date, and description from a result element."""
    # Title and URL
    title_link = r.query_selector("a[data-testid='result-title-a']")
    url = title_link.get_attribute("href") if title_link else None
    title = title_link.inner_text().strip() if title_link else ""

    # Snippet/description - try multiple selectors
    snippet = ""
    for selector in [
        "div[data-result='snippet']",
        "[data-testid='result-snippet']",
        ".result__snippet",
        "div.E2eLOJr8HctVnDOTM8fs",
    ]:
        el = r.query_selector(selector)
        if el:
            snippet = el.inner_text().strip()
            break

    # Date - DDG sometimes shows it in the snippet or a dedicated element
    date = ""
    for selector in [
        "span[data-testid='result-extras-url-date']",
        "time",
        ".result__url",
    ]:
        el = r.query_selector(selector)
        if el:
            candidate = el.get_attribute("datetime") or el.inner_text().strip()
            if any(c.isdigit() for c in candidate):
                date = candidate
                break

    return {
        "title": title,
        "url": url,
        "date": date,
        "description": snippet,
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def click_more_and_collect(page, max_clicks=50, pause=2.0):
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
    page = context.new_page()
    page.goto(SEARCH_URL)
    time.sleep(5)

    raw_results = click_more_and_collect(page, max_clicks=10, pause=2)
    print(f"Total raw results collected: {len(raw_results)}")

    # Extract data and deduplicate by URL
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

    print(f"Unique results after dedup: {len(data)}")

    # --- Save JSON ---
    json_path = "results_skate_macba.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON saved -> {json_path}")

    # --- Save CSV ---
    csv_path = "results_skate_macba.csv"
    fieldnames = ["title", "url", "date", "description", "scraped_at"]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"CSV saved -> {csv_path}")



