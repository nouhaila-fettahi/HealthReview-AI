import json
import os
from pathlib import Path
from datetime import datetime, timezone

from langchain_groq import ChatGroq


ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT / "data/processed/final_screening_results.json"
OUTPUT_FILE = ROOT / "data/processed/methodological_quality_assessment.json"

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing!")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=api_key,
    temperature=0
)


CRITERIA = {
    "C1_objectives": "Clarity of research objectives",
    "C2_data_provenance": "Description of data sources and provenance",
    "C3_representativeness": "Representativeness of the data",
    "C4_mapping_methodology": "Clarity of the mapping or transformation methodology",
    "C5_validation": "Validation of the proposed method or system",
    "C6_evaluation_metrics": "Use of evaluation metrics or measurable results",
    "C7_reproducibility": "Availability of tools, code, and implementation details",
    "C8_limitations": "Discussion of methodological limitations"
}

ALLOWED_VALUES = {"YES", "PARTIAL", "NO", "UNCLEAR"}


def load_included_articles():
    """Load only articles with a final INCLUDE decision."""

    with INPUT_FILE.open(encoding="utf-8") as file:
        data = json.load(file)

    articles = (
        data.get("articles", [])
        if isinstance(data, dict)
        else data
    )

    return [
        article for article in articles
        if article.get("final_decision") == "INCLUDE"
    ]


def evaluate_article(article):
    """Evaluate methodological quality using available article information."""

    article_text = json.dumps(
        article,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are a scientific methodological appraisal assistant.

Evaluate the methodological quality of this healthcare
interoperability research article.

Use ONLY the information provided below.

ARTICLE:
{article_text}

ASSESSMENT CRITERIA:
{json.dumps(CRITERIA, indent=2)}

For every criterion, assign exactly one value:
YES, PARTIAL, NO, or UNCLEAR.


Rules:
- Use only information explicitly available in the article data.
- Do not invent information or assumptions.
- YES: the criterion is clearly supported by evidence.
- PARTIAL: the criterion is only partially supported.
- NO: explicit evidence demonstrates that the criterion
  is not satisfied or that a methodological weakness exists.
- UNCLEAR: information is missing or insufficient to
  make a reliable judgment.
- Absence of information in an abstract MUST NOT
  automatically result in NO.
- In particular, if limitations, code availability,
  validation, or evaluation metrics are not mentioned
  in the abstract, use UNCLEAR unless explicit evidence
  supports another rating.
- Distinguish methodological weaknesses from reporting gaps.
- Provide a short evidence-based justification.
- This is a preliminary AI-assisted appraisal, not a
  validated formal risk-of-bias assessment.
- Human review is mandatory.


Return ONLY valid JSON with this structure:

{{
  "article_title": "article title",
  "doi": "article DOI",
  "study_type": "identified study type or UNCLEAR",
  "criteria": {{
    "C1_objectives": {{
      "rating": "YES/PARTIAL/NO/UNCLEAR",
      "justification": "evidence-based explanation"
    }}
  }},
  "overall_comment": "brief methodological appraisal",
  "human_review_required": true
}}

Include all eight criteria in the JSON.
"""

    response = llm.invoke(prompt)

    content = response.content.strip()

    if content.startswith("```"):
        content = content.split("```", 2)[1]
        if content.startswith("json"):
            content = content[4:]

    result = json.loads(content.strip())

    # Check that all criteria are present and ratings are allowed.
    criteria = result.get("criteria", {})

    for criterion in CRITERIA:
        if criterion not in criteria:
            raise ValueError(f"Missing criterion: {criterion}")

        rating = criteria[criterion].get("rating")

        if rating not in ALLOWED_VALUES:
            raise ValueError(
                f"Invalid rating for {criterion}: {rating}"
            )

    result["human_review_required"] = True

    return result


def main():

    print("===== METHODOLOGICAL QUALITY AGENT =====")

    articles = load_included_articles()

    print("Included articles:", len(articles))

    assessments = []
    errors = []

    for index, article in enumerate(articles, start=1):

        title = article.get("title", "Unknown title")

        print(f"\nEvaluating article {index}/{len(articles)}")
        print("Title:", title)

        try:
            assessment = evaluate_article(article)
            assessments.append(assessment)
            print("Assessment completed.")

        except Exception as error:
            errors.append({
                "title": title,
                "error": str(error)
            })
            print("Assessment failed:", error)

    output = {
        "assessment_date": datetime.now(
            timezone.utc
        ).isoformat(),
        "assessment_type": "AI-assisted methodological quality appraisal",
        "criteria": CRITERIA,
        "total_articles": len(articles),
        "successfully_assessed": len(assessments),
        "failed_assessments": len(errors),
        "human_review_required": True,
        "assessments": assessments,
        "errors": errors,
        "limitations": (
            "Preliminary AI-assisted appraisal based on available "
            "article metadata and abstracts. Full-text review and "
            "human verification are required."
        )
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n===== ASSESSMENT SUMMARY =====")
    print("Articles:", len(articles))
    print("Successfully assessed:", len(assessments))
    print("Failed:", len(errors))
    print("Human review required: YES")
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
 