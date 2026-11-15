import requests
from urllib.parse import quote

CROSSREF_API = "https://api.crossref.org/works"
EUROPE_PMC_API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

HEADERS = {
    "User-Agent": "HealthReviewAI/1.0 (research assistant)"
}


def search_crossref(title):
    """Find publication metadata and DOI using Crossref."""

    try:
        response = requests.get(
            CROSSREF_API,
            params={"query.title": title, "rows": 5},
            headers=HEADERS,
            timeout=20
        )
        response.raise_for_status()

        items = response.json()["message"]["items"]

        if not items:
            return None

        # Select the closest title returned by Crossref.
        item = items[0]

        return {
            "title": item.get("title", [None])[0],
            "doi": item.get("DOI"),
            "year": (
                item.get("published", {})
                .get("date-parts", [[None]])[0][0]
            ),
            "authors": [
                f"{a.get('given', '')} {a.get('family', '')}".strip()
                for a in item.get("author", [])
            ],
            "publisher": item.get("publisher"),
            "source": "Crossref"
        }

    except requests.RequestException as error:
        print("Crossref error:", error)
        return None


def search_europe_pmc(title):
    """Check whether a full-text version is available in Europe PMC."""

    try:
        response = requests.get(
            EUROPE_PMC_API,
            params={
                "query": f'TITLE:"{title}"',
                "format": "json",
                "pageSize": 5
            },
            headers=HEADERS,
            timeout=20
        )
        response.raise_for_status()

        results = response.json().get("resultList", {}).get("result", [])

        if not results:
            return None

        article = results[0]

        pmcid = article.get("pmcid")
        is_open_access = article.get("isOpenAccess") == "Y"

        full_text_url = None

        if pmcid:
            full_text_url = (
                f"https://europepmc.org/articles/{pmcid}"
            )

        return {
            "pmid": article.get("pmid"),
            "pmcid": pmcid,
            "is_open_access": is_open_access,
            "full_text_url": full_text_url,
            "source": "Europe PMC"
        }

    except requests.RequestException as error:
        print("Europe PMC error:", error)
        return None


def resolve_article(title):
    """Resolve DOI and discover available full text."""

    print(f"\nSearching: {title}")

    metadata = search_crossref(title)
    full_text = search_europe_pmc(title)

    return {
        "query_title": title,
        "metadata": metadata,
        "full_text": full_text
    }


if __name__ == "__main__":
    test_title = (
        "MENDS-ON-FHIR: leveraging the OMOP common data model "
        "and FHIR standards for national chronic disease surveillance"
    )

    result = resolve_article(test_title)

    import json
    print(json.dumps(result, indent=2, ensure_ascii=False))
