# HealthReview AI
### An Agentic AI Framework for Healthcare Interoperability Literature Reviews

HealthReview AI is a research-oriented application designed to support the systematic analysis of scientific literature in healthcare interoperability. It combines AI-assisted literature screening, knowledge extraction, evidence synthesis, methodological quality assessment, and Retrieval-Augmented Generation (RAG).

The project focuses on interoperability between healthcare data standards and models, particularly **HL7 FHIR** and **OMOP Common Data Model (OMOP CDM)**.

---

## 1. Project Objectives

The main objectives are to:

- Support the screening and classification of scientific publications.
- Extract structured knowledge from selected research papers.
- Identify interoperability approaches, transformations, and data integration methods.
- Compare the evidence reported across scientific studies.
- Assess methodological quality using predefined criteria.
- Provide evidence-grounded answers through a RAG assistant.
- Generate a structured scientific literature review report.

## 2. Research Scope

The project investigates healthcare data interoperability, with particular attention to:

- HL7 FHIR (Fast Healthcare Interoperability Resources).
- OMOP Common Data Model.
- FHIR-to-OMOP and OMOP-to-FHIR transformations.
- Clinical data integration and ETL pipelines.
- Healthcare data harmonization and semantic interoperability.

**Review period:** 2014–2024.

**Current screening corpus:** 19 records.

**Included studies:** 5 publications.

The current evidence base is preliminary. Four included studies were available at abstract level, while one had full-text content available. Findings should therefore be interpreted in light of these evidence limitations.

## 3. Main Features

| Module | Description |
|---|---|
| Dashboard | Overview of the literature review and project progress |
| Screening | AI-assisted screening and human validation of publications |
| Knowledge Extraction | Structured extraction of relevant information |
| Evidence Synthesis | Identification of themes, comparisons, and research gaps |
| Quality Assessment | Assessment using eight predefined methodological criteria |
| RAG Assistant | Retrieval of relevant evidence and generation of grounded answers |
| Scientific Report | Generation of a structured literature review report |

## 4. System Architecture

The application follows a modular, agent-oriented architecture.

```text
Scientific Literature
        |
        v
Literature Search & DOI Resolution
        |
        v
Merge & Deduplication
        |
        v
AI-Assisted Screening
        |
        v
Human Validation
        |
        v
Document Processing
        |
        v
Knowledge Extraction
        |
        v
Evidence Validation & Synthesis
        |
        +----------------------+
        |                      |
        v                      v
Quality Assessment       Vector Store
                               |
                               v
                         RAG Retrieval
                               |
                               v
                         RAG Answer
                               |
                               v
                      Citation Validation
        |
        v
Scientific Report
```

The repository also includes a LangGraph workflow for coordinating selected processing and validation stages.

## 5. Technologies

The project uses the following technologies and tools:

- **Python** – Main programming language.
- **Streamlit** – Interactive research dashboard.
- **LangGraph** – Workflow orchestration.
- **LangChain** – LLM and retrieval integration.
- **ChromaDB** – Vector database for document retrieval.
- **RAG** – Evidence retrieval and grounded answer generation.
- **LLM providers** – Model integrations used by the project, depending on configuration.
- **JSON** – Structured intermediate and final research outputs.

## 6. Repository Structure

```text
HealthReview-AI/
│
├── agents/
│   ├── literature_search.py
│   ├── screening.py
│   ├── human_validation.py
│   ├── document_processor.py
│   ├── knowledge_extraction.py
│   ├── evidence_synthesis.py
│   ├── methodological_quality_agent.py
│   ├── rag_retriever.py
│   ├── rag_answer_agent.py
│   ├── citation_validator.py
│   ├── critic_agent.py
│   ├── vector_store.py
│   └── workflow_graph.py
│
├── data/
│   └── processed/
│       ├── final_screening_results.json
│       ├── extracted_knowledge.json
│       ├── evidence_synthesis.json
│       ├── methodological_quality_assessment.json
│       ├── rag_answer.json
│       └── final_report.md
│
├── app.py
├── main.py
├── planner_output.json
├── README.md
└── .gitignore
```

The repository contains selected processed research outputs. Original paper files, local vector databases, virtual environments, and API credentials are not included.

## 7. Installation and Execution

### Prerequisites

- Python 3.10 or later.
- Git.
- An environment configured with the dependencies required by the project.
- API credentials for any external LLM provider enabled in the configuration.

### Clone the repository

```bash
git clone https://github.com/nouhaila-fettahi/HealthReview-AI.git
cd HealthReview-AI
```

### Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

**Windows**
```bash
.venv\Scripts\activate
```

**Linux / macOS**
```bash
source .venv/bin/activate
```

### Install dependencies

Install the Python packages required by the project and its configured agents. Streamlit can be installed with:

```bash
pip install streamlit
```

Additional packages and provider-specific integrations must be installed according to the modules enabled in the project.

### Configure API credentials

Create a local `.env` file if required by the selected LLM integration. Add the relevant API key using the environment variable name expected by the corresponding agent.

**Important:** Never commit API keys, passwords, or other secrets to GitHub.

### Launch the dashboard

```bash
streamlit run app.py
```

## 8. Current Research Outputs

The current implementation produces structured outputs for:

- Literature screening and human review.
- DOI resolution and article metadata enrichment.
- Knowledge extraction.
- Evidence synthesis and research gap identification.
- Methodological quality assessment.
- RAG-based evidence retrieval and answer generation.
- Citation validation.
- Scientific report generation.

The current screening corpus contains 19 records, with 5 studies included in the final screening results.

The quality assessment uses eight predefined criteria. It is a project-specific appraisal framework and should not be interpreted as a validated risk-of-bias instrument.

## 9. Limitations

The current version is a research prototype. Its outputs require human verification.

Known limitations include:

- The evidence corpus is relatively small.
- Full-text availability is limited.
- LLM-generated screening, extraction, and synthesis results may contain errors.
- RAG answers depend on the coverage and quality of retrieved documents.
- The methodological assessment uses predefined project criteria rather than a validated instrument.
- The workflow does not yet represent a fully autonomous end-to-end review process.
- The preliminary screening statistics should not be interpreted as a completed PRISMA 2020 review flow.

## 10. Future Work

Potential improvements include:

- Expanding the scientific literature corpus.
- Improving full-text acquisition and document processing.
- Strengthening human-in-the-loop validation.
- Enhancing retrieval quality and citation traceability.
- Extending interoperability analysis to additional healthcare standards.
- Improving workflow orchestration and reproducibility.
- Evaluating the system against expert-reviewed reference results.

## 11. Author

**Nouhaila Fettahi**  
PhD Candidate – Healthcare Data Interoperability  
Laboratoire des Technologies Innovantes (LTI)  
ENSA Tangier, Morocco

---

*HealthReview AI is developed as a research prototype to support evidence-based analysis of healthcare interoperability literature.*
