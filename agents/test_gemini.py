import os
from langchain_google_genai import ChatGoogleGenerativeAI

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing!")

print("Connecting to Gemini...")

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=api_key,
    temperature=0
)

response = llm.invoke(
    "Explain the difference between HL7 FHIR and OMOP CDM "
    "in three concise scientific paragraphs."
)

print("\n===== GEMINI RESPONSE =====\n")
print(response.content)
print("\n===== TEST COMPLETED =====")
