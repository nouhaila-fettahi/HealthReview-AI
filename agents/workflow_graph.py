
from typing import TypedDict
from pathlib import Path
import json
from datetime import datetime, timezone

from langgraph.graph import StateGraph, START, END

try:
    from .rag_retriever import retrieve_evidence
except ImportError:
    from rag_retriever import retrieve_evidence


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data" / "processed"


# =====================================================
# 1. RESEARCH STATE
# =====================================================

class ResearchState(TypedDict, total=False):
    topic: str
    methodological_quality: dict
    research_question: str

    screening: dict
    knowledge: dict
    synthesis: dict
    quality_report: dict
    prisma: dict

    rag_evidence: list
    rag_answer: dict
    citation_validation: dict

    errors: list
    status: str


# =====================================================
# 2. UTILITY FUNCTIONS
# =====================================================

def load_json(filename):
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    with path.open(encoding="utf-8") as file:
        return json.load(file)


def save_json(filename, data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    path = DATA_DIR / filename

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    return path


# =====================================================
# 3. LOAD EXISTING RESEARCH RESULTS
# =====================================================

def load_existing_results(state: ResearchState):
    """Load existing validated research outputs."""

    print("\n[LANGGRAPH] Loading existing research results...")

    screening = load_json("final_screening_results.json")
    knowledge = load_json("extracted_knowledge.json")
    synthesis = load_json("evidence_synthesis.json")
    quality = load_json("quality_report.json")

    return {
        "screening": screening,
        "knowledge": knowledge,
        "synthesis": synthesis,
        "quality_report": quality,
        "errors": [],
        "status": "RESULTS_LOADED"
    }


# =====================================================
# 4. VALIDATE RESEARCH RESULTS
# =====================================================

def validate_results(state: ResearchState):
    """Check the availability of principal research outputs."""

    print("\n[LANGGRAPH] Validating research outputs...")

    required = [
        "screening",
        "knowledge",
        "synthesis",
        "quality_report"
    ]

    missing = [
        key for key in required
        if not state.get(key)
    ]

    if missing:
        message = f"Missing outputs: {missing}"

        print("Validation failed:", message)

        return {
            "errors": [message],
            "status": "VALIDATION_FAILED"
        }

    print("All required research outputs are available.")

    return {"status": "VALIDATED"}


# =====================================================
# 5. PRISMA STATISTICS
# =====================================================

def generate_prisma_statistics(state: ResearchState):
    """Calculate preliminary screening statistics."""

    print("\n[LANGGRAPH] Calculating PRISMA statistics...")

    data = state["screening"]

    articles = (
        data.get("articles", [])
        if isinstance(data, dict)
        else data
    )

    counts = {
        "records_screened": len(articles),
        "included": 0,
        "excluded": 0,
        "uncertain": 0
    }

    for article in articles:
        decision = article.get("final_decision")

        if decision == "INCLUDE":
            counts["included"] += 1

        elif decision == "EXCLUDE":
            counts["excluded"] += 1

        elif decision == "UNCERTAIN":
            counts["uncertain"] += 1

    output = {
        "screening_statistics": counts,
        "note": (
            "Preliminary counts based on final screening records. "
            "These are not a complete PRISMA 2020 flow diagram."
        )
    }

    output_path = save_json("prisma_statistics.json", output)

    print("PRISMA statistics:", counts)
    print("Saved:", output_path)

    return {
        "prisma": output,
        "status": "PRISMA_GENERATED"
    }


# =====================================================
# 6. RAG RETRIEVAL NODE
# =====================================================

def rag_retrieval_node(state: ResearchState):
    """Retrieve scientific passages from the vector database."""

    print("\n[LANGGRAPH] Retrieving scientific evidence...")

    question = state.get(
        "research_question",
        "How are HL7 FHIR resources transformed into OMOP CDM?"
    )

    evidence = retrieve_evidence(question, k=5)

    output_path = save_json("rag_evidence.json", evidence)

    print("Retrieved passages:", len(evidence))
    print("Evidence saved:", output_path)

    return {
        "rag_evidence": evidence
    }


# =====================================================
# 7. RAG ANSWER NODE
# =====================================================

def rag_answer_node(state: ResearchState):
    """Generate a grounded scientific answer."""

    print("\n[LANGGRAPH] Generating scientific answer...")

    question = state.get(
        "research_question",
        "How are HL7 FHIR resources transformed into OMOP CDM?"
    )

    evidence = state.get("rag_evidence", [])

    try:
        from .rag_answer_agent import generate_answer
    except ImportError:
        from rag_answer_agent import generate_answer

    result = generate_answer(question, evidence)

    result["question"] = question
    result["generated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    json_path = save_json("rag_answer.json", result)

    # Generate Markdown references.
    references = []

    for item in result.get("citations", []):
        ranks = ", ".join(
            str(rank)
            for rank in item.get("evidence_ranks", [])
        )

        references.append(
            f"- {item.get('title')} "
            f"({item.get('year')}). "
            f"DOI: {item.get('doi')}. "
            f"Evidence ranks: {ranks}."
        )

    markdown = (
        "# HealthReview AI - Scientific RAG Answer\n\n"
        f"**Question:** {question}\n\n"
        f"**Evidence status:** {result.get('evidence_status')}\n\n"
        f"{result.get('answer', '')}\n\n"
        "## Retrieved references\n\n"
        + "\n".join(references)
    )

    md_path = DATA_DIR / "rag_answer.md"

    md_path.write_text(
        markdown,
        encoding="utf-8"
    )

    print("Answer generated successfully.")
    print("Unique citations:", len(result.get("citations", [])))
    print("JSON saved:", json_path)
    print("Markdown saved:", md_path)

    return {
        "rag_answer": result,
        "status": "RAG_ANSWER_GENERATED"
    }


# =====================================================
# 8. CITATION VALIDATION NODE
# =====================================================

def citation_validation_node(state: ResearchState):
    """Validate references against retrieved scientific evidence."""

    print("\n[LANGGRAPH] Validating scientific citations...")

    evidence = state.get("rag_evidence", [])
    answer = state.get("rag_answer", {})

    try:
        from .citation_validator import validate_citations
    except ImportError:
        from citation_validator import validate_citations

    validation = validate_citations(evidence, answer)

    output_path = save_json(
        "citation_validation.json",
        validation
    )

    print("Total citations:", validation["total_citations"])
    print("Valid citations:", validation["valid_citations"])
    print("Invalid citations:", validation["invalid_citations"])
    print("Validation status:", validation["validation_status"])
    print("Validation saved:", output_path)

    if validation["validation_status"] == "PASSED":
        status = "CITATIONS_VALIDATED"
    else:
        status = "CITATION_VALIDATION_FAILED"

    return {
        "citation_validation": validation,
        "status": status
    }


# =====================================================
# METHODOLOGICAL QUALITY NODE
# =====================================================

def methodological_quality_node(state: ResearchState):
    """Load the methodological quality assessment."""

    print("\n[LANGGRAPH] Loading methodological quality assessment...")

    try:
        assessment = load_json(
            "methodological_quality_assessment.json"
        )

        print(
            "Articles assessed:",
            assessment.get("successfully_assessed", 0)
        )

        print("Human review required: YES")

        return {
            "methodological_quality": assessment,
            "status": "QUALITY_ASSESSED"
        }

    except Exception as error:
        print("Quality assessment error:", error)

        return {
            "errors": [str(error)],
            "status": "QUALITY_ASSESSMENT_FAILED"
        }

# =====================================================
# 9. FINISH WORKFLOW
# =====================================================

def finish_workflow(state: ResearchState):
    """Display the final workflow status."""

    print("\n[LANGGRAPH] Workflow completed.")

    return {
        "status": state.get("status", "COMPLETED")
    }


# =====================================================
# 10. BUILD LANGGRAPH WORKFLOW
# =====================================================

def build_workflow():

    graph = StateGraph(ResearchState)

    # Register all nodes.
    graph.add_node("load_results", load_existing_results)
    graph.add_node("validate_results", validate_results)
    graph.add_node("prisma_statistics", generate_prisma_statistics)
    graph.add_node("rag_retrieval", rag_retrieval_node)
    graph.add_node("rag_answer", rag_answer_node)
    graph.add_node("citation_validation", citation_validation_node)

    graph.add_node(
        "methodological_quality",
        methodological_quality_node
    )

    graph.add_node("finish", finish_workflow)
    # Define workflow connections.
    graph.add_edge(START, "load_results")

    graph.add_edge(
        "load_results",
        "validate_results"
    )

    graph.add_conditional_edges(
        "validate_results",
        lambda state: (
            "prisma_statistics"
            if state.get("status") == "VALIDATED"
            else "finish"
        )
    )

    graph.add_edge(
        "prisma_statistics",
        "rag_retrieval"
    )

    graph.add_edge(
        "rag_retrieval",
        "rag_answer"
    )

    graph.add_edge(
        "rag_answer",
        "citation_validation"
    )

    graph.add_edge(
    "citation_validation",
    "methodological_quality"
    )

    graph.add_edge(
    "methodological_quality",
    "finish"
    )

    graph.add_edge("finish", END)

    return graph.compile()


# =====================================================
# 11. EXECUTE WORKFLOW
# =====================================================

if __name__ == "__main__":

    workflow = build_workflow()

    initial_state = {
        "topic": (
            "Interoperability between HL7 FHIR "
            "and OMOP CDM in healthcare"
        ),

        "research_question": (
            "How are HL7 FHIR resources transformed "
            "into the OMOP Common Data Model?"
        ),

        "errors": []
    }

    result = workflow.invoke(initial_state)

    print("\n===== LANGGRAPH EXECUTION SUMMARY =====")

    print("Status:", result.get("status"))

    print(
        "PRISMA:",
        result.get("prisma", {}).get("screening_statistics")
    )

    print(
        "Retrieved passages:",
        len(result.get("rag_evidence", []))
    )

    print(
        "Unique citations:",
        len(result.get("rag_answer", {}).get("citations", []))
    )

    print(
        "Citation validation:",
        result.get("citation_validation", {}).get(
            "validation_status"
        )
    )

    print(
        "Valid citations:",
        result.get("citation_validation", {}).get(
            "valid_citations"
        )
    )
