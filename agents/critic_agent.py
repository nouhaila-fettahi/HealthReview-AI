
import os
import json
from pathlib import Path
from datetime import datetime, timezone

from langchain_groq import ChatGroq
from json_repair import repair_json


# =====================================================
# 1. CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data/processed/evidence_synthesis.json"
OUTPUT_FILE = BASE_DIR / "data/processed/quality_report.json"

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing!")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=api_key,
    temperature=0
)


# =====================================================
# 2. LOAD SYNTHESIS AND SOURCE ARTICLES
# =====================================================

def load_data():

    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    synthesis = data.get("synthesis", {})
    articles = data.get("source_articles", [])

    if not synthesis or not articles:
        raise ValueError("Synthesis or source articles are missing!")

    return synthesis, articles


# =====================================================
# 3. AUTOMATIC STRUCTURAL VALIDATION
# =====================================================

def validate_references(synthesis, articles):

    valid_ids = {
        article.get("article_id")
        for article in articles
    }

    sections = [
        "main_themes",
        "comparative_analysis",
        "research_gaps",
        "future_research_directions"
    ]

    issues = []

    for section in sections:
        for index, item in enumerate(synthesis.get(section, [])):

            references = item.get("supporting_articles", [])

            if not isinstance(references, list):
                issues.append({
                    "section": section,
                    "item_index": index,
                    "issue": "Invalid reference format",
                    "severity": "HIGH"
                })
                continue

            if not references:
                issues.append({
                    "section": section,
                    "item_index": index,
                    "issue": "No supporting article provided",
                    "severity": "MEDIUM"
                })

            for reference in references:
                if reference not in valid_ids:
                    issues.append({
                        "section": section,
                        "item_index": index,
                        "issue": f"Unknown article ID: {reference}",
                        "severity": "HIGH"
                    })

    return issues, valid_ids


# =====================================================
# 4. INTELLIGENT SCIENTIFIC REVIEW
# =====================================================

def review_synthesis(synthesis, articles):

    compact_articles = []

    for article in articles:

        compact_articles.append({
            "article_id": article.get("article_id"),
            "title": article.get("title"),
            "year": article.get("year"),
            "doi": article.get("doi"),
            "source_type": article.get("source_type"),
            "source_chunk_ids": article.get("source_chunk_ids", []),
            "supporting_evidence": article.get("supporting_evidence", []),
            "healthcare_standards": article.get("healthcare_standards", []),
            "etl_architecture": article.get("etl_architecture"),
            "mapping_techniques": article.get("mapping_techniques", []),
            "main_findings": article.get("main_findings", []),
            "evaluation_methods": article.get("evaluation_methods", []),
            "limitations": article.get("limitations", []),
            "future_directions": article.get("future_directions", [])
        })

    prompt = f"""
You are a strict scientific quality reviewer.

Review the following evidence synthesis using ONLY
the supplied extracted article information.

SOURCE ARTICLES:
{json.dumps(compact_articles, ensure_ascii=False)}

SYNTHESIS:
{json.dumps(synthesis, ensure_ascii=False)}

Evaluate:

1. Whether each main theme is supported by its cited articles.
2. Whether each comparative observation is supported.
3. Whether each research gap is justified by the available evidence.
4. Whether any statement generalizes beyond the evidence.
5. Whether article IDs are correctly associated with claims.

IMPORTANT METHODOLOGICAL RULES:

- The available information comes mainly from abstracts.
- Absence of information in an abstract does NOT prove
  that the full article does not discuss that subject.
- Do not invent contradictions or missing information.
- Distinguish unsupported claims from confirmed errors.
- Do not assume all articles implement ETL pipelines.
- Do not treat FHIR and OMOP CDM as interchangeable.
- Be especially careful with words such as
  "universal", "always", "all" and "proves".
- Do not introduce external scientific knowledge.

Return ONLY valid JSON with this structure:

{{
  "overall_assessment": "string",
  "quality_score": 0,
  "theme_reviews": [
    {{
      "theme": "string",
      "status": "SUPPORTED",
      "comment": "string"
    }}
  ],
  "comparison_reviews": [
    {{
      "dimension": "string",
      "status": "SUPPORTED",
      "comment": "string"
    }}
  ],
  "research_gap_reviews": [
    {{
      "gap": "string",
      "status": "SUPPORTED",
      "comment": "string"
    }}
  ],
  "generalization_warnings": [
    "string"
  ],
  "recommendations": [
    "string"
  ]
}}

Allowed statuses:
SUPPORTED, PARTIALLY_SUPPORTED, NOT_VERIFIABLE,
UNSUPPORTED.

The quality score must be an integer between 0 and 100.
Do not claim that the full articles were reviewed.
"""

    response = llm.invoke(prompt)

    content = response.content

    if isinstance(content, list):
        content = "".join(
            item.get("text", "") if isinstance(item, dict)
            else str(item)
            for item in content
        )

    content = str(content).strip()

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No valid JSON returned by Groq")

    result = repair_json(
        content[start:end + 1],
        return_objects=True
    )

    if not isinstance(result, dict):
        raise ValueError("QA response is not a JSON object")

    score = result.get("quality_score")

    if type(score) is not int or not 0 <= score <= 100:
        raise ValueError("Invalid quality score")

    required_fields = [
        "overall_assessment",
        "theme_reviews",
        "comparison_reviews",
        "research_gap_reviews",
        "generalization_warnings",
        "recommendations"
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(f"Missing QA field: {field}")

    return result


# =====================================================
# 5. SAVE QUALITY REPORT
# =====================================================

def save_report(report):

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print("\nQuality report saved:", OUTPUT_FILE)


# =====================================================
# 6. MAIN
# =====================================================

def main():

    print("\n===== CRITIC / QUALITY ASSURANCE AGENT =====")

    synthesis, articles = load_data()

    print("Source articles:", len(articles))

    print("\n1. Checking article references...")

    structural_issues, valid_ids = validate_references(
        synthesis, articles
    )

    print("Valid source IDs:", len(valid_ids))
    print("Structural issues:", len(structural_issues))

    print("\n2. Reviewing scientific evidence with Groq...")

    review = review_synthesis(synthesis, articles)

    report = {
        "project": "HealthReview AI",
        "agent": "Critic / Quality Assurance Agent",
        "model": "openai/gpt-oss-120b",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "articles_reviewed": len(articles),
        "structural_issues": structural_issues,
        "scientific_review": review
    }

    save_report(report)

    print("\n===== QUALITY REVIEW COMPLETED =====")
    print("Quality score:", review.get("quality_score"))
    print("Recommendations:", len(review.get("recommendations", [])))
    print("Generalization warnings:", len(review.get("generalization_warnings", [])))


if __name__ == "__main__":
    main()
