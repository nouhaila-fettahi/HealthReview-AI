
import os
import json
from pathlib import Path
from datetime import datetime, timezone

from langchain_groq import ChatGroq

try:
    from .rag_retriever import retrieve_evidence
except ImportError:
    from rag_retriever import retrieve_evidence


ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = ROOT / "data/processed/rag_evidence.json"
OUTPUT_JSON = ROOT / "data/processed/rag_answer.json"
OUTPUT_MD = ROOT / "data/processed/rag_answer.md"

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing!")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=api_key,
    temperature=0
)


def build_unique_citations(evidence):
    """Group retrieved passages by article to avoid duplicate references."""

    grouped = {}

    for item in evidence:
        # DOI is the preferred identifier; title is the fallback.
        key = item.get("doi") or item.get("title")

        if not key:
            key = f"unknown_article_{item.get('rank', 'unknown')}"

        if key not in grouped:
            grouped[key] = {
                "title": item.get("title"),
                "doi": item.get("doi"),
                "year": item.get("year"),
                "sections": [],
                "evidence_ranks": []
            }

        section = item.get("section")
        if section and section not in grouped[key]["sections"]:
            grouped[key]["sections"].append(section)

        rank = item.get("rank")
        if rank is not None and rank not in grouped[key]["evidence_ranks"]:
            grouped[key]["evidence_ranks"].append(rank)

    return list(grouped.values())


def generate_answer(question, evidence):
    """Generate a grounded answer using retrieved scientific evidence."""

    if not evidence:
        return {
            "answer": "Insufficient scientific evidence was retrieved.",
            "citations": [],
            "evidence_status": "INSUFFICIENT"
        }

    prompt = f"""
You are HealthReview AI, a scientific research assistant
specialized in healthcare interoperability.

Answer the research question using ONLY the scientific
evidence provided below.

RESEARCH QUESTION:
{question}

RETRIEVED SCIENTIFIC EVIDENCE:
{json.dumps(evidence, ensure_ascii=False, indent=2)}

INSTRUCTIONS:

1. Use only the retrieved passages.
2. Do not invent facts, methods, or results.
3. Distinguish findings from interpretations.
4. Cite every important scientific claim using the
   article title, DOI, year, and evidence rank.
5. If the evidence is insufficient, say so explicitly.
6. Do not claim that one article represents the entire field.
7. Mention when evidence comes from a single article.
8. Do not invent references.

Return a structured scientific answer containing:

- Direct answer
- Main findings
- Technical explanation
- Limitations of the available evidence
- References

"""

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "citations": build_unique_citations(evidence),
        "evidence_status": "RETRIEVED",
        "model": "openai/gpt-oss-120b"
    }


def main():

    question = (
        "How are HL7 FHIR resources transformed "
        "into the OMOP Common Data Model?"
    )

    print("===== HEALTHREVIEW AI - RAG ANSWER AGENT =====")

    # Reuse previously retrieved evidence when available.
    if INPUT_FILE.exists():
        with INPUT_FILE.open(encoding="utf-8") as file:
            evidence = json.load(file)
        print("Existing retrieved evidence loaded.")
    else:
        evidence = retrieve_evidence(question, k=5)
        print("New evidence retrieved.")

    result = generate_answer(question, evidence)

    result["question"] = question
    result["generated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT_JSON.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # Generate Markdown references without duplicates.
    references = []

    for item in result["citations"]:
        ranks = ", ".join(
            str(rank) for rank in item["evidence_ranks"]
        )

        references.append(
            f"- {item['title']} ({item['year']}). "
            f"DOI: {item['doi']}. "
            f"Evidence ranks: {ranks}."
        )

    OUTPUT_MD.write_text(
        "# HealthReview AI - Scientific RAG Answer\n\n"
        f"**Question:** {question}\n\n"
        f"**Evidence status:** {result['evidence_status']}\n\n"
        f"{result['answer']}\n\n"
        "## Retrieved references\n\n"
        + "\n".join(references),
        encoding="utf-8"
    )

    print("\n===== RAG ANSWER GENERATED =====")
    print("JSON:", OUTPUT_JSON)
    print("Markdown:", OUTPUT_MD)
    print("Unique citations:", len(result["citations"]))
    print("Retrieved passages:", len(evidence))


if __name__ == "__main__":
    main()
