from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


ROOT = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = ROOT / "data" / "vectorstore"

COLLECTION_NAME = "healthreview_articles"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_vectorstore():
    """Connect to the existing ChromaDB collection."""

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTORSTORE_DIR)
    )

    return vectorstore


def retrieve_evidence(question: str, k: int = 5):
    """Retrieve relevant scientific passages with source metadata."""

    if not question or not question.strip():
        raise ValueError("Research question cannot be empty.")

    vectorstore = get_vectorstore()

    results = vectorstore.similarity_search_with_score(
        question,
        k=k
    )

    evidence = []

    for rank, (doc, distance) in enumerate(results, start=1):
        evidence.append({
            "rank": rank,
            "title": doc.metadata.get("title", "Unknown"),
            "doi": doc.metadata.get("doi"),
            "year": doc.metadata.get("year"),
            "section": doc.metadata.get("section"),
            "distance": float(distance),
            "text": doc.page_content
        })

    return evidence


if __name__ == "__main__":

    question = (
        "How are HL7 FHIR resources transformed "
        "into the OMOP Common Data Model?"
    )

    results = retrieve_evidence(question, k=5)

    print("\n===== RAG RETRIEVAL RESULTS =====")
    print("Question:", question)
    print("Retrieved passages:", len(results))

    for item in results:
        print(f"\n--- Evidence {item['rank']} ---")
        print("Title:", item["title"])
        print("DOI:", item["doi"])
        print("Year:", item["year"])
        print("Section:", item["section"])
        print("Distance:", round(item["distance"], 4))
        print("Text:", item["text"][:500])
