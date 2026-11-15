import os
from langchain_groq import ChatGroq

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY is missing!")

print("Connecting to Groq...")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=api_key,
    temperature=0
)

response = llm.invoke(
    "Explain the difference between HL7 FHIR and OMOP CDM "
    "in three concise scientific paragraphs."
)

print("\n===== GROQ RESPONSE =====\n")
print(response.content)
print("\n===== TEST COMPLETED =====")
