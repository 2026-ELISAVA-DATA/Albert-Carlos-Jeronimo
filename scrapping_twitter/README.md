# Scraping de búsquedas en X (Twitter) usando Playwright y Chrome (Chromium)

## Descripción

En este ejercicio aprenderás a **extraer resultados de búsqueda de X.com (antes Twitter)** utilizando [Playwright](https://playwright.dev/python/).  
En vez de depender de la API oficial, nos aprovechamos de una sesión ya autenticada en Chrome/Chromium usando el sistema de "Chrome DevTools Protocol".  
Así podemos **automatizar navegación y extracción de datos** como si fuéramos un usuario real, accediendo a cualquier resultado de búsqueda con tus permisos/idioma/cookies existentes.

Playwright es una poderosa biblioteca multiplataforma para Python (y otros lenguajes) que permite controlar navegadores como Chrome, Firefox y Safari de forma automatizada, cargar páginas, hacer clicks, extraer datos y gestionar sesiones reales (con JavaScript completamente funcional).

---

## Requisitos

- Tener **Chrome o Chromium** instalado.
- Instalar la biblioteca de Playwright para Python:
    ```bash
    pip install playwright
    playwright install
    ```

---

## Pasos

### 1. **Abre Chrome/Chromium con depuración remota en terminal**

Esto permite que Playwright se conecte a tu navegador ya abierto (¡y con tu sesión iniciada!).

```bash
chrome --remote-debugging-port=9222 --user-data-dir="/ruta/tu_perfil_chrome"
```
- En Windows suele ser:  
  `chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\Users\TU_USUARIO\AppData\Local\Google\Chrome\User Data"`
- En Linux/Mac cambia `chrome` por `chromium` si usas Chromium.

en mac
```
open -na "Google Chrome" --args --user-data-dir="/Users/tuusuario/Library/Application Support/Google/Chrome" https://www.google.com
```


- Puedes averiguar la ruta de tu perfil en `chrome://version` dentro del navegador.

**Inicia sesión manualmente en X.com** en esa ventana.

---

### 2. **Código de scraping con Playwright**

El siguiente script automatiza una búsqueda en X y extrae los primeros 10 tweets visibles.

```python
from playwright.sync_api import sync_playwright
import time
import json

SEARCH_URL = "https://x.com/search?q=skate%20barcelona&f=live"

with sync_playwright() as p:
    # Conéctate al Chrome abierto con depuración remota (ya logueado)
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    
    # Abre una nueva pestaña/contexto para no molestar tus pestañas manuales
    context = browser.contexts[0] if browser.contexts else browser.new_context()
    page = context.new_page()
    page.goto(SEARCH_URL)

    time.sleep(5)  # Espera a que cargue la página y los tweets

    articles = page.query_selector_all("article[role='article']")
    print(f"Tweets encontrados: {len(articles)}")

    tweets = []
    for idx, article in enumerate(articles, 1):
        tweet_text = article.inner_text()
        print(f"{idx}: {tweet_text}\n{'-'*40}")
        tweets.append(tweet_text)
        if idx >= 10:
            break

    # Guardar resultados en JSON
    with open("tweets_skate_barcelona.json", "w", encoding="utf-8") as f:
        json.dump(tweets, f, ensure_ascii=False, indent=2)
    print("Tweets guardados en tweets_skate_barcelona.json")
```

---

## Notas

- Este método es efectivo para búsquedas públicas, hilos, perfiles, etc.
- Si quieres scrapear más resultados, puedes automatizar el scroll (`page.evaluate('window.scrollBy(0, 2000)')` y volver a capturar artículos).
- Puedes modificar el selector para extraer otros datos: usuario, fecha, enlaces, imágenes, etc.
- **No compartas tu perfil, cookies o sesión con nadie.** Mantén la privacidad y seguridad.

---

## Referencias

- [Sitio Oficial de Playwright Python](https://playwright.dev/python/)
- [Documentación "connect_over_cdp"](https://playwright.dev/python/docs/browsers#connecting-to-existing-browser-instance)
- [X (Twitter) Search](https://x.com/search)

---

### 🚀 ¡Listo! Así aprovechas tu navegador real y Playwright para tareas de scraping éticas, prácticas y directas 👍
