import os
import json
from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser


class ScreeningDecision(BaseModel):
    decision: Literal["INCLUDE", "EXCLUDE", "UNCERTAIN"]
    reason: str = Field(description="Explanation of the decision")
    matched_inclusion_criteria: List[str]
    matched_exclusion_criteria: List[str]
    supporting_evidence: str = Field(
        description="Short evidence from the title or abstract"
    )


class ScreeningAgent:

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError("GROQ_API_KEY is missing!")

        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            api_key=api_key,
            temperature=0,
            max_retries=2
        )

        self.parser = PydanticOutputParser(
            pydantic_object=ScreeningDecision
        )

        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
                You are a scientific literature screening assistant.

                Evaluate the publication using ONLY its title and abstract
                and the supplied inclusion and exclusion criteria.

                Rules:
                - INCLUDE: the available evidence supports relevance.
                - EXCLUDE: the available evidence clearly meets an
                  exclusion criterion.
                - UNCERTAIN: evidence is insufficient or ambiguous.
                - Never invent information or references.
                - Do not treat missing information as proof of exclusion.
                - Quote short supporting evidence from the supplied text.
                - Apply the criteria consistently.

                {format_instructions}
                """
            ),
            (
                "human",
                """
                TITLE:
                {title}

                ABSTRACT:
                {abstract}

                INCLUSION CRITERIA:
                {inclusion}

                EXCLUSION CRITERIA:
                {exclusion}
                """
            )
        ])

    def screen(self, article, inclusion, exclusion):

        chain = self.prompt | self.llm | self.parser

        result = chain.invoke({
            "title": article.get("title", ""),
            "abstract": article.get("abstract", ""),
            "inclusion": json.dumps(inclusion, ensure_ascii=False),
            "exclusion": json.dumps(exclusion, ensure_ascii=False),
            "format_instructions": self.parser.get_format_instructions()
        })

        return result


def main():

    input_path = Path("data/processed/enriched_articles.json")
    planner_path = Path("planner_output.json")
    output_path = Path("data/processed/screening_results.json")

    with input_path.open(encoding="utf-8") as file:
        corpus = json.load(file)

    planner_text = planner_path.read_text(encoding="utf-8")

    # Extract JSON after the Research Planner header
    json_start = planner_text.find("{")

    if json_start == -1:
        raise ValueError("No JSON object found in planner_output.json")

    plan, _ = json.JSONDecoder().raw_decode(
        planner_text[json_start:]
    )

    inclusion = plan["inclusion_criteria"]
    exclusion = plan["exclusion_criteria"]

    agent = ScreeningAgent()
    results = []

    articles = corpus["articles"]

    for index, article in enumerate(articles, start=1):

        title = article.get("title") or "Unknown title"
        abstract = article.get("abstract")

        print(f"\n[{index}/{len(articles)}] Screening: {title[:70]}")

        record = {
            "title": title,
            "doi": article.get("doi"),
            "pmid": article.get("pmid"),
            "abstract_source": article.get("abstract_source"),
            "decision": "UNCERTAIN",
            "reason": "",
            "matched_inclusion_criteria": [],
            "matched_exclusion_criteria": [],
            "supporting_evidence": "",
            "human_validation": "PENDING"
        }

        if not abstract:
            record["reason"] = (
                "Abstract unavailable. Full-text or additional "
                "information is required for screening."
            )
            results.append(record)
            print("Decision: UNCERTAIN (missing abstract)")
            continue

        try:
            decision = agent.screen(
                article,
                inclusion,
                exclusion
            )

            record.update(decision.model_dump())
            print("Decision:", record["decision"])

        except Exception as error:
            record["reason"] = (
                f"Screening could not be completed: {str(error)}"
            )
            print("Screening error:", error)

        results.append(record)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "total_articles": len(results),
        "include": sum(
            x["decision"] == "INCLUDE" for x in results
        ),
        "exclude": sum(
            x["decision"] == "EXCLUDE" for x in results
        ),
        "uncertain": sum(
            x["decision"] == "UNCERTAIN" for x in results
        ),
        "articles": results
    }

    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n===== SCREENING COMPLETED =====")
    print("Total:", output["total_articles"])
    print("Include:", output["include"])
    print("Exclude:", output["exclude"])
    print("Uncertain:", output["uncertain"])
    print("Saved to:", output_path)


if __name__ == "__main__":
    main()
