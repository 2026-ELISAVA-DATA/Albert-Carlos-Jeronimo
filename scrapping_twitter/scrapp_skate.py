from playwright.sync_api import sync_playwright
import time
import json

SEARCH_URL = "https://x.com/search?q=skate%20barcelona&f=live"

def scroll_and_collect(page, scroll_times=10, scroll_pause=2.0):
    all_articles = set()
    for i in range(scroll_times):
        articles = page.query_selector_all("article[role='article']")
        print(f"Scroll {i+1}: {len(articles)} tweets"),
        all_articles.update(articles)
        # Scroll down
        page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        time.sleep(scroll_pause)
    return list(all_articles)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.new_page()
    page.goto(SEARCH_URL)
    time.sleep(5)  # Espera inicial

    # Scroll y recoger todos los artículos/tweets visibles
    articles = scroll_and_collect(page, scroll_times=10, scroll_pause=2)

    print(f"Total de tweets extraídos: {len(articles)}")
    tweets = []
    seen_texts = set()
    for article in articles:
        tweet_text = article.inner_text()
        # Evitar duplicados (X repite en el scroll)
        if tweet_text and tweet_text not in seen_texts:
            tweets.append({"texto": tweet_text})
            seen_texts.add(tweet_text)

    # Guardar en JSON
    with open("tweets_skate_barcelona.json", "w", encoding="utf-8") as f:
        json.dump(tweets, f, ensure_ascii=False, indent=2)
    print("Tweets guardados en tweets_skate_barcelona.json")