from playwright.sync_api import sync_playwright
import time
import json
import csv
from datetime import datetime
import re

SEARCH_QUERIES = [
    "skate MACBA Barcelona",
    "skateboarding MACBA plaza",
    "MACBA skate spot Barcelona",
    "skate Barcelona MACBA history",
    "skateboarding Barcelona museum contemporary art",
    "MACBA skaters documentary",
    "skate culture MACBA",
    "Barcelona skate scene MACBA",
    "MACBA skateboarding footage",
    "skate spots Barcelona MACBA",
]

def extract_date_from_page(page):
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

def extract_result_data(r, query=""):
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
    }

def scrape_query(page, query, max_clicks=10, pause=2.0):
    url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}&t=chromentp&ia=web"
    print(f"\n{'='*50}")
    print(f"Searching: {query}")
    print(f"{'='*50}")

    page.goto(url)
    time.sleep(4)

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
            except Exception as e:
                print(f"  Could not click More Results: {e}")
                break
            time.sleep(pause)
        else:
            print("  No more results.")
            break

    return all_results

# --- Main ---
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0] if browser.contexts else browser.new_context()

    search_page = context.new_page()

    all_data = []
    seen_urls = set()

    for query in SEARCH_QUERIES:
        raw_results = scrape_query(search_page, query, max_clicks=10, pause=2)

        new_count = 0
        for r in raw_results:
            try:
                item = extract_result_data(r, query=query)
            except Exception as e:
                print(f"  Error extracting: {e}")
                continue

            if item["url"] and item["url"] not in seen_urls:
                all_data.append(item)
                seen_urls.add(item["url"])
                new_count += 1

        print(f"  -> {new_count} new unique results (total so far: {len(all_data)})")
        time.sleep(3)

    print(f"\nTotal unique results across all queries: {len(all_data)}")

    # Visit each page to get publication date
    article_page = context.new_page()

    for i, item in enumerate(all_data):
        if item["date"]:
            continue
        try:
            print(f"[{i+1}/{len(all_data)}] Getting date: {item['url']}")
            article_page.goto(item["url"], timeout=10000, wait_until="domcontentloaded")
            time.sleep(1)
            item["date"] = extract_date_from_page(article_page)
        except Exception as e:
            print(f"  Failed: {e}")
            item["date"] = ""

    article_page.close()

    # --- Save JSON ---
    json_path = "Scrapduck_chrome_multiplequeryes.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    print(f"\nJSON saved -> {json_path}")

    # --- Save CSV ---
    csv_path = "Scrapduck_chrome_multiplequeryes.csv"
    fieldnames = ["title", "url", "date", "description", "query"]

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_data)
    print(f"CSV saved -> {csv_path}")
    print(f"Final dataset: {len(all_data)} unique links")
