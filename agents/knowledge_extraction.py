import os
import json
import re
from pathlib import Path
from datetime import datetime, timezone

from langchain_groq import ChatGroq


# =====================================================
# 1. CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SCREENING_FILE = BASE_DIR / "data/processed/screening_results.json"
ENRICHED_FILE = BASE_DIR / "data/processed/enriched_articles.json"
OUTPUT_FILE = BASE_DIR / "data/processed/extracted_knowledge.json"

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing!")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=api_key,
    temperature=0
)


# =====================================================
# 2. LOAD AND MATCH ARTICLES
# =====================================================

def load_articles():

    with open(SCREENING_FILE, encoding="utf-8") as f:
        screening = json.load(f)["articles"]

    with open(ENRICHED_FILE, encoding="utf-8") as f:
        enriched = json.load(f)["articles"]

    included = [
        article for article in screening
        if article.get("decision") == "INCLUDE"
    ]

    matched = []

    for article in included:

        enriched_article = next(
            (
                item for item in enriched
                if article.get("doi")
                and item.get("doi")
                and article["doi"].strip().lower()
                == item["doi"].strip().lower()
            ),
            None
        )

        if not enriched_article and article.get("pmid"):
            enriched_article = next(
                (
                    item for item in enriched
                    if str(item.get("pmid", "")).strip()
                    == str(article["pmid"]).strip()
                ),
                None
            )

        if enriched_article:
            matched.append((article, enriched_article))
        else:
            print("WARNING: No enriched match:", article.get("title"))

    return matched


# =====================================================
# 3. KNOWLEDGE EXTRACTION
# =====================================================

def extract_knowledge(screening, article):

    abstract = article.get("abstract") or ""

    if not abstract.strip():
        return {
            "extraction_status": "NO_ABSTRACT",
            "research_objective": None,
            "healthcare_standards": [],
            "etl_architecture": None,
            "mapping_techniques": [],
            "data_sources": [],
            "datasets": [],
            "evaluation_methods": [],
            "main_findings": [],
            "limitations": [],
            "future_directions": [],
            "supporting_evidence": []
        }

    prompt = f"""
You are a scientific literature analysis assistant
specialized in healthcare interoperability.

Analyze ONLY the information explicitly supported
by the following article abstract.

ARTICLE TITLE:
{article.get("title", "")}

ARTICLE YEAR:
{article.get("year", "")}

JOURNAL:
{article.get("journal", "")}

ABSTRACT:
{abstract}

SCREENING JUSTIFICATION:
{screening.get("reason", "")}

TASK:
Extract structured scientific knowledge relevant to:

- HL7 and FHIR
- OMOP Common Data Model
- Healthcare interoperability
- ETL pipelines
- Clinical data integration
- Data mapping and transformation

Return ONLY one valid JSON object with these exact keys:

{{
  "research_objective": "string or null",
  "healthcare_standards": ["string"],
  "etl_architecture": "string or null",
  "mapping_techniques": ["string"],
  "data_sources": ["string"],
  "datasets": ["string"],
  "evaluation_methods": ["string"],
  "main_findings": ["string"],
  "limitations": ["string"],
  "future_directions": ["string"],
  "supporting_evidence": [
    {{
      "claim": "extracted information",
      "quote": "exact quotation from the abstract"
    }}
  ]
}}

STRICT RULES:

1. Never invent information.
2. Use null or an empty list when information is absent.
3. Do not assume a dataset or evaluation method exists.
4. Supporting quotations must be copied exactly
   from the abstract.
5. Distinguish FHIR, HL7, OMOP CDM and other standards.
6. Focus on healthcare interoperability and ETL.
7. Do not use external knowledge to complete missing details.
8. Return valid JSON only, without Markdown fences.
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

    # Remove optional Markdown JSON fences
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    # Extract JSON object
    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No valid JSON object returned by Groq")

    result = json.loads(content[start:end + 1])

    return {
        "extraction_status": "COMPLETED",
        **result
    }


# =====================================================
# 4. SAVE RESULTS
# =====================================================

def save_results(results):

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "project": "HealthReview AI",
        "agent": "Knowledge Extraction Agent",
        "model": "openai/gpt-oss-120b",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(results),
        "articles": results
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


# =====================================================
# 5. MAIN
# =====================================================

def main():

    print("\n===== KNOWLEDGE EXTRACTION AGENT =====")

    articles = load_articles()

    print("Matched included articles:", len(articles))

    results = []

    for index, (screening, article) in enumerate(articles, 1):

        print(
            f"\n[{index}/{len(articles)}] "
            f"Extracting: {article.get('title', 'Unknown')}"
        )

        try:
            knowledge = extract_knowledge(screening, article)

            results.append({
                "title": article.get("title"),
                "doi": article.get("doi"),
                "pmid": article.get("pmid"),
                "year": article.get("year"),
                "journal": article.get("journal"),
                "abstract_source": article.get("abstract_source"),
                "screening_decision": screening.get("decision"),
                "human_validation": screening.get("human_validation"),
                "knowledge": knowledge
            })

            print("Status:", knowledge["extraction_status"])

        except Exception as error:

            print("EXTRACTION ERROR:", str(error))

            results.append({
                "title": article.get("title"),
                "doi": article.get("doi"),
                "screening_decision": screening.get("decision"),
                "human_validation": screening.get("human_validation"),
                "knowledge": {
                    "extraction_status": "ERROR",
                    "error": str(error)
                }
            })

        # Save progressively to avoid losing completed work
        save_results(results)

    completed = sum(
        item["knowledge"]["extraction_status"] == "COMPLETED"
        for item in results
    )

    print("\n===== EXTRACTION COMPLETED =====")
    print("Matched articles:", len(articles))
    print("Successfully extracted:", completed)
    print("Errors:", len(results) - completed)
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
