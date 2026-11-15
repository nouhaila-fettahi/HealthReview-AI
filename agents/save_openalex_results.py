import json
from datetime import datetime, timezone
from pathlib import Path
from literature_search import LiteratureSearchAgent

query = "HL7 FHIR OMOP CDM healthcare interoperability ETL pipelines"

agent = LiteratureSearchAgent()
articles = agent.search(query, max_results=10)

output = {
    "source": "OpenAlex",
    "query": query,
    "retrieved_at": datetime.now(timezone.utc).isoformat(),
    "total_results": len(articles),
    "articles": articles
}

path = Path("data/raw/openalex_results.json")
path.write_text(
    json.dumps(output, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(f"Saved {len(articles)} articles to {path}")
