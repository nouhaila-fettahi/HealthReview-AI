

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

results = vectorstore.similarity_search_with_score(
    question,
    k=5
)

print("\n===== SEMANTIC SEARCH RESULTS =====")
print("Question:", question)

for i, (doc, score) in enumerate(results, 1):
    print(f"\n--- RESULT {i} ---")
    print("Title:", doc.metadata.get("title"))
    print("DOI:", doc.metadata.get("doi"))
    print("Year:", doc.metadata.get("year"))
    print("Section:", doc.metadata.get("section"))
    print("Distance:", round(score, 4))
    print("Text:", doc.page_content[:700], "...")
