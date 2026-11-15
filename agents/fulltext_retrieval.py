import json
import re
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

INPUT_FILE = Path("data/processed/doi_resolution_results.json")
OUTPUT_DIR = Path("data/papers/xml")
MANIFEST_FILE = Path("data/processed/fulltext_manifest.json")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)


def safe_filename(title):
    name = re.sub(r"[^a-zA-Z0-9]+", "_", title or "article")
    return name.strip("_")[:90] or "article"


def article_key(record):
    return (
        record.get("pmcid")
        or record.get("doi")
        or record.get("title")
        or record.get("original_title")
    )


# HTTP session with automatic retries
session = requests.Session()

retry_strategy = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    raise_on_status=False,
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)

session.headers.update({
    "User-Agent": "HealthReviewAI/1.0 (academic research)"
})


with INPUT_FILE.open(encoding="utf-8") as f:
    data = json.load(f)

# Preserve previous results
if MANIFEST_FILE.exists():
    with MANIFEST_FILE.open(encoding="utf-8") as f:
        old_manifest = json.load(f)
else:
    old_manifest = []

manifest_by_key = {
    article_key(item): item
    for item in old_manifest
    if article_key(item)
}

processed = []

for index, article in enumerate(data.get("articles", []), 1):

    decision = article.get("final_decision", "UNCERTAIN")

    if decision not in ("INCLUDE", "UNCERTAIN"):
        continue

    epmc = article.get("europe_pmc") or {}
    pmcid = epmc.get("pmcid")
    is_open = epmc.get("is_open_access", False)

    title = article.get("original_title") or article.get("title") or f"Article_{index}"
    key = article_key({
        "pmcid": pmcid,
        "doi": article.get("doi"),
        "title": title
    })

    previous = manifest_by_key.get(key, {})

    record = {
        **previous,
        "title": title,
        "decision": decision,
        "pmcid": pmcid,
    }

    # Keep previously downloaded valid files
    previous_file = record.get("file")

    if (
        record.get("status") == "DOWNLOADED"
        and previous_file
        and Path(previous_file).exists()
        and Path(previous_file).stat().st_size > 0
    ):
        print(f"[SKIP] Already downloaded: {title}")
        processed.append(record)
        continue

    if not pmcid or not is_open:
        record.update({
            "status": "NO_OPEN_FULL_TEXT",
            "file": None,
            "error": None,
        })
        processed.append(record)
        print(f"[SKIP] No open full text: {title}")
        continue

    url = (
        "https://www.ebi.ac.uk/europepmc/"
        f"webservices/rest/{pmcid}/fullTextXML"
    )

    output_path = OUTPUT_DIR / (safe_filename(title) + ".xml")

    try:
        print(f"\n[{index}] Downloading: {title}")

        response = session.get(url, timeout=60)
        response.raise_for_status()

        content = response.content

        if not content.strip().startswith(b"<"):
            raise ValueError("Response is not XML")

        # Save only after successful validation
        output_path.write_bytes(content)

        record.update({
            "status": "DOWNLOADED",
            "file": str(output_path),
            "error": None,
        })

        print("[OK] Download completed")

    except (requests.RequestException, ValueError) as exc:

        record.update({
            "status": "ERROR",
            "file": None,
            "error": str(exc),
        })

        print(f"[ERROR] {title}: {exc}")

    processed.append(record)
    time.sleep(0.5)


# Keep previous manifest records not present in this input
processed_keys = {article_key(item) for item in processed}

for item in old_manifest:
    key = article_key(item)
    if key and key not in processed_keys:
        processed.append(item)

with MANIFEST_FILE.open("w", encoding="utf-8") as f:
    json.dump(processed, f, indent=2, ensure_ascii=False)

print("\n===== FULL TEXT RETRIEVAL SUMMARY =====")
print("Candidates:", len(processed))
print("Downloaded:", sum(x.get("status") == "DOWNLOADED" for x in processed))
print("Unavailable:", sum(x.get("status") == "NO_OPEN_FULL_TEXT" for x in processed))
print("Errors:", sum(x.get("status") == "ERROR" for x in processed))
print("Manifest:", MANIFEST_FILE)
