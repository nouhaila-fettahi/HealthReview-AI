import requests
from typing import List, Dict


class PubMedSearchAgent:

    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "HealthReviewAI/1.0 (research project)"
        })

    def search(self, query: str, max_results: int = 10) -> List[Dict]:

        print(f"Searching PubMed for: {query}")

        # Step 1: Retrieve PubMed IDs
        search_response = self.session.get(
            self.base_url + "esearch.fcgi",
            params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "sort": "relevance"
            },
            timeout=30
        )

        search_response.raise_for_status()
        search_data = search_response.json()

        pmids = search_data["esearchresult"]["idlist"]

        if not pmids:
            return []

        # Step 2: Retrieve article summaries
        summary_response = self.session.get(
            self.base_url + "esummary.fcgi",
            params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json"
            },
            timeout=30
        )

        summary_response.raise_for_status()
        summary_data = summary_response.json()["result"]

        articles = []

        for pmid in pmids:
            item = summary_data.get(pmid, {})

            if not item:
                continue

            authors = [
                author.get("name", "")
                for author in item.get("authors", [])[:3]
            ]

            doi = None

            for article_id in item.get("articleids", []):
                if article_id.get("idtype") == "doi":
                    doi = article_id.get("value")
                    break

            article = {
                "source": "PubMed",
                "pmid": pmid,
                "title": item.get("title"),
                "year": item.get("pubdate", "")[:4],
                "authors": authors,
                "journal": item.get("fulljournalname"),
                "doi": doi,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            }

            articles.append(article)

        return articles


if __name__ == "__main__":

    agent = PubMedSearchAgent()

    query = (
        '("FHIR" OR "Fast Healthcare Interoperability Resources") '
        'AND ("OMOP" OR "Observational Medical Outcomes Partnership") '
        'AND (interoperability OR ETL OR mapping OR transformation)'
    )

    results = agent.search(query, max_results=10)

    print("\n===== PUBMED SEARCH RESULTS =====\n")

    for index, article in enumerate(results, start=1):
        print(f"\nArticle {index}")
        print("Title:", article["title"])
        print("Year:", article["year"])
        print("Authors:", ", ".join(article["authors"]))
        print("Journal:", article["journal"])
        print("DOI:", article["doi"])
        print("PMID:", article["pmid"])
        print("URL:", article["url"])

    print(f"\nTotal articles retrieved: {len(results)}")
    print("\n===== PUBMED SEARCH COMPLETED =====")
