import json
import re
import time
from pathlib import Path
from difflib import SequenceMatcher

import requests

INPUT_FILE = Path("data/processed/final_screening_results.json")
OUTPUT_FILE = Path("data/processed/doi_resolution_results.json")

CROSSREF_URL = "https://api.crossref.org/works"
EUROPE_PMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

HEADERS = {"User-Agent": "HealthReviewAI/1.0 (academic research)"}


def normalize(text):
    text = (text or "").lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def similarity(a, b):
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def crossref_search(title):
    response = requests.get(
        CROSSREF_URL,
        params={"query.title": title, "rows": 5},
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    items = response.json().get("message", {}).get("items", [])

    candidates = []
    for item in items:
        candidate_title = (item.get("title") or [None])[0]
        if not candidate_title:
            continue

        score = similarity(title, candidate_title)
        candidates.append((score, item, candidate_title))

    if not candidates:
        return None

    score, item, candidate_title = max(candidates, key=lambda x: x[0])

    if score < 0.75:
        return {
            "matched": False,
            "similarity": round(score, 3),
            "returned_title": candidate_title
        }

    date_parts = (
        item.get("published", {}).get("date-parts")
        or item.get("published-print", {}).get("date-parts")
        or [[None]]
    )

    return {
        "matched": True,
        "similarity": round(score, 3),
        "title": candidate_title,
        "doi": item.get("DOI"),
        "year": date_parts[0][0],
        "publisher": item.get("publisher"),
        "authors": [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in item.get("author", [])
        ]
    }


def europe_pmc_search(title):
    response = requests.get(
        EUROPE_PMC_URL,
        params={
            "query": f'TITLE:"{title}"',
            "format": "json",
            "pageSize": 10
        },
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    items = response.json().get("resultList", {}).get("result", [])

    candidates = []
    for item in items:
        candidate_title = item.get("title", "")
        score = similarity(title, candidate_title)

        if candidate_title:
            candidates.append((score, item, candidate_title))

    if not candidates:
        return None

    score, item, candidate_title = max(candidates, key=lambda x: x[0])

    if score < 0.75:
        return {
            "matched": False,
            "similarity": round(score, 3),
            "returned_title": candidate_title
        }

    pmcid = item.get("pmcid")
    is_oa = item.get("isOpenAccess") == "Y"

    return {
        "matched": True,
        "similarity": round(score, 3),
        "title": candidate_title,
        "pmid": item.get("pmid"),
        "pmcid": pmcid,
        "is_open_access": is_oa,
        "full_text_url": (
            f"https://europepmc.org/articles/{pmcid}"
            if pmcid else None
        )
    }


def main():
    with INPUT_FILE.open(encoding="utf-8") as f:
        data = json.load(f)

    selected = [
        article for article in data.get("articles", [])
        if article.get("final_decision") in {"INCLUDE", "UNCERTAIN"}
    ]

    results = []

    print(f"Articles selected: {len(selected)}")

    for index, article in enumerate(selected, start=1):
        title = article.get("title", "")

        print(f"\n[{index}/{len(selected)}] {title}")

        result = {
            "original_title": title,
            "final_decision": article.get("final_decision"),
            "crossref": None,
            "europe_pmc": None,
            "status": "NOT_FOUND"
        }

        try:
            result["crossref"] = crossref_search(title)
            result["europe_pmc"] = europe_pmc_search(title)

            crossref_match = (
                result["crossref"]
                and result["crossref"].get("matched")
            )
            pmc_match = (
                result["europe_pmc"]
                and result["europe_pmc"].get("matched")
            )

            if crossref_match or pmc_match:
                result["status"] = "MATCH_FOUND"

            print("Status:", result["status"])

        except requests.RequestException as error:
            result["status"] = "API_ERROR"
            result["error"] = str(error)
            print("API error:", error)

        results.append(result)
        time.sleep(0.5)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(
            {"total": len(results), "articles": results},
            f,
            indent=2,
            ensure_ascii=False
        )

    print("\n===== DOI RESOLUTION SUMMARY =====")
    print("Total:", len(results))
    print("Matches:", sum(r["status"] == "MATCH_FOUND" for r in results))
    print("Not found:", sum(r["status"] == "NOT_FOUND" for r in results))
    print("API errors:", sum(r["status"] == "API_ERROR" for r in results))
    print("Saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
