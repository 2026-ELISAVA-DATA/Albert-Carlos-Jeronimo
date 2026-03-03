import anthropic
import csv
import time

client = anthropic.Anthropic()

def get_sentiment(text):
    if not text or len(text.strip()) < 3:
        return ""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=10,
            messages=[
                {
                    "role": "user",
                    "content": f"""Rate the sentiment of this tweet from 1 to 10.
1 = very negative, 5 = neutral, 10 = very positive.
Reply with ONLY a single number, nothing else.

Tweet: {text}"""
                }
            ]
        )
        score = message.content[0].text.strip()
        return int(score) if score.isdigit() else ""
    except Exception as e:
        print(f"  Sentiment error: {e}")
        return ""

# --- Main ---
input_csv = "tweets_macba_skate_V5.csv"
output_csv = "tweets_macba_skate_sentiment.csv"

with open(input_csv, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    fieldnames = reader.fieldnames + ["sentiment"]

print(f"Total tweets to process: {len(rows)}")

results = []
for i, row in enumerate(rows):
    text = row.get("description", "")
    print(f"[{i+1}/{len(rows)}] Scoring: {text[:50]}...")
    
    score = get_sentiment(text)
    row["sentiment"] = score
    results.append(row)

    # Save progress every 50 rows in case it crashes
    if (i + 1) % 50 == 0:
        print(f"  Saving progress at {i+1} rows...")
        with open(output_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

    time.sleep(0.5)  # avoid rate limiting

# Final save
with open(output_csv, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"Done! Saved to {output_csv}")
