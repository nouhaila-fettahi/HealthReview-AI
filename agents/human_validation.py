import json
from pathlib import Path
from datetime import datetime, timezone

INPUT_FILE = Path("data/processed/screening_results.json")
OUTPUT_FILE = Path("data/processed/human_validated_results.json")

VALID_DECISIONS = {"INCLUDE", "EXCLUDE", "UNCERTAIN"}


def load_articles():
    # Resume previous human reviews if they exist.
    source = OUTPUT_FILE if OUTPUT_FILE.exists() else INPUT_FILE

    with source.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Restore abstracts from the enriched corpus without overwriting
    # existing human decisions.
    enriched_file = Path("data/processed/enriched_articles.json")

    if enriched_file.exists():
        with enriched_file.open("r", encoding="utf-8") as f:
            enriched_data = json.load(f)

        index = {}

        for item in enriched_data.get("articles", []):
            keys = [
                ("doi", str(item.get("doi", "")).strip().lower()),
                ("pmid", str(item.get("pmid", "")).strip()),
                ("title", " ".join(item.get("title", "").lower().split()))
            ]

            for key_type, value in keys:
                if value:
                    index[(key_type, value)] = item

        restored = 0

        for article in data.get("articles", []):
            keys = [
                ("doi", str(article.get("doi", "")).strip().lower()),
                ("pmid", str(article.get("pmid", "")).strip()),
                ("title", " ".join(article.get("title", "").lower().split()))
            ]

            match = next(
                (index[key] for key_type, value in keys
                 if value and (key := (key_type, value)) in index),
                None
            )

            if match and not article.get("abstract") and match.get("abstract"):
                article["abstract"] = match["abstract"]
                article["abstract_source"] = match.get("abstract_source")
                restored += 1

        print(f"Abstracts restored: {restored}")

    return data


def save_results(data):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write safely to avoid damaging an existing result.
    temporary = OUTPUT_FILE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    temporary.replace(OUTPUT_FILE)


def validate_articles():
    data = load_articles()
    articles = data["articles"]

    print("\n===== HEALTHREVIEW AI =====")
    print("HUMAN VALIDATION MODULE")
    print(f"Total articles: {len(articles)}")
    print("Commands: INCLUDE, EXCLUDE, UNCERTAIN")
    print("Type Q to save and quit.\n")

    for index, article in enumerate(articles, start=1):
        if article.get("human_validation") == "VALIDATED":
            continue

        print("\n" + "=" * 65)
        print(f"ARTICLE {index}/{len(articles)}")
        print("Title:", article.get("title", "Unknown"))
        print("AI decision:", article.get("decision", "UNKNOWN"))
        print("AI reason:", article.get("reason", "Not available"))
        print("Abstract:", article.get("abstract", "Not available"))

        while True:
            choice = input(
                "\nYour decision (INCLUDE/EXCLUDE/UNCERTAIN/Q): "
            ).strip().upper()

            if choice == "Q":
                save_results(data)
                print("\nProgress saved. You can resume later.")
                return

            if choice in VALID_DECISIONS:
                break

            print("Invalid choice. Please try again.")

        note = input("Reason or comment (optional): ").strip()

        # Preserve the original AI screening decision.
        article["human_decision"] = choice
        article["human_validation"] = "VALIDATED"
        article["human_reason"] = note
        article["validated_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        save_results(data)
        print("Human decision saved successfully.")

    print("\n===== VALIDATION COMPLETED =====")
    print("Results saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    validate_articles()
