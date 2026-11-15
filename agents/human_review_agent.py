
import json
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT / "data/processed/methodological_quality_assessment.json"
OUTPUT_FILE = ROOT / "data/processed/human_review_results.json"

ALLOWED_VALUES = {"YES", "PARTIAL", "NO", "UNCLEAR"}


def load_assessments():
    with INPUT_FILE.open(encoding="utf-8") as file:
        return json.load(file)


def review_article(article, index, total):
    print("\n" + "=" * 65)
    print(f"ARTICLE {index}/{total}")
    print("=" * 65)

    print("Title:", article.get("article_title"))
    print("DOI:", article.get("doi"))
    print("Study type:", article.get("study_type", "UNCLEAR"))

    reviewed_criteria = {}

    for criterion, evaluation in article.get("criteria", {}).items():

        ai_rating = evaluation.get("rating", "UNCLEAR")
        ai_justification = evaluation.get("justification", "")

        print("\n" + "-" * 65)
        print(f"CRITERION: {criterion}")
        print("AI rating:", ai_rating)
        print("AI justification:", ai_justification)

        while True:
            decision = input(
                "\nYour decision [Enter=Keep / YES / PARTIAL / NO / UNCLEAR / SKIP]: "
            ).strip().upper()

            if decision == "":
                decision = ai_rating

            if decision == "SKIP":
                reviewed_criteria[criterion] = {
                    "ai_rating": ai_rating,
                    "rating": ai_rating,
                    "ai_justification": ai_justification,
                    "human_justification": None,
                    "review_status": "NOT_REVIEWED"
                }
                break

            if decision not in ALLOWED_VALUES:
                print("Invalid choice. Try again.")
                continue

            print("\nSelected rating:", decision)

            justification = input(
                "Human justification (Enter=keep AI justification): "
            ).strip()

            if justification:
                print("\nPlease verify your justification:")
                print(justification)

                confirmation = input(
                    "Confirm this justification? [Y/N]: "
                ).strip().upper()

                if confirmation != "Y":
                    print("Please enter the justification again.")
                    continue

            reviewed_criteria[criterion] = {
                "ai_rating": ai_rating,
                "rating": decision,
                "ai_justification": ai_justification,
                "human_justification": justification or None,
                "review_status": (
                    "CONFIRMED"
                    if decision == ai_rating
                    else "MODIFIED"
                )
            }
            break

    return {
        "article_title": article.get("article_title"),
        "doi": article.get("doi"),
        "criteria": reviewed_criteria,
        "review_completed_at": datetime.now(timezone.utc).isoformat()
    }


def main():
    print("===== HEALTHREVIEW AI - HUMAN REVIEW =====")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(INPUT_FILE)

    data = load_assessments()
    assessments = data.get("assessments", [])

    output = {
        "review_type": "Human validation of AI-assisted assessment",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(assessments),
        "human_review_required": True,
        "reviewed_articles": []
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print("Articles to review:", len(assessments))

    for index, article in enumerate(assessments, start=1):
        reviewed = review_article(article, index, len(assessments))
        output["reviewed_articles"].append(reviewed)

        OUTPUT_FILE.write_text(
            json.dumps(output, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        print("\nArticle review saved.")

    completed = all(
        all(
            item.get("review_status") != "NOT_REVIEWED"
            for item in article["criteria"].values()
        )
        for article in output["reviewed_articles"]
    )

    output["human_review_completed"] = completed

    OUTPUT_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n===== HUMAN REVIEW SUMMARY =====")
    print("Articles reviewed:", len(output["reviewed_articles"]))
    print("Review completed:", completed)
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
