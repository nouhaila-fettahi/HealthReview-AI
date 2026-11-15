
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

EVIDENCE_FILE = ROOT / "data/processed/rag_evidence.json"
ANSWER_FILE = ROOT / "data/processed/rag_answer.json"
OUTPUT_FILE = ROOT / "data/processed/citation_validation.json"


def normalize_doi(doi):
    """Normalize DOI values for comparison."""

    if not doi:
        return ""

    doi = str(doi).strip().lower()

    doi = doi.replace("https://doi.org/", "")
    doi = doi.replace("http://doi.org/", "")
    doi = doi.replace("doi:", "")

    return doi.strip()


def validate_citations(evidence, answer):
    """Validate generated references against retrieved evidence."""

    evidence_dois = {
        normalize_doi(item.get("doi"))
        for item in evidence
        if item.get("doi")
    }

    evidence_ranks = {
        item.get("rank")
        for item in evidence
        if item.get("rank") is not None
    }

    evidence_articles = {}

    for item in evidence:
        doi = normalize_doi(item.get("doi"))

        if doi:
            evidence_articles[doi] = item

    results = []

    for citation in answer.get("citations", []):

        doi = normalize_doi(citation.get("doi"))

        ranks = citation.get("evidence_ranks", [])

        doi_valid = doi in evidence_dois

        valid_ranks = [
            rank for rank in ranks
            if rank in evidence_ranks
        ]

        ranks_valid = (
            len(ranks) > 0
            and len(valid_ranks) == len(ranks)
        )

        article = evidence_articles.get(doi, {})

        title_valid = (
            citation.get("title") == article.get("title")
            if article else False
        )

        year_valid = (
            citation.get("year") == article.get("year")
            if article else False
        )

        is_valid = (
            doi_valid
            and ranks_valid
            and title_valid
            and year_valid
        )

        results.append({
            "title": citation.get("title"),
            "doi": citation.get("doi"),
            "doi_valid": doi_valid,
            "title_valid": title_valid,
            "year_valid": year_valid,
            "ranks_valid": ranks_valid,
            "valid_ranks": valid_ranks,
            "status": "VALID" if is_valid else "INVALID"
        })

    valid_count = sum(
        item["status"] == "VALID"
        for item in results
    )

    return {
        "total_citations": len(results),
        "valid_citations": valid_count,
        "invalid_citations": len(results) - valid_count,
        "validation_status": (
            "PASSED"
            if len(results) > 0 and valid_count == len(results)
            else "FAILED"
        ),
        "citation_results": results
    }


def main():

    print("===== CITATION VALIDATION AGENT =====")

    if not EVIDENCE_FILE.exists():
        raise FileNotFoundError(EVIDENCE_FILE)

    if not ANSWER_FILE.exists():
        raise FileNotFoundError(ANSWER_FILE)

    with EVIDENCE_FILE.open(encoding="utf-8") as file:
        evidence = json.load(file)

    with ANSWER_FILE.open(encoding="utf-8") as file:
        answer = json.load(file)

    result = validate_citations(evidence, answer)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_FILE.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("Total citations:", result["total_citations"])
    print("Valid citations:", result["valid_citations"])
    print("Invalid citations:", result["invalid_citations"])
    print("Validation status:", result["validation_status"])
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
