import json
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote


INPUT = Path("data/processed/merged_articles.json")
OUTPUT = Path("data/processed/enriched_articles.json")

session = requests.Session()
session.headers.update({
    "User-Agent": "HealthReviewAI/1.0 (academic research project)"
})


def fetch_pubmed_abstracts(pmids):
    """Retrieve abstracts from PubMed using PMID."""

    if not pmids:
        return {}

    response = session.get(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
        params={
            "db": "pubmed",
            "id": ",".join(pmids),
            "rettype": "abstract",
            "retmode": "xml"
        },
        timeout=60
    )
    response.raise_for_status()

    root = ET.fromstring(response.content)
    abstracts = {}

    for article in root.findall(".//PubmedArticle"):
        pmid_element = article.find(".//PMID")

        if pmid_element is None:
            continue

        pmid = pmid_element.text

        sections = article.findall(".//Abstract/AbstractText")
        parts = []

        for section in sections:
            text = "".join(section.itertext()).strip()

            if text:
                label = section.attrib.get("Label")
                parts.append(f"{label}: {text}" if label else text)

        if parts:
            abstracts[pmid] = "\n".join(parts)

    return abstracts


def reconstruct_openalex_abstract(index):
    """Reconstruct abstract from OpenAlex inverted index."""

    if not index:
        return None

    words = {}

    for word, positions in index.items():
        for position in positions:
            words[position] = word

    if not words:
        return None

    return " ".join(words[i] for i in sorted(words))


def fetch_openalex_abstract(doi):
    """Retrieve abstract using DOI from OpenAlex."""

    url = (
        "https://api.openalex.org/works/"
        + quote("https://doi.org/" + doi, safe=":/")
    )

    response = session.get(url, timeout=30)

    if response.status_code == 404:
        return None

    response.raise_for_status()

    data = response.json()

    return reconstruct_openalex_abstract(
        data.get("abstract_inverted_index")
    )


def main():

    with INPUT.open(encoding="utf-8") as file:
        data = json.load(file)

    articles = data["articles"]

    pmids = sorted({
        str(article["pmid"])
        for article in articles
        if article.get("pmid")
    })

    print("Retrieving PubMed abstracts...")
    pubmed_abstracts = fetch_pubmed_abstracts(pmids)

    stats = {
        "pubmed": 0,
        "openalex": 0,
        "missing": 0,
        "errors": []
    }

    for number, article in enumerate(articles, start=1):

        article["abstract"] = None
        article["abstract_source"] = None

        pmid = str(article.get("pmid") or "").strip()
        doi = article.get("doi")

        try:
            # Priority 1: PubMed
            if pmid and pubmed_abstracts.get(pmid):
                article["abstract"] = pubmed_abstracts[pmid]
                article["abstract_source"] = "PubMed"
                stats["pubmed"] += 1

            # Priority 2: OpenAlex
            elif doi:
                abstract = fetch_openalex_abstract(doi)

                if abstract:
                    article["abstract"] = abstract
                    article["abstract_source"] = "OpenAlex"
                    stats["openalex"] += 1
                else:
                    stats["missing"] += 1

            else:
                stats["missing"] += 1

        except requests.RequestException as error:
            stats["errors"].append({
                "title": article.get("title"),
                "error": str(error)
            })
            stats["missing"] += 1

        print(
            f"[{number}/{len(articles)}] "
            f"{article.get('title', 'Unknown title')[:65]} "
            f"-> {article['abstract_source'] or 'ABSTRACT MISSING'}"
        )

    result = {
        "total_articles": len(articles),
        "abstracts_from_pubmed": stats["pubmed"],
        "abstracts_from_openalex": stats["openalex"],
        "abstracts_missing": stats["missing"],
        "errors": stats["errors"],
        "articles": articles
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    OUTPUT.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n===== ABSTRACT ENRICHMENT COMPLETED =====")
    print("Total articles:", len(articles))
    print("PubMed abstracts:", stats["pubmed"])
    print("OpenAlex abstracts:", stats["openalex"])
    print("Missing abstracts:", stats["missing"])
    print("Saved to:", OUTPUT)


if __name__ == "__main__":
    main()
