import json
import re
from pathlib import Path
from collections import defaultdict


def normalize_doi(doi):
    if not doi:
        return ""
    doi = doi.lower().strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi.rstrip(" .")


def normalize_title(title):
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return " ".join(title.split())


def load_articles(path):
    with open(path, encoding="utf-8") as file:
        return json.load(file)["articles"]


def merge_articles():
    openalex = load_articles("data/raw/openalex_results.json")
    pubmed = load_articles("data/raw/pubmed_results.json")

    all_articles = []

    for article in openalex:
        article["source"] = "OpenAlex"
        all_articles.append(article)

    for article in pubmed:
        article["source"] = "PubMed"
        all_articles.append(article)

    merged = []
    doi_index = {}
    pmid_index = {}
    title_index = {}
    duplicate_log = []

    for article in all_articles:
        doi = normalize_doi(article.get("doi"))
        pmid = str(article.get("pmid") or "").strip()
        title = normalize_title(article.get("title"))

        # Match priority: DOI, PMID, then normalized title
        existing_index = None
        match_method = None

        if doi and doi in doi_index:
            existing_index = doi_index[doi]
            match_method = "DOI"

        elif pmid and pmid in pmid_index:
            existing_index = pmid_index[pmid]
            match_method = "PMID"

        elif title and title in title_index:
            existing_index = title_index[title]
            match_method = "TITLE"

        if existing_index is not None:
            existing = merged[existing_index]

            sources = set(existing["sources"])
            sources.add(article["source"])
            existing["sources"] = sorted(sources)

            for key in ["doi", "pmid", "year", "journal"]:
                if not existing.get(key) and article.get(key):
                    existing[key] = article[key]

            duplicate_log.append({
                "title": article.get("title"),
                "source": article["source"],
                "matched_by": match_method
            })

        else:
            normalized = {
                "title": article.get("title"),
                "year": article.get("year"),
                "authors": article.get("authors", []),
                "journal": article.get("journal"),
                "doi": doi or None,
                "pmid": pmid or None,
                "sources": [article["source"]]
            }

            index = len(merged)
            merged.append(normalized)

        # Register identifiers for future matching
        current = merged[
            existing_index if existing_index is not None else len(merged) - 1
        ]

        if doi:
            doi_index[doi] = (
                existing_index if existing_index is not None else len(merged) - 1
            )

        if pmid:
            pmid_index[pmid] = (
                existing_index if existing_index is not None else len(merged) - 1
            )

        if title:
            title_index[title] = (
                existing_index if existing_index is not None else len(merged) - 1
            )

    output = {
        "total_before_deduplication": len(all_articles),
        "total_after_deduplication": len(merged),
        "duplicates_detected": len(duplicate_log),
        "articles": merged,
        "duplicate_log": duplicate_log
    }

    Path("data/processed").mkdir(parents=True, exist_ok=True)

    output_path = Path("data/processed/merged_articles.json")
    output_path.write_text(
        json.dumps(output, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n===== MERGE AND DEDUPLICATION =====")
    print("Articles before:", len(all_articles))
    print("Articles after:", len(merged))
    print("Duplicates detected:", len(duplicate_log))
    print("Saved to:", output_path)


if __name__ == "__main__":
    merge_articles()
