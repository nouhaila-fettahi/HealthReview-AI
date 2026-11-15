
import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Project paths
ROOT = Path(__file__).resolve().parent.parent
CHUNKS_FILE = ROOT / "data" / "processed" / "document_chunks.json"
VECTORSTORE_DIR = ROOT / "data" / "vectorstore"

COLLECTION_NAME = "healthreview_articles"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_chunks():
    """Load extracted document chunks."""
    with CHUNKS_FILE.open(encoding="utf-8") as f:
        chunks = json.load(f)

    documents = []

    for chunk in chunks:
        text = chunk.get("text", "").strip()
        metadata = chunk.get("metadata", {})

        if not text:
            continue

        clean_metadata = {
            key: value
            for key, value in metadata.items()
            if value is not None
            and isinstance(value, (str, int, float, bool))
        }

        documents.append(
            Document(
                page_content=text,
                metadata=clean_metadata
            )
        )

    return documents


def build_vectorstore():
    """Create and persist the Chroma vector database."""

    documents = load_chunks()
    print(f"Loaded {len(documents)} chunks.")

    if not documents:
        raise ValueError("No valid document chunks found.")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(VECTORSTORE_DIR)
    )

    existing_count = vectorstore._collection.count()

    if existing_count > 0:
        print("Existing vector database detected.")
        print(f"Stored chunks: {existing_count}")
        print("No duplicate documents added.")
        return vectorstore

    ids = [f"chunk_{i}" for i in range(len(documents))]

    print("Generating embeddings and indexing documents...")

    vectorstore.add_documents(
        documents=documents,
        ids=ids
    )

    print("\n===== VECTOR STORE SUMMARY =====")
    print(f"Collection: {COLLECTION_NAME}")
    print(f"Embedding model: {EMBEDDING_MODEL}")
    print(f"Stored chunks: {vectorstore._collection.count()}")
    print(f"Database: {VECTORSTORE_DIR}")

    return vectorstore


if __name__ == "__main__":
    build_vectorstore()
