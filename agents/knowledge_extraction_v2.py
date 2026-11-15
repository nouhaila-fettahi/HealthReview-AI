import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from langchain_groq import ChatGroq


# ============================================================
# 1. CONFIGURATION
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

SCREENING_FILE = BASE_DIR / "data" / "processed" / "final_screening_results.json"
ENRICHED_FILE = BASE_DIR / "data" / "processed" / "enriched_articles.json"
CHUNKS_FILE = BASE_DIR / "data" / "processed" / "document_chunks.json"
OUTPUT_FILE = BASE_DIR / "data" / "processed" / "extracted_knowledge.json"

MODEL_NAME = "openai/gpt-oss-120b"
# Reduce further to 3000 if Groq still reports a TPM limit.
MAX_SOURCE_CHARS = 5000

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY is missing. Configure it in Codespaces secrets.")

llm = ChatGroq(model=MODEL_NAME, api_key=api_key, temperature=0)


# ============================================================
# 2. LOAD DATA
# ============================================================
def load_json(path: Path):
    """Load a JSON file using UTF-8 encoding."""
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_data():
    """Load screening records, enriched metadata, and document chunks."""
    screening = load_json(SCREENING_FILE)["articles"]
    enriched_articles = load_json(ENRICHED_FILE)["articles"]
    chunks = load_json(CHUNKS_FILE)

    enriched_by_doi = {
        str(article.get("doi", "")).strip().lower(): article
        for article in enriched_articles
        if article.get("doi")
    }

    chunks_by_doi = defaultdict(list)
    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        doi = str(metadata.get("doi", "")).strip().lower()
        if doi:
            chunks_by_doi[doi].append(chunk)

    return screening, enriched_by_doi, chunks_by_doi


# ============================================================
# 3. BUILD ARTICLE SOURCE
# ============================================================
def build_article_source(screening, enriched_by_doi, chunks_by_doi):
    """Use full-text chunks when available; otherwise use the abstract."""
    doi = str(screening.get("doi", "")).strip().lower()
    article_metadata = enriched_by_doi.get(doi, {})

    article_chunks = sorted(
        chunks_by_doi.get(doi, []),
        key=lambda chunk: chunk.get("metadata", {}).get("chunk_index", 0),
    )

    if article_chunks:
        source_type = "FULL_TEXT"
        source_parts = []
        chunk_ids = []

        for chunk in article_chunks:
            chunk_id = chunk.get("chunk_id", "UNKNOWN")
            text = chunk.get("text", "")
            if text.strip():
                source_parts.append(f"[CHUNK_ID: {chunk_id}]\n{text}")
                chunk_ids.append(chunk_id)

        source_text = "\n\n".join(source_parts)
    else:
        source_type = "ABSTRACT"
        source_text = article_metadata.get("abstract") or ""
        chunk_ids = []

    truncated = len(source_text) > MAX_SOURCE_CHARS
    if truncated:
        source_text = source_text[:MAX_SOURCE_CHARS]

    return {
        "title": screening.get("title", article_metadata.get("title", "")),
        "doi": screening.get("doi"),
        "year": article_metadata.get("year"),
        "journal": article_metadata.get("journal"),
        "source_type": source_type,
        "source_text": source_text,
        "chunk_ids": chunk_ids,
        "source_truncated": truncated,
    }


# ============================================================
# 4. KNOWLEDGE EXTRACTION
# ============================================================
def extract_knowledge(article):
    """Extract structured scientific knowledge from the supplied source only."""
    source_text = article["source_text"]

    if not source_text.strip():
        return {
            "extraction_status": "NO_SOURCE",
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
            "supporting_evidence": [],
        }

    prompt = f"""
You are a scientific literature analysis agent specialized in healthcare interoperability.

Analyze ONLY the source text provided below.

ARTICLE INFORMATION:
Title: {article['title']}
DOI: {article['doi']}
Year: {article['year']}
Journal: {article['journal']}
Source type: {article['source_type']}

RESEARCH SCOPE:
- HL7 and FHIR
- OMOP Common Data Model
- Healthcare interoperability
- ETL pipelines
- Clinical data integration
- Data mapping and transformation

TASK:
Extract structured scientific knowledge from the source.

Return ONE valid JSON object with exactly these keys:

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
      "claim": "scientific claim",
      "quote": "exact quotation copied from source",
      "chunk_id": "chunk identifier or null"
    }}
  ]
}}

STRICT RULES:
1. Never invent information.
2. Use null or empty lists when information is absent.
3. Do not assume a dataset or evaluation method exists.
4. Supporting quotations must be copied exactly.
5. Distinguish HL7, FHIR, OMOP CDM and other standards.
6. Do not use external knowledge.
7. If the source is an abstract, do not claim to have analyzed the full text.
8. Include only evidence actually supported by the source.
9. For full-text evidence, preserve the CHUNK_ID when available.
10. Return valid JSON only, without Markdown fences.
11. Every supporting quote must be copied verbatim from SOURCE TEXT.
12. Never paraphrase or summarize inside the quote field.
13. Never insert ellipses (...) or omit words inside a quotation.
14. Each quote must be a continuous passage from one source chunk.
15. Keep quotes concise (15-40 words whenever possible).
16. Before returning JSON, verify that every quote exists exactly
    in the provided SOURCE TEXT.
17. If no exact supporting quotation is available, do not create
    the evidence item.

18. Every quotation must be copied as one continuous passage
   from SOURCE TEXT.

19. Never use ellipses (...), even when the source passage
   is long.

20. Never combine separate sentences or passages into
   a single quotation.

21. Do not correct spelling, grammar, punctuation,
   abbreviations, or reference numbers in quotations.

22. Do not replace words with synonyms or paraphrase
   any part of a quotation.

23. Each quotation must be directly searchable as an
   exact substring of SOURCE TEXT.

24. If no exact quotation can be identified, omit the
   evidence item rather than generating an approximate
   quotation.

25. Keep each quotation short and focused, preferably
   between 15 and 40 words, while preserving its exact
   wording.

SOURCE TEXT:
{source_text}
"""

    response = llm.invoke(prompt)
    content = response.content

    if isinstance(content, list):
        content = "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )

    content = str(content).strip()
    start = content.find("{")
    if start == -1:
        raise ValueError("No JSON object returned by the model.")

    result, _ = json.JSONDecoder().raw_decode(content[start:])
    return result


# ============================================================
# 5. SAVE RESULTS PROGRESSIVELY
# ============================================================
def save_results(results):
    """Write results to a temporary file, then replace the output file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "project": "HealthReview AI",
        "agent": "Knowledge Extraction Agent",
        "model": MODEL_NAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(results),
        "articles": results,
    }

    temporary_file = OUTPUT_FILE.with_suffix(".tmp")
    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2, ensure_ascii=False)

    temporary_file.replace(OUTPUT_FILE)


# ============================================================
# 6. MAIN PIPELINE
# ============================================================

def main():
    print("\n===== HEALTHREVIEW AI =====")
    print("KNOWLEDGE EXTRACTION AGENT V2")
    print("=" * 55)

    # 1. Load input data
    screening_articles, enriched_by_doi, chunks_by_doi = load_data()

    # 2. Keep only articles approved in final screening
    included_articles = [
        article
        for article in screening_articles
        if article.get("final_decision") == "INCLUDE"
    ]

    print("Included articles:", len(included_articles))

    if not included_articles:
        print("No included articles found. Extraction stopped.")
        return

    # 3. Load previous extraction results
    if OUTPUT_FILE.exists():
        existing_articles = load_json(OUTPUT_FILE).get("articles", [])
    else:
        existing_articles = []

    # 4. Identify DOIs belonging to the final included corpus
    included_dois = {
        str(article.get("doi", "")).strip().lower()
        for article in included_articles
        if article.get("doi")
    }

    # 5. Keep only successful results for currently included articles
    results = [
        item for item in existing_articles
        if (
            item.get("knowledge") is not None
            and str(item.get("doi", "")).strip().lower() in included_dois
        )
    ]

    completed_dois = {
        str(item.get("doi", "")).strip().lower()
        for item in results
        if item.get("doi")
    }
    # Save the cleaned results, even if all articles are skipped.
    save_results(results)

    print("Previously completed extractions:", len(completed_dois))

    # 6. Extract knowledge article by article
    for index, screening in enumerate(included_articles, start=1):

        article = build_article_source(
            screening,
            enriched_by_doi,
            chunks_by_doi,
        )

        doi_key = str(article.get("doi", "")).strip().lower()

        print(f"\n[{index}/{len(included_articles)}] {article['title']}")

        if doi_key and doi_key in completed_dois:
            print("Extraction: SKIPPED (already successful)")
            continue

        print("Source:", article["source_type"])
        print("Chunks:", len(article["chunk_ids"]))
        print("Source truncated:", article["source_truncated"])

        try:
            knowledge = extract_knowledge(article)

            record = {
                "title": article["title"],
                "doi": article["doi"],
                "year": article["year"],
                "journal": article["journal"],
                "source_type": article["source_type"],
                "source_truncated": article["source_truncated"],
                "source_chunk_ids": article["chunk_ids"],
                "screening_decision": "INCLUDE",
                "human_validation": screening.get(
                    "human_validation", "PENDING"
                ),
                "knowledge": knowledge,
                "extraction_error": None,
            }

            print("Extraction: SUCCESS")

            if doi_key:
                completed_dois.add(doi_key)

        except Exception as error:

            print("Extraction error:", str(error))

            record = {
                "title": article["title"],
                "doi": article["doi"],
                "year": article["year"],
                "journal": article["journal"],
                "source_type": article["source_type"],
                "source_truncated": article["source_truncated"],
                "source_chunk_ids": article["chunk_ids"],
                "screening_decision": "INCLUDE",
                "human_validation": screening.get(
                    "human_validation", "PENDING"
                ),
                "knowledge": None,
                "extraction_error": str(error),
            }

        # 7. Save after every article
        results.append(record)
        save_results(results)

    # 8. Final summary
    successful = sum(
        1 for item in results
        if item.get("knowledge") is not None
    )

    failed = sum(
        1 for item in results
        if item.get("knowledge") is None
    )

    print("\n===== EXTRACTION SUMMARY =====")
    print("Included articles:", len(included_articles))
    print("Successful extractions:", successful)
    print("Failed extractions:", failed)
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
