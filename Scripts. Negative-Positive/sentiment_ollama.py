# Sentiment Analysis con Ollama (GRATIS, local, Windows)
# INSTALACION (solo la primera vez):
# 1. Descarga Ollama: https://ollama.com/download/windows
# 2. Abre CMD y ejecuta: ollama pull llama3.2
# 3. Instala dependencias: pip install ollama
# 4. Pon tu CSV en la misma carpeta y ejecuta: python sentiment_ollama.py

import csv
import time
import sys

try:
    import ollama
except ImportError:
    print("ERROR: Falta el paquete 'ollama'. Ejecuta: pip install ollama")
    sys.exit(1)

# --- Configuracion ---
INPUT_CSV  = "tweets_macba_skate_V5.csv"
OUTPUT_CSV = "tweets_macba_skate_sentiment.csv"
MODEL      = "llama3.2"
TEXT_COL   = "description"
SAVE_EVERY = 50

def check_ollama_running():
    try:
        ollama.list()
        return True
    except Exception:
        return False

def get_sentiment(text):
    if not text or len(text.strip()) < 3:
        return ""
    prompt = (
        "Is the sentiment of this tweet positive or negative?\n"
        "Reply with ONLY '1' if positive (or neutral), or '0' if negative. Nothing else.\n"
        "Tweet: " + text
    )
    try:
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
        return ""
    except Exception as e:
        print("  Error: " + str(e))
        return ""

def save_progress(rows, fieldnames, path):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

if __name__ == "__main__":
    print("Comprobando Ollama...")
    if not check_ollama_running():
        print("ERROR: Ollama no esta activo. Abre la app Ollama e intentalo de nuevo.")
        sys.exit(1)
    print("Ollama activo. Modelo: " + MODEL + "\n")

    try:
        with open(INPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = list(reader.fieldnames) + ["sentiment"]
    except FileNotFoundError:
        print("ERROR: No se encuentra '" + INPUT_CSV + "'. Pon el CSV en la misma carpeta.")
        sys.exit(1)

    total = len(rows)
    print("Total tweets: " + str(total))
    print("  1 = positivo / neutro")
    print("  0 = negativo\n")
    results = []
    start = time.time()

    for i, row in enumerate(rows):
        text = row.get(TEXT_COL, "")
        preview = text[:60].replace("\n", " ")
        score = get_sentiment(text)
        row["sentiment"] = score
        results.append(row)
        label = "(positivo)" if score == 1 else "(negativo)" if score == 0 else "(sin datos)"
        print("[" + str(i+1) + "/" + str(total) + "] " + label + " " + preview + "...")

        if (i + 1) % SAVE_EVERY == 0:
            save_progress(results, fieldnames, OUTPUT_CSV)
            elapsed = time.time() - start
            rate = (i + 1) / elapsed
            remaining = (total - i - 1) / rate if rate > 0 else 0
            print("  >> Guardado. Restante: ~" + str(round(remaining/60, 1)) + " min")

        time.sleep(0.1)

    save_progress(results, fieldnames, OUTPUT_CSV)
    elapsed = time.time() - start
    print("\nHecho! " + str(total) + " tweets en " + str(round(elapsed/60, 1)) + " min.")
    print("Archivo guardado: " + OUTPUT_CSV)