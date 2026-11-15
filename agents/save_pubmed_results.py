import json
from datetime import datetime, timezone
from pathlib import Path
from pubmed_search import PubMedSearchAgent

query = (
    '("FHIR" OR "Fast Healthcare Interoperability Resources") '
    'AND ("OMOP" OR "Observational Medical Outcomes Partnership") '
    'AND (interoperability OR ETL OR mapping OR transformation)'
)

agent = PubMedSearchAgent()
articles = agent.search(query, max_results=10)

output = {
    "source": "PubMed",
    "query": query,
    "retrieved_at": datetime.now(timezone.utc).isoformat(),
    "total_results": len(articles),
    "articles": articles
}

path = Path("data/raw/pubmed_results.json")
path.write_text(
    json.dumps(output, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print(f"Saved {len(articles)} articles to {path}")
