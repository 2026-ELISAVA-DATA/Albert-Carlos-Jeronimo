# PASO 1

# Metodología de Scraping — MACBA Skate

## Contexto del proyecto

La plaza del MACBA ha trascendido su condición arquitectónica para consolidarse como un enclave fundamental en la cultura global del skateboarding. Ante la propuesta de reforma del espacio y la emergencia del movimiento *Save the MACBA*, se activa un debate que excede lo urbano y se sitúa en el ámbito del patrimonio cultural contemporáneo y la apropiación del espacio público.

Este proyecto construye una base de datos que recoge la conversación digital generada en torno al conflicto, extrayendo tweets y artículos web mediante técnicas de web scraping. Estos contenidos son posteriormente procesados para identificar su polaridad y visualizados sobre una infografía tridimensional del museo.

---

## Stack técnico

| Herramienta   | Uso                              |
| ------------- | -------------------------------- |
| Python 3      | Lenguaje principal               |
| Playwright    | Automatización del navegador     |
| Google Chrome | Navegador controlado remotamente |
| CSV / JSON    | Formatos de salida               |

### Instalación de dependencias
```bash
pip3 install playwright
playwright install
```

---

## Parte 1 — Scraping de Twitter / X

### Objetivo

Recoger tweets públicos relacionados con MACBA y el skateboarding, incluyendo el movimiento *saveMACBA*, para construir un dataset de la conversación digital en torno al conflicto.

### Setup del navegador

El scraper se conecta a una instancia real de Chrome vía CDP *(Chrome DevTools Protocol)*, lo que permite usar una sesión con login activo y evitar bloqueos.

**1. Cerrar Chrome completamente:**
```bash
pkill -a -i "Google Chrome"
```

**2. Abrir Chrome con puerto de debugging:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --no-first-run \
  --no-default-browser-check \
  --user-data-dir="/tmp/chrome_scraping" \
  "about:blank"
```

**3. Verificar que el puerto está activo:**
```bash
curl http://localhost:9222/json
```

Respuesta esperada: JSON con las tabs abiertas, incluyendo `x.com`.

**4. Login manual:**
- Navegar a `x.com` en la ventana de Chrome
- Iniciar sesión con la cuenta
- Confirmar que el feed carga correctamente

---

### Queries utilizadas

Se definieron 17 queries divididas en tres categorías temáticas, cada una buscada en tres tabs de Twitter *(Top, Latest, Media)* para maximizar la cobertura:

**Queries en inglés:**
- `MACBA skate`
- `MACBA skateboarding`
- `MACBA barcelona`
- `skate MACBA`
- `MACBA skaters`
- `MACBA skating`
- `MACBA spot`
- `skate barcelona MACBA`
- `MACBA plaza skate`
- `barcelona skate plaza`
- `macba sk8`
- `macba skatepark`
- `MACBA skate cultura`
- `MACBA skate historia`

**Queries en español:**
- `museo MACBA skate`
- `patinaje MACBA`

**Movimiento:**
- `saveMACBA`

> Cada query se ejecuta en los tabs **Top**, **Latest** y **Media**, resultando en hasta 51 búsquedas distintas. Los duplicados se eliminan por URL.

---

### Lógica del scraper
```
Para cada query:
  Para cada tab (top, latest, media):
    1. Cargar la URL de búsqueda
    2. Esperar a que aparezcan tweets (máx. 15s)
    3. Si no aparecen → reintentar hasta 3 veces
    4. Si aparece error de Twitter → recargar página
    5. Hacer scroll progresivo recogiendo tweets
    6. Si 3 scrolls seguidos sin tweets nuevos → pasar al siguiente
    7. Pausa de 10s entre búsquedas
