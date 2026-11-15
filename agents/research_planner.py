import os
from typing import List
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


class ResearchPlan(BaseModel):
    research_topic: str = Field(description="Research topic")
    research_question: str = Field(description="Main research question")
    objectives: List[str] = Field(description="Research objectives")
    keywords: List[str] = Field(description="Scientific search keywords")
    databases: List[str] = Field(description="Relevant scientific databases")
    inclusion_criteria: List[str] = Field(description="Inclusion criteria")
    exclusion_criteria: List[str] = Field(description="Exclusion criteria")


class ResearchPlannerAgent:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is missing!")

        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            api_key=api_key,
            temperature=0
        )

        self.parser = PydanticOutputParser(
            pydantic_object=ResearchPlan
        )

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are an expert scientific research planner.
                Create rigorous and reproducible research plans.
                Focus on healthcare interoperability.
                Do not invent scientific references.
                {format_instructions}"""
            ),
            (
                "human",
                "Create a research plan for this topic: {topic}"
            )
        ])

    def run(self, topic: str) -> ResearchPlan:
        chain = self.prompt | self.llm | self.parser

        result = chain.invoke({
            "topic": topic,
            "format_instructions": self.parser.get_format_instructions()
        })

        return result


if __name__ == "__main__":
    agent = ResearchPlannerAgent()

    topic = (
        "Interoperability between HL7 FHIR and OMOP CDM "
        "using ETL pipelines in healthcare"
    )

    print("\n===== RESEARCH PLANNER AGENT =====\n")

    plan = agent.run(topic)

    print(plan.model_dump_json(indent=2))
    print("\n===== PLANNER COMPLETED =====")
