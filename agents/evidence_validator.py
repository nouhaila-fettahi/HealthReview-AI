import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent

CHUNKS_FILE = BASE_DIR / "data/processed/document_chunks.json"
EXTRACTED_FILE = BASE_DIR / "data/processed/extracted_knowledge.json"
OUTPUT_FILE = BASE_DIR / "data/processed/evidence_validation.json"


def normalize(text):
    """Normalize whitespace and case for secondary comparison."""
    return " ".join(str(text).split()).casefold()


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_evidence():
    chunks = load_json(CHUNKS_FILE)
    extracted = load_json(EXTRACTED_FILE)

    # Build source index using chunk IDs
    chunk_index = {
        chunk.get("chunk_id"): chunk.get("text", "")
        for chunk in chunks
        if chunk.get("chunk_id")
    }

    report = []
    stats = Counter()

    for article in extracted.get("articles", []):
        knowledge = article.get("knowledge") or {}
        evidences = knowledge.get("supporting_evidence", [])

        for evidence in evidences:
            chunk_id = evidence.get("chunk_id")
            quote = str(evidence.get("quote") or "")
            source_type = article.get("source_type", "UNKNOWN")

            # Validate chunk ID and quotation
            if not chunk_id:
                status = "NO_CHUNK_ID"

            elif chunk_id not in chunk_index:
                status = "INVALID_CHUNK"

            elif not quote.strip():
                status = "NOT_FOUND"

            else:
                source_text = chunk_index[chunk_id]

                if quote in source_text:
                    status = "EXACT"

                elif normalize(quote) in normalize(source_text):
                    status = "PARTIAL"

                else:
                    status = "NOT_FOUND"

            stats[status] += 1

            report.append({
                "article_title": article.get("title"),
                "doi": article.get("doi"),
                "source_type": source_type,
                "claim": evidence.get("claim"),
                "quote": quote,
                "chunk_id": chunk_id,
                "validation_status": status
            })

    # Save validation results
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "total_evidence": len(report),
            "statistics": dict(stats),
            "evidence": report
        }, f, indent=2, ensure_ascii=False)

    # Display validation report
    print("\n===== HEALTHREVIEW AI =====")
    print("EVIDENCE VALIDATION REPORT")
    print("=" * 45)

    print("Total evidence:", len(report))

    for status in [
        "EXACT",
        "PARTIAL",
        "NOT_FOUND",
        "INVALID_CHUNK",
        "NO_CHUNK_ID"
    ]:
        print(f"{status}: {stats[status]}")

    print("\nOutput:", OUTPUT_FILE)


if __name__ == "__main__":
    validate_evidence()
