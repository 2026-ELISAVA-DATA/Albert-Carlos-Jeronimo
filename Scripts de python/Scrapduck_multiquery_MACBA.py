from playwright.sync_api import sync_playwright
import time
import json
import csv
from datetime import datetime
import re
from urllib.parse import quote_plus

QUERIES = [
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
    "saveMACBA",
    "MACBA skate cultura",
    "MACBA skate historia",
]

def make_ddg_url(query):
    return f"https://duckduckgo.com/?q={quote_plus(query)}&t=chromentp&ia=web"

def extract_date_from_page(page):
    """Try to extract a publication date from the actual article page."""
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
            if candidate and re.search(r'\d{4}', candidate):
                return candidate[:50]

    scripts = page.query_selector_all("script[type='application/ld+json']")
    for script in scripts:
        try:
            ld = json.loads(script.inner_text())
            if isinstance(ld, list):
                ld = ld[0]
            for key in ["datePublished", "dateCreated", "dateModified"]:
                if key in ld:
                    return ld[key]
        except Exception:
            continue

    return ""

def extract_result_data(r, query):
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
        "query": query,
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

def click_more_and_collect(page, query, max_clicks=40, pause=2.0):
    seen_ids = set()
    all_results = []

    for i in range(max_clicks):
        results = page.query_selector_all("article[data-testid='result']")
        print(f"  Click {i+1}: {len(results)} results visible")

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
                print("  Clicked 'More Results'")
            except Exception as e:
                print(f"  Could not click More Results: {e}")
                break
            time.sleep(pause)
        else:
            print("  No more results or button unavailable.")
            break

    return all_results

# --- Main ---
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0] if browser.contexts else browser.new_context()

    all_data = []
    seen_urls = set()

    search_page = context.new_page()

    for q_idx, query in enumerate(QUERIES):
        print(f"\n[Query {q_idx+1}/{len(QUERIES)}] '{query}'")
        url = make_ddg_url(query)
        search_page.goto(url)
        time.sleep(5)  # wait for DDG to load

        raw_results = click_more_and_collect(search_page, query, max_clicks=10, pause=2)
        print(f"  Raw results: {len(raw_results)}")

        for r in raw_results:
            try:
                item = extract_result_data(r, query)
            except Exception as e:
                print(f"  Error extracting result: {e}")
                continue

            if item["url"] and item["url"] not in seen_urls:
                all_data.append(item)
                seen_urls.add(item["url"])

        print(f"  Unique so far: {len(all_data)}")
        time.sleep(2)  # polite pause between queries

    search_page.close()
    print(f"\nTotal unique results across all queries: {len(all_data)}")

    # Visit each URL to get missing dates
    article_page = context.new_page()

    for i, item in enumerate(all_data):
        if item["date"]:
            continue
        try:
            print(f"[{i+1}/{len(all_data)}] Fetching date from: {item['url']}")
            article_page.goto(item["url"], timeout=10000, wait_until="domcontentloaded")
            time.sleep(1)
            item["date"] = extract_date_from_page(article_page)
        except Exception as e:
            print(f"  Could not fetch page: {e}")
            item["date"] = ""

    article_page.close()

    # --- Save JSON ---
    json_path = "Scrapduck_multiquery_MACBA.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"\nJSON saved -> {json_path}")

    # --- Save CSV ---
    csv_path = "Scrapduck_multiquery_MACBA.csv"
    fieldnames = ["title", "url", "date", "description", "query", "scraped_at"]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    print(f"CSV saved -> {csv_path}")
    print(f"Total rows: {len(all_data)}")