```

### Datos extraídos por tweet

| Campo | Descripción |
|-------|-------------|
| `title` | Nombre de usuario |
| `url` | Link directo al tweet |
| `date` | Fecha de publicación (ISO 8601) |
| `description` | Texto del tweet |
| `query` | Query y tab que lo encontró |

### Script
```
scrapp_twitter_V5.py
```

### Output
```
tweets_macba_skate_V5.csv
tweets_macba_skate_V5.json
```
[Twitter 2](https://drive.google.com/file/d/14w3n5eC4j8kZWaJb7oHpYZdnadYXRVdW/view?usp=drive_link)
---

## Parte 2 — Scraping de la web

### Objetivo

Recoger artículos, noticias y posts de blogs relacionados con MACBA y el skateboarding para complementar el dataset con contenido editorial y periodístico.

### Setup del navegador

El scraper web usa DuckDuckGo como motor de búsqueda para evitar bloqueos y no requerir login. Se conecta al mismo Chrome con debugging activo.

> Mismo proceso de apertura de Chrome que en la Parte 1.

---

### Queries utilizadas

Se definieron 17 queries orientadas a maximizar la cobertura de contenido editorial:

**Queries en inglés:**
- `MACBA skate`
- `MACBA skateboarding`
- `MACBA barcelona`
- `skate MACBA`
- `MACBA skaters`
- `MACBA skating`
- `MACBA spot`
- `skate barcelona MACBA`
- `MACBA plaza skate`
- `barcelona skate plaza`
- `macba sk8`
- `macba skatepark`
- `MACBA skate cultura`
- `MACBA skate historia`

**Queries en español:**
- `museo MACBA skate`
- `patinaje MACBA`

**Movimiento:**
- `saveMACBA`

---

### Lógica del scraper
```
Para cada query:
  1. Cargar búsqueda en DuckDuckGo
  2. Hacer scroll y clickar "More Results" hasta 40 veces
  3. Extraer título, URL y descripción de cada resultado
  4. Visitar cada URL individualmente
  5. Buscar fecha de publicación en meta tags, JSON-LD y elementos HTML
  6. Deduplicar por URL
  7. Pausa de 2s entre queries
```

[Web 1](https://drive.google.com/file/d/1JQ_FtCTts9Q0GnkjlnmNIPmq5ioBq-5J/view?usp=drive_link)
### Extracción de fechas

Para cada artículo el scraper busca la fecha de publicación en este orden de prioridad:

1. **Meta tags** — `article:published_time`, `pubdate`, `datePublished`
2. **Elementos HTML** — `<time datetime="">`, clases con `date`, `published`, `timestamp`
3. **JSON-LD** — bloques `application/ld+json` con campos `datePublished`, `dateCreated`

### Datos extraídos por artículo

| Campo | Descripción |
|-------|-------------|
| `title` | Título del artículo o página |
| `url` | URL del artículo |
| `date` | Fecha de publicación |
| `description` | Fragmento descriptivo del resultado |
| `query` | Query que encontró el artículo |
| `scraped_at` | Fecha y hora del scraping |

### Script
```
Scrapduck_multiquery_MACBA.py
```

### Output
```
Scrapduck_multiquery_MACBA_masclicks.csv
Scrapduck_multiquery_MACBA_masclicks.json
```

[Web 2](https://drive.google.com/file/d/1pmt2N6wj9afiGMAUVbjeTghscHwZ2crX/view?usp=drive_link)

---

## Resumen del dataset

| Dataset | Script | Fuente | Formato |
|---------|--------|--------|---------|
| `tweets_macba_skate_V5.csv` | `scrapp_twitter_V5.py` | Twitter / X | CSV + JSON |
| `Scrapduck_multiquery_MACBA_masclicks.csv` | `Scrapduck_multiquery_MACBA.py` | Web (DuckDuckGo) | CSV + JSON |

---

## Columnas del CSV

| Columna | Twitter | Web |
|---------|---------|-----|
| `title` | Nombre de usuario | Título del artículo |
| `url` | Link directo al tweet | URL del artículo |
| `date` | Fecha de publicación (ISO 8601) | Fecha de publicación |
| `description` | Texto del tweet | Fragmento descriptivo |
| `query` | Query + tab que lo encontró | Query que lo encontró |
| `scraped_at` | — | Fecha y hora del scraping |

---

## Troubleshooting

| Problema | Solución |
|----------|----------|
| `connection refused` | Chrome no está corriendo con el puerto 9222 |
| `No tweets found` | Query sin resultados, se salta automáticamente |
| `Something went wrong` | Twitter rate limiting, el script recarga automáticamente |
| `Login wall detected` | La sesión expiró, vuelve a hacer login en Chrome |
| Tweets stuck en 8 | Usar `context.pages[0]` en vez de `new_context()` |
| Sin fecha en web | El artículo no expone fecha en HTML, se deja vacío |

# Paso 2

# Valor sentimental - OLLAMA

Para el análisis de sentimiento se utilizó **Ollama**, una herramienta que permite ejecutar modelos de inteligencia artificial de forma local en el ordenador, sin necesidad de conexión a internet ni de pagar por ningún servicio. El modelo utilizado fue **LLaMA 3.2**, al que se le enviaba el texto de cada tweet o descripción de artículo web y se le pedía que clasificara su sentimiento como positivo (1) o negativo (0). Este proceso se automatizó mediante un script de Python que leía los datos de un CSV, procesaba cada entrada una a una y generaba un nuevo CSV con una columna adicional llamada "sentiment" con el valor correspondiente. El mismo método se aplicó tanto a los tweets sobre el MACBA como a los artículos web, permitiendo analizar de forma sistemática el tono general del discurso online alrededor del espacio.

# Análisis de Sentimiento con Ollama

## Requisitos previos
- Windows 10 o 11
- Conexión a internet (solo para la instalación)

---

## Paso 1 — Instalar Python
1. Ve a **python.org/downloads** y descarga la última versión
2. Durante la instalación, marca obligatoriamente la casilla **"Add Python to PATH"**
3. Verifica la instalación abriendo CMD y ejecutando:
```
   python --version
