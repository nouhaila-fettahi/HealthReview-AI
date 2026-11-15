import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

INPUT_DIR = Path("data/papers/xml")
MANIFEST_FILE = Path("data/processed/fulltext_manifest.json")
DOI_FILE = Path("data/processed/doi_resolution_results.json")

OUTPUT_DIR = Path("data/processed")
DOCUMENTS_FILE = OUTPUT_DIR / "extracted_documents.json"
CHUNKS_FILE = OUTPUT_DIR / "document_chunks.json"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


def local_name(tag):
    """Remove XML namespace from a tag."""
    return tag.split("}")[-1]


def clean_text(text):
    text = re.sub(r"\s+", " ", text or "")
    return text.strip()


def extract_paragraphs(section):
    """Extract paragraphs without duplicating nested sections."""
    paragraphs = []

    def walk(element):
        for child in element:
            tag = local_name(child.tag)

            if tag == "sec":
                continue

            if tag == "p":
                text = clean_text(" ".join(child.itertext()))
                if text:
                    paragraphs.append(text)
            else:
                walk(child)

    walk(section)
    return paragraphs


def extract_sections(body):
    """Extract sections recursively while preserving hierarchy."""
    sections = []

    def walk(parent, parent_title=""):
        for sec in parent:
            if local_name(sec.tag) != "sec":
                continue

            heading = next(
                (child for child in sec
                 if local_name(child.tag) == "title"),
                None
            )

            title = (
                clean_text(" ".join(heading.itertext()))
                if heading is not None
                else "Untitled section"
            )

            full_title = (
                f"{parent_title} > {title}"
                if parent_title else title
            )

            paragraphs = extract_paragraphs(sec)

            sections.append({
                "section": full_title,
                "text": "\n\n".join(paragraphs)
            })

            walk(sec, full_title)

    walk(body)
    return sections


def split_into_chunks(text):
    """Split text into overlapping character-based chunks."""
    text = clean_text(text)

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def get_article_metadata(pmcid, doi_data):
    for article in doi_data.get("articles", []):
        epmc = article.get("europe_pmc") or {}

        if epmc.get("pmcid") == pmcid:
            crossref = article.get("crossref") or {}

            return {
                "doi": crossref.get("doi"),
                "year": crossref.get("year"),
                "authors": crossref.get("authors", []),
                "publisher": crossref.get("publisher"),
                "decision": article.get("final_decision"),
            }

    return {}


def main():
    with MANIFEST_FILE.open(encoding="utf-8") as f:
        manifest = json.load(f)

    with DOI_FILE.open(encoding="utf-8") as f:
        doi_data = json.load(f)

    documents = []
    all_chunks = []

    for item in manifest:
        if item.get("status") != "DOWNLOADED":
            continue

        xml_path = Path(item["file"])

        if not xml_path.exists():
            print(f"[SKIP] Missing file: {xml_path}")
            continue

        print(f"\nProcessing: {item['title']}")

        root = ET.parse(xml_path).getroot()

        title_element = root.find(".//article-title")
        title = (
            clean_text(" ".join(title_element.itertext()))
            if title_element is not None
            else item["title"]
        )

        abstract_element = root.find(".//abstract")
        abstract = (
            clean_text(" ".join(abstract_element.itertext()))
            if abstract_element is not None
            else ""
        )

        body = next(
            (element for element in root.iter()
             if local_name(element.tag) == "body"),
            None
        )

        sections = extract_sections(body) if body is not None else []

        pmcid = item.get("pmcid")
        metadata = get_article_metadata(pmcid, doi_data)

        document = {
            "title": title,
            "pmcid": pmcid,
            "doi": metadata.get("doi"),
            "year": metadata.get("year"),
            "authors": metadata.get("authors", []),
            "decision": item.get("decision"),
            "abstract": abstract,
            "sections": sections,
        }

        documents.append(document)

        for section in sections:
            for index, chunk_text in enumerate(
                split_into_chunks(section["text"])
            ):
                all_chunks.append({
                    "chunk_id": f"{pmcid}_{len(all_chunks) + 1}",
                    "text": chunk_text,
                    "metadata": {
                        "title": title,
                        "doi": metadata.get("doi"),
                        "pmcid": pmcid,
                        "year": metadata.get("year"),
                        "decision": item.get("decision"),
                        "section": section["section"],
                        "chunk_index": index,
                        "source_file": xml_path.name,
                    }
                })

        print("Sections:", len(sections))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    DOCUMENTS_FILE.write_text(
        json.dumps(documents, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    CHUNKS_FILE.write_text(
        json.dumps(all_chunks, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n===== PROCESSING SUMMARY =====")
    print("Documents:", len(documents))
    print("Sections:", sum(len(d["sections"]) for d in documents))
    print("Chunks:", len(all_chunks))
    print("Documents saved:", DOCUMENTS_FILE)
    print("Chunks saved:", CHUNKS_FILE)


if __name__ == "__main__":
    main()
