from playwright.sync_api import sync_playwright
import time
import json

SEARCH_URL = "https://duckduckgo.com/?q=skate+macba&t=chromentp&ia=web"

def click_more_and_collect(page, max_clicks=50, pause=2.0):
    all_results = set()
    for i in range(max_clicks):
        results = page.query_selector_all("article[data-testid='result']")
        print(f"Click {i+1}: {len(results)} resultados")
        all_results.update(results)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        more_btn = page.query_selector("#more-results")  # Nuevo selector del botón More Results
        if more_btn and more_btn.is_enabled():
            try:
                more_btn.click()
                print("Click en 'More Results'")
            except Exception as e:
                print(f"No se pudo hacer clic en More Results: {e}")
                break
            time.sleep(pause)
        else:
            print("No hay más resultados o el botón no está disponible.")
            break
    return list(all_results)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.new_page()
    page.goto(SEARCH_URL)
    time.sleep(5)

    results = click_more_and_collect(page, max_clicks=10, pause=2)

    print(f"Total de resultados extraídos: {len(results)}")
    data = []
    seen_links = set()

    for r in results:
        # Título y URL
        title_link = r.query_selector("a[data-testid='result-title-a']")
        url = title_link.get_attribute("href") if title_link else None
        title = title_link.inner_text() if title_link else ""
        # Snippet/descripción
        snippet_el = r.query_selector("div[data-result='snippet']")
        snippet = snippet_el.inner_text() if snippet_el else ""
        # Evitar duplicados por URL
        if url and url not in seen_links:
            data.append({"titulo": title, "url": url, "snippet": snippet})
            seen_links.add(url)

    with open("resultados_skate_Macba_skate.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("Resultados guardados en resultados_skate_barcelona.json")
