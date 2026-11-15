

from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

ROOT = Path(__file__).resolve().parent.parent
VECTORSTORE_DIR = ROOT / "data" / "vectorstore"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)

vectorstore = Chroma(
    collection_name="healthreview_articles",
    embedding_function=embeddings,
    persist_directory=str(VECTORSTORE_DIR)
)

question = (
    "Which studies describe ETL pipelines transforming "
    "HL7 FHIR data into the OMOP Common Data Model?"
)

retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={
        "k": 5,
        "fetch_k": 30,
        "lambda_mult": 0.5
    }
)

results = retriever.invoke(question)

print("\n===== MMR RETRIEVAL RESULTS =====")

seen = set()

for i, doc in enumerate(results, 1):
    title = doc.metadata.get("title", "Unknown")
    doi = doc.metadata.get("doi", "Unknown")

    seen.add(doi)

    print(f"\n--- RESULT {i} ---")
    print("Title:", title)
    print("DOI:", doi)
    print("Year:", doc.metadata.get("year"))
    print("Section:", doc.metadata.get("section"))
    print("Text:", doc.page_content[:500], "...")

print("\n===== DIVERSITY SUMMARY =====")
print("Retrieved chunks:", len(results))
print("Unique articles:", len(seen))
