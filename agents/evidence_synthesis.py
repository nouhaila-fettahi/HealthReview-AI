import os
import json
import re
from json_repair import repair_json
from pathlib import Path
from datetime import datetime, timezone

from langchain_groq import ChatGroq


# =====================================================
# 1. CONFIGURATION
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = BASE_DIR / "data/processed/extracted_knowledge.json"
OUTPUT_FILE = BASE_DIR / "data/processed/evidence_synthesis.json"

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing!")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=api_key,
    temperature=0
)


# =====================================================
# 2. LOAD EXTRACTED KNOWLEDGE
# =====================================================


def load_knowledge():

    with open(INPUT_FILE, encoding="utf-8") as f:
        data = json.load(f)

    articles = [
        article
        for article in data.get("articles", [])
        if (
            isinstance(article.get("knowledge"), dict)
            and article.get("knowledge")
            and article.get("extraction_error") is None
        )
    ]

    if not articles:
        raise ValueError("No valid extracted knowledge found!")

    print("Valid knowledge records:", len(articles))

    return articles



# =====================================================
# 3. PREPARE SCIENTIFIC EVIDENCE
# =====================================================


def prepare_evidence(articles):

    evidence = []

    for index, article in enumerate(articles, 1):

        knowledge = article.get("knowledge", {})

        evidence.append({
            "article_id": f"A{index}",
            "title": article.get("title"),
            "year": article.get("year"),
            "doi": article.get("doi"),
            "source_type": article.get("source_type"),
            "source_chunk_ids": article.get("source_chunk_ids", []),

            "healthcare_standards": knowledge.get(
                "healthcare_standards", []
            ),
            "etl_architecture": knowledge.get("etl_architecture"),
            "mapping_techniques": knowledge.get(
                "mapping_techniques", []
            ),
            "data_sources": knowledge.get("data_sources", []),
            "datasets": knowledge.get("datasets", []),
            "evaluation_methods": knowledge.get(
                "evaluation_methods", []
            ),
            "main_findings": knowledge.get("main_findings", []),
            "limitations": knowledge.get("limitations", []),
            "future_directions": knowledge.get(
                "future_directions", []
            ),
            "supporting_evidence": knowledge.get(
                "supporting_evidence", []
            )
        })

    return evidence

# =====================================================
# 4. GENERATE EVIDENCE SYNTHESIS
# =====================================================

def synthesize_evidence(evidence):

    prompt = f"""
You are a scientific research synthesis assistant
specialized in healthcare interoperability.

Your task is to synthesize the scientific evidence
extracted from the following research articles.

SCIENTIFIC EVIDENCE:

{json.dumps(evidence, ensure_ascii=False, indent=2)}

OBJECTIVE:

Produce a comparative synthesis focusing on:

1. HL7 and FHIR standards.
2. OMOP Common Data Model.
3. Healthcare interoperability.
4. ETL architectures and pipelines.
5. Data mapping and transformation.
6. Clinical data integration.
7. Evaluation methods and research limitations.

Return ONLY one valid JSON object with this structure:

{{
  "research_overview": "string",
  "main_themes": [
    {{
      "theme": "string",
      "description": "string",
      "supporting_articles": ["A1"]
    }}
  ],
  "comparative_analysis": [
    {{
      "dimension": "string",
      "observations": "string",
      "supporting_articles": ["A1"]
    }}
  ],
  "research_gaps": [
    {{
      "gap": "string",
      "explanation": "string",
      "supporting_articles": ["A1"]
    }}
  ],
  "future_research_directions": [
    {{
      "direction": "string",
      "justification": "string",
      "supporting_articles": ["A1"]
    }}
  ],
  "overall_conclusion": "string"
}}

STRICT RULES:

1. Use ONLY the supplied extracted evidence.
2. Never invent scientific findings.
3. Do not assume that all articles use FHIR or OMOP.
4. Distinguish HL7, FHIR and OMOP CDM.
5. Every theme and comparison must cite supporting article IDs.
6. Do not invent research gaps. If evidence is insufficient,
   explicitly state that.
7. Distinguish observed findings from interpretations.
8. Return valid JSON only, without Markdown fences.
9. Cite only article IDs that exist in the supplied evidence.
10. Never present abstract-based evidence as full-text evidence.
11. Do not create numerical statistics or quantitative comparisons
    unless explicitly present in the supplied evidence.
12. When evidence is insufficient, state this explicitly.
13. Preserve the distinction between reported findings
    and your own cross-article interpretation.
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

    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    start = content.find("{")
    end = content.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No valid JSON returned by Groq")
    result = repair_json(
        content[start:end + 1],
        return_objects=True
    )

    return result


# =====================================================
# 5. SAVE SYNTHESIS
# =====================================================

def save_synthesis(synthesis, evidence):

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "project": "HealthReview AI",
        "agent": "Evidence Synthesis Agent",
        "model": "openai/gpt-oss-120b",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(evidence),
        "source_articles": evidence,
        "synthesis": synthesis
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("\nSynthesis saved:", OUTPUT_FILE)


# =====================================================
# 6. MAIN
# =====================================================

def main():

    print("\n===== EVIDENCE SYNTHESIS AGENT =====")

    articles = load_knowledge()

    print("Completed articles:", len(articles))

    evidence = prepare_evidence(articles)

    print("Scientific evidence prepared.")

    synthesis = synthesize_evidence(evidence)

    save_synthesis(synthesis, evidence)

    print("\n===== SYNTHESIS COMPLETED =====")
    print("Articles analyzed:", len(evidence))
    print("Themes:", len(synthesis.get("main_themes", [])))
    print("Research gaps:", len(synthesis.get("research_gaps", [])))
    print("Comparisons:", len(synthesis.get("comparative_analysis", [])))


if __name__ == "__main__":
    main()