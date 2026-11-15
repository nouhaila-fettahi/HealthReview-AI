import argparse
import json
import subprocess
import sys
from pathlib import Path

from agents.research_planner import ResearchPlannerAgent
from agents.literature_search import LiteratureSearchAgent
from agents.pubmed_search import PubMedSearchAgent
from agents.merge_deduplicate import merge_articles

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data/raw"
PROCESSED_DIR = BASE_DIR / "data/processed"

TOPIC = (
    "Interoperability between HL7 FHIR and OMOP CDM "
    "using ETL pipelines in healthcare"
)

PUBMED_QUERY = (
    '("FHIR" OR "Fast Healthcare Interoperability Resources") '
    'AND ("OMOP" OR "Observational Medical Outcomes Partnership") '
    'AND (interoperability OR ETL OR mapping OR transformation)'
)


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"[SAVED] {path.relative_to(BASE_DIR)}")


def run_script(script):
    print(f"\n[RUNNING] {script}")
    subprocess.run(
        [sys.executable, str(BASE_DIR / script)],
        cwd=BASE_DIR,
        check=True
    )


def run_new_search():
    print("\n===== 1. RESEARCH PLANNER =====")

    planner = ResearchPlannerAgent()
    plan = planner.run(TOPIC)

    plan_data = (
        plan.model_dump()
        if hasattr(plan, "model_dump")
        else plan
    )

    save_json(PROCESSED_DIR / "planner_output.json", plan_data)

    print("\n===== 2. LITERATURE SEARCH =====")

    openalex = LiteratureSearchAgent()
    openalex_results = openalex.search(TOPIC, max_results=10)

    pubmed = PubMedSearchAgent()
    pubmed_results = pubmed.search(PUBMED_QUERY, max_results=10)

    save_json(
        RAW_DIR / "openalex_results.json",
        {"articles": openalex_results}
    )

    save_json(
        RAW_DIR / "pubmed_results.json",
        {"articles": pubmed_results}
    )

    print("\n===== 3. MERGE & DEDUPLICATION =====")
    merge_articles()

    print("\n===== 4. ABSTRACT ENRICHMENT =====")
    run_script("agents/enrich_abstracts.py")

    print("\n===== 5. AI SCREENING =====")
    run_script("agents/screening.py")

    print("\n===== 6. HUMAN VALIDATION =====")
    from agents.human_validation import validate_articles
    validate_articles()

    print(
        "\nHuman validation finished. "
        "Check final_screening_results.json before continuing."
    )


def run_downstream_pipeline():
    required_files = [
        PROCESSED_DIR / "final_screening_results.json",
    ]

    for path in required_files:
        if not path.exists():
            raise FileNotFoundError(
                f"Required file missing: {path}"
            )

    print("\n===== 7. DOI RESOLUTION =====")
    if not (PROCESSED_DIR / "doi_resolution_results.json").exists():
        run_script("agents/batch_doi_resolver.py")
    else:
        print("[REUSE] DOI resolution results already exist.")

    print("\n===== 8. FULL-TEXT RETRIEVAL =====")
    manifest = PROCESSED_DIR / "fulltext_manifest.json"

    if not manifest.exists():
        run_script("agents/fulltext_retrieval.py")
    else:
        print("[REUSE] Full-text manifest already exists.")

    print("\n===== 9. DOCUMENT PROCESSING =====")
    documents = PROCESSED_DIR / "extracted_documents.json"
    chunks = PROCESSED_DIR / "document_chunks.json"

    if not documents.exists() or not chunks.exists():
        run_script("agents/document_processor.py")
    else:
        print("[REUSE] Extracted documents and chunks already exist.")

    print("\n===== 10. KNOWLEDGE EXTRACTION =====")
    if not (PROCESSED_DIR / "extracted_knowledge.json").exists():
        run_script("agents/knowledge_extraction_v2.py")
    else:
        print("[REUSE] Extracted knowledge already exists.")

    print("\n===== 11. EVIDENCE SYNTHESIS =====")
    if not (PROCESSED_DIR / "evidence_synthesis.json").exists():
        run_script("agents/evidence_synthesis.py")
    else:
        print("[REUSE] Evidence synthesis already exists.")

    print("\n===== 12. CRITIC / QUALITY ASSURANCE =====")
    if not (PROCESSED_DIR / "quality_report.json").exists():
        run_script("agents/critic_agent.py")
    else:
        print("[REUSE] Quality report already exists.")

    print("\n===== HEALTHREVIEW AI PIPELINE COMPLETED =====")


def main():
    parser = argparse.ArgumentParser(
        description="HealthReview AI - Research pipeline orchestrator"
    )

    parser.add_argument(
        "--new-search",
        action="store_true",
        help="Start a new literature search and human validation"
    )

    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if args.new_search:
        run_new_search()
    else:
        print("MODE: RESUME EXISTING RESULTS")
        print("Existing research outputs will be preserved.")
        run_downstream_pipeline()


if __name__ == "__main__":
    main()
