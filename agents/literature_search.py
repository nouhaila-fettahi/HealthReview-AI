import requests
from typing import List, Dict


class LiteratureSearchAgent:

    def __init__(self):
        self.base_url = "https://api.openalex.org/works"

    def search(self, query: str, max_results: int = 10) -> List[Dict]:

        print(f"Searching OpenAlex for: {query}")

        params = {
            "search": query,
            "per_page": max_results,
            "sort": "relevance_score:desc"
        }

        response = requests.get(
            self.base_url,
            params=params,
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        articles = []

        for item in data.get("results", []):

            authors = [
                author.get("author", {}).get("display_name", "")
                for author in item.get("authorships", [])[:3]
            ]

            source = item.get("primary_location") or {}
            source = source.get("source") or {}

            article = {
                "title": item.get("title"),
                "year": item.get("publication_year"),
                "doi": item.get("doi"),
                "authors": authors,
                "journal": source.get("display_name"),
                "cited_by": item.get("cited_by_count", 0),
                "openalex_id": item.get("id")
            }

            articles.append(article)

        return articles


if __name__ == "__main__":

    agent = LiteratureSearchAgent()

    query = (
        "HL7 FHIR OMOP CDM healthcare "
        "interoperability ETL pipelines"
    )

    results = agent.search(query, max_results=10)

    print("\n===== LITERATURE SEARCH RESULTS =====\n")

    for index, article in enumerate(results, start=1):
        print(f"\nArticle {index}")
        print("Title:", article["title"])
        print("Year:", article["year"])
        print("Authors:", ", ".join(article["authors"]))
        print("Journal:", article["journal"])
        print("DOI:", article["doi"])
        print("Citations:", article["cited_by"])

    print(f"\nTotal articles retrieved: {len(results)}")
    print("\n===== SEARCH COMPLETED =====")