```

---

## Paso 2 — Instalar Ollama
1. Ve a **ollama.com/download/windows** y descarga el instalador
2. Instálalo (quedará como icono en la barra de tareas)

---

## Paso 3 — Descargar el modelo LLaMA 3.2
1. Abre CMD y ejecuta:
```
   ollama pull llama3.2
```
2. Espera a que se descargue (~2GB)

---

## Paso 4 — Instalar la librería de Python
1. En CMD ejecuta:
```
   python -m pip install ollama
```

---

## Paso 5 — Preparar los archivos
1. Crea una carpeta en tu ordenador
2. Pon dentro el script `.py` y el CSV con los datos

---

## Paso 6 — Ejecutar el script
1. En CMD, navega a la carpeta donde están los archivos:
```
   cd C:\ruta\a\tu\carpeta
```
2. Ejecuta el script:
```
   python sentiment_ollama_web.py
```
3. El script procesará cada fila del CSV y mostrará en pantalla si cada entrada es positiva o negativa

---

## Resultado
Se genera un nuevo archivo CSV con una columna adicional llamada **`sentiment`**:
- **1** = positivo o neutro(No teniamos tiempo de crear otro filtro en la web)
- **0** = negativo

[Sentimientos](https://drive.google.com/file/d/1xj6aInrkGBmftCGRKX0AZln8OhiLNaip/view?usp=drive_link)
## Cómo funciona el código

El núcleo del script es la función `get_sentiment()`, que es la que se comunica con Ollama y decide si un texto es positivo o negativo:
```python
def get_sentiment(text):
    if not text or len(text.strip()) < 3:
        return ""
    prompt = (
        "Is the sentiment of this web article description positive or negative?\n"
        "Reply with ONLY '1' if positive (or neutral), or '0' if negative. Nothing else.\n"
        "Text: " + text
    )
    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0, "num_predict": 3},
    )
    score = response["message"]["content"].strip()
    if "1" in score:
        return 1
    if "0" in score:
        return 0
```

**El prompt** es la instrucción que se le envía al modelo con cada texto. Le pregunta si el sentimiento es positivo o negativo y le obliga a responder únicamente con `1` o `0`, sin ninguna explicación adicional. Este texto se puede modificar para darle criterios más específicos, por ejemplo orientados al skateboarding en espacios públicos.

**`temperature: 0`** hace que el modelo sea determinista, es decir, que siempre tienda a dar la misma respuesta ante el mismo texto, sin "improvisar".

**`num_predict: 3`** limita la longitud de la respuesta a muy pocas palabras, forzando al modelo a devolver solo el número.

El script recorre el CSV fila a fila, envía el texto de la columna `description` a Ollama, recibe el valor `1` o `0` y lo escribe en una nueva columna llamada `sentiment` en el archivo de salida.



**FUTUROS PASOS**

1- Actualizar la web si salen nuevos articulos o tweets de el macba (scrap automatico).
2- El analisis de sentimiento en ollama se podria mejorar dandole un promt mas extenso en el que se relacionan palabras especificas con la categorizacion positiva o negativa.
3- Mejorar la UI de la web haciendo journey studies con gente que nunca la haya usado y que nos den feedback de lo que no esta claro.
4- Hacer un scrap de instagram para sacar aun mas datos, y añadir un filtro mas a la web.
