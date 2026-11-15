# HealthReview AI: An Agentic AI-Assisted Pipeline for Systematic Literature Review in Healthcare Data Interoperability

## Abstract

Systematic literature reviews in healthcare interoperability require the identification, screening, extraction, appraisal, and synthesis of scientific evidence from heterogeneous publications. These activities are time-consuming and require methodological consistency and traceability. This project presents HealthReview AI, an AI-assisted multi-agent pipeline designed to support the systematic review process in the field of healthcare data interoperability, with a particular focus on HL7 Fast Healthcare Interoperability Resources (FHIR) and the Observational Medical Outcomes Partnership Common Data Model (OMOP CDM).

The prototype combines specialized agents for literature search and screening, knowledge extraction, evidence synthesis, methodological quality assessment, and quality assurance. A LangGraph-based workflow coordinates the processing of existing research outputs, while a Retrieval-Augmented Generation (RAG) component uses a ChromaDB vector store to retrieve scientific evidence and generate source-grounded answers with citation validation.

The experimental corpus contains 19 screened records, from which five studies were finally included, ten excluded, and four classified as uncertain. The five included studies were processed for knowledge extraction and evidence synthesis. Methodological assessment was conducted using eight predefined criteria. RAG evaluation demonstrated the importance of retrieval-grounded responses: the system correctly identified that the retrieved evidence from the MENDS-on-FHIR study described OMOP-to-FHIR transformation rather than the reverse direction.

The results demonstrate the feasibility of combining agent-based processing, evidence retrieval, and automated quality checks to support literature review activities. However, the prototype remains an AI-assisted research tool rather than a fully autonomous systematic review system. Limitations include restricted full-text availability, preliminary screening statistics, and the need for further validation of methodological assessments and workflow automation.

**Keywords:** Agentic AI, Systematic Literature Review, Healthcare Interoperability, HL7 FHIR, OMOP CDM, LangGraph, Retrieval-Augmented Generation, Multi-Agent Systems.

---

## 1. Introduction

### 1.1 Background

Healthcare interoperability is essential for enabling the exchange, integration, and reuse of clinical information across heterogeneous healthcare information systems. Different standards and data models have been developed to address this challenge.

HL7 Fast Healthcare Interoperability Resources (FHIR) provides standardized resources and interfaces for exchanging healthcare information. In contrast, the Observational Medical Outcomes Partnership Common Data Model (OMOP CDM) provides a standardized structure for organizing observational healthcare data and supporting large-scale clinical research.

Integrating these standards requires appropriate data transformation, semantic mapping, terminology alignment, and validation mechanisms. These topics have generated increasing scientific interest, particularly in relation to ETL pipelines connecting healthcare information systems.

At the same time, reviewing the scientific literature in this domain involves several complex activities, including searching publications, evaluating relevance, extracting technical information, comparing methodologies, and identifying research gaps.

Recent advances in Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), and multi-agent systems offer opportunities to assist researchers in these activities.

### 1.2 Problem Statement

Traditional literature review processes require substantial manual effort. Researchers must repeatedly examine publications, identify relevant information, compare technical approaches, and ensure that conclusions remain supported by the available evidence.

Although LLMs can assist with these tasks, generating answers without controlled retrieval and validation introduces risks such as hallucinations, incorrect citations, and unsupported conclusions.

Therefore, the main problem addressed by this project is:

How can an AI-assisted multi-agent system support the systematic literature review process while maintaining evidence traceability, methodological transparency, and human oversight?

### 1.3 Objectives

The main objective is to design and implement HealthReview AI, an agent-based pipeline supporting scientific literature review activities.

The specific objectives are:

- Automate and assist the processing of scientific literature.
- Support article screening using predefined inclusion and exclusion criteria.
- Extract structured knowledge from selected publications.
- Generate comparative evidence synthesis.
- Assist methodological quality assessment.
- Retrieve relevant scientific passages using RAG.
- Validate citations and improve the reliability of generated answers.
- Maintain traceability of intermediate results and processing stages.

---

## 2. System Architecture and Technologies

### 2.1 Architectural Overview

HealthReview AI follows a modular multi-agent architecture in which specialized components perform distinct literature review tasks.

The main components include:

1. **Coordinator and Workflow Manager:** Coordinates processing stages and manages the workflow state.
2. **Search and Retrieval Components:** Support the collection and retrieval of scientific publications and relevant evidence.
3. **Screening Agent:** Evaluates publication relevance using predefined eligibility criteria.
4. **Knowledge Extraction Agent:** Extracts structured information from selected publications.
5. **Evidence Synthesis Agent:** Organizes findings into themes, comparative dimensions, and research gaps.
6. **Methodological Quality Assessment Agent:** Evaluates the methodological reporting of selected studies.
7. **RAG Component:** Retrieves relevant passages from the indexed scientific corpus and generates evidence-grounded answers.
8. **Critic / Quality Assurance Agent:** Reviews the generated synthesis and identifies potential structural or scientific issues.

Human validation is incorporated into the screening and methodological assessment processes.

### 2.2 Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| LLM | openai/gpt-oss-120b |
| LLM access | Groq |
| Workflow orchestration | LangGraph |
| Embedding model | sentence-transformers/all-MiniLM-L6-v2 |
| Vector database | ChromaDB |
| Retrieval | Similarity-based vector retrieval |
| Document processing | Python document-processing components |
| Data storage | JSON and Markdown |
| Development environment | GitHub Codespaces |

### 2.3 LangGraph Workflow

The implemented LangGraph workflow processes existing outputs through the following sequence:

`load_results → validate_results → prisma_statistics → rag_retrieval → rag_answer → citation_validation → methodological_quality → finish`

Conditional execution is used for the preliminary PRISMA statistics stage.

The workflow maintains a shared state containing information such as:

- Research topic and research question.
- Screening results.
- Extracted knowledge.
- Evidence synthesis.
- Quality reports.
- Preliminary PRISMA statistics.
- Retrieved RAG evidence.
- Generated RAG answers.
- Citation validation results.
- Methodological assessment.
- Processing errors and workflow status.

The implemented graph primarily coordinates and validates previously generated outputs. It should therefore be distinguished from a fully autonomous end-to-end workflow that independently performs every literature review stage.

---

## 3. Research Methodology

### 3.1 Research Topic and Scope

The experimental application focuses on healthcare data interoperability, particularly the integration of HL7 FHIR and OMOP CDM.

The main review scope is the transformation direction:

**FHIR → OMOP CDM**

Studies addressing the reverse direction, OMOP → FHIR, are retained as complementary evidence but are distinguished from studies directly addressing the main research scope.

### 3.2 Screening Process

The screening process uses predefined inclusion and exclusion criteria.

The inclusion criteria cover:

- Scientific journal articles, conference papers, and technical reports.
- Publications within the period 2014–2024.
- English-language publications.
- Studies describing, implementing, or evaluating ETL processes connecting FHIR and OMOP CDM.
- Studies discussing semantic mapping, terminology alignment, or data provenance.

The screening process combines an initial AI decision with human validation and a subsequent temporal eligibility check.

The final dataset contains 19 records.

### 3.3 Knowledge Extraction

The Knowledge Extraction Agent processes the five finally included studies and extracts structured information, including:

- Research objectives.
- Standards and technologies.
- ETL architecture.
- Mapping techniques.
- Data sources and datasets.
- Evaluation methods.
- Main findings.
- Limitations.
- Future research directions.
- Supporting evidence.

The extraction stage processed five articles without reported extraction errors.

### 3.4 Evidence Synthesis

The Evidence Synthesis Agent organizes the extracted knowledge into six main themes:

1. FHIR as an intermediate representation for OMOP integration.
2. Direct mapping of source data to OMOP without FHIR.
3. Virtual clinical knowledge-graph generation from OMOP via Ontop.
4. Multi-standard mapping across openEHR, FHIR, and OMOP.
5. XSLT-based transformation from HL7 FHIR Bundles to OMOP.
6. JSON-to-JSON transformation using Whistle from OMOP to FHIR.

The synthesis also compares standard utilization, ETL architecture patterns, mapping techniques, data coverage, and evaluation methods.

### 3.5 Methodological Quality Assessment

An AI-assisted assessment was performed on all five included studies using eight custom criteria:

| ID | Criterion |
|---|---|
| C1 | Clarity of research objectives |
| C2 | Description of data sources and provenance |
| C3 | Representativeness of the data |
| C4 | Clarity of mapping or transformation methodology |
| C5 | Validation of the proposed method or system |
| C6 | Use of evaluation metrics |
| C7 | Reproducibility |
| C8 | Discussion of methodological limitations |

Each criterion is evaluated using three possible ratings: YES, PARTIAL, and UNCLEAR.

These criteria constitute a project-specific appraisal framework. They are not a validated formal Risk of Bias instrument.

Human review is required to verify the AI-generated assessments.

### 3.6 Retrieval-Augmented Generation

The RAG component uses ChromaDB to index scientific document chunks and retrieve relevant passages.

The vector store contains 141 chunks in the `healthreview_articles` collection.

The retrieval process consists of:

1. Receiving a research question.
2. Generating an embedding for the query.
3. Retrieving relevant passages from ChromaDB.
4. Providing retrieved evidence to the LLM.
5. Generating an answer grounded in the retrieved passages.
6. Validating the citations associated with the generated answer.

Citation validation checks the consistency of citation metadata, including the article title, DOI, publication year, and retrieved passage ranks.

---

## 4. Experimental Setup

### 4.1 Corpus Characteristics

The experimental corpus contains 19 screened scientific records.

Five studies were finally included in the analysis. Of these five studies, one was available as full text in the indexed corpus, while four were represented by abstracts only.

This difference in source availability is important because the depth of extraction and evidence retrieval depends on the available publication content.

### 4.2 Initial and Human Screening Results

The screening process produced the following results:

| Decision | Initial AI screening | Human validation | Final decision |
|---|---:|---:|---:|
| INCLUDE | 9 | 5 | 5 |
| EXCLUDE | 5 | 8 | 10 |
| UNCERTAIN | 5 | 6 | 4 |
| **Total** | **19** | **19** | **19** |

The final decision counts incorporate the temporal eligibility check. Two initially uncertain records were subsequently excluded because their publication year was 2025, outside the predefined 2014–2024 period.

The four remaining uncertain records are not counted as excluded.

These statistics describe the available screening dataset. They should not be interpreted as a complete PRISMA 2020 flow diagram because all identification, deduplication, and full-text eligibility counts have not been established as a complete flow.

### 4.3 Included Studies

The five included publications are:

| ID | Publication | Year | DOI |
|---|---|---:|---|
| A1 | Towards the Representation of Genomic Data in HL7 FHIR and OMOP CDM | 2021 | 10.3233/shti210545 |
| A2 | FHIR-Ontop-OMOP: Building clinical knowledge graphs in FHIR RDF with the OMOP Common Data Model | 2022 | 10.1016/j.jbi.2022.104201 |
| A3 | From OpenEHR to FHIR and OMOP Data Model for Microbiology Findings | 2021 | 10.3233/shti210189 |
| A4 | Data Integration into OMOP CDM for Heterogeneous Clinical Data Collections via HL7 FHIR Bundles and XSLT | 2020 | 10.3233/shti200138 |
| A5 | MENDS-on-FHIR: leveraging the OMOP common data model and FHIR standards for national chronic disease surveillance | 2024 | 10.1093/jamiaopen/ooae045 |

### 4.4 Directionality of Interoperability

An important distinction emerged during the comparative analysis.

| Article | Transformation direction | Relevance |
|---|---|---|
| A1 | VCF → FHIR → OMOP, with direct VCF → OMOP mapping | Directly relevant |
| A2 | OMOP → FHIR RDF through Ontop | Complementary |
| A3 | openEHR → FHIR → OMOP | Directly relevant |
| A4 | FHIR Bundles → XSLT → OMOP | Directly relevant |
| A5 | OMOP JSON → Whistle → FHIR R4 Bundles | Complementary |

Consequently, three studies provide direct evidence concerning the FHIR-to-OMOP direction, while two studies describe the reverse direction.

This distinction is essential for avoiding incorrect generalizations about the capabilities and directionality of the studied pipelines.

---

## 5. Results and Analysis

### 5.1 Screening Performance

The initial AI screening classified nine records as INCLUDE, five as EXCLUDE, and five as UNCERTAIN.

Human validation produced five INCLUDE, eight EXCLUDE, and six UNCERTAIN decisions.

After applying the final temporal eligibility criterion, the dataset contained five included studies, ten excluded studies, and four uncertain studies.

The difference between initial AI decisions and final decisions highlights the importance of human oversight and explicit eligibility checks.

### 5.2 Knowledge Extraction Results

The Knowledge Extraction Agent successfully processed all five included publications.

| Source type | Number of articles |
|---|---:|
| Full text | 1 |
| Abstract only | 4 |
| **Total** | **5** |

No extraction errors were reported.

Nevertheless, extraction completeness varies according to the available source material. In particular, limitations, implementation details, and reproducibility information were not consistently available in the abstracts.

### 5.3 Comparative Analysis of ETL Approaches

The five studies illustrate different approaches to healthcare data transformation.

**A1 – Genomic Data Integration**

The study investigates semantic mapping between genomic data, HL7 FHIR, and OMOP CDM. It reports direct mapping from VCF files to OMOP with coverage slightly above 50%. It also reports that using FHIR as an intermediate representation does not introduce further information loss, with a transformation success rate close to 100%.

**A2 – FHIR-Ontop-OMOP**

This study uses Ontop to map relational OMOP tables into FHIR RDF representations, enabling virtual clinical knowledge-graph generation and SPARQL querying. It represents the OMOP-to-FHIR direction and is therefore complementary to the main review scope.

**A3 – openEHR, FHIR, and OMOP**

This study describes a multi-standard transformation workflow for microbiology findings, connecting openEHR, FHIR, and OMOP CDM. Its FHIR-to-OMOP stage is directly relevant to the review.

**A4 – FHIR Bundles and XSLT**

This approach transforms FHIR Bundles into OMOP CDM using XSLT. The study also discusses terminology mapping involving LOINC and SNOMED CT.

**A5 – MENDS-on-FHIR**

This study describes an OMOP-to-FHIR pipeline for chronic disease surveillance. SQL queries generate OMOP JSON objects, which are transformed into FHIR R4 Bundles using the Whistle engine before validation and loading.

The five approaches demonstrate the diversity of technical solutions used to connect healthcare data standards. However, they do not all address the same transformation direction or application context.

### 5.4 Research Gaps

Three main research gaps emerged from the evidence synthesis.

**Gap 1: Limited performance and scalability evaluation**

The reviewed studies focus primarily on mapping coverage, data consistency, conformance, or qualitative feasibility. Systematic reporting of runtime, memory consumption, and scalability remains limited.

**Gap 2: Limited evaluation of downstream clinical and analytical impact**

The studies mainly demonstrate technical feasibility. Their impact on clinical decision support, research reproducibility, and patient outcomes remains insufficiently evaluated.

**Gap 3: Insufficient semantic validation**

Validation approaches often rely on coverage percentages, patient-count equivalence, or conformance checks. More comprehensive concept-level semantic equivalence assessments are needed.

---

## 6. Methodological Quality Assessment Results

All five included studies were assessed using the eight project-specific criteria.

The aggregate ratings are presented below.

| Criterion | YES | PARTIAL | UNCLEAR |
|---|---:|---:|---:|
| C1 – Objectives | 5 | 0 | 0 |
| C2 – Data provenance | 2 | 3 | 0 |
| C3 – Representativeness | 0 | 0 | 5 |
| C4 – Mapping methodology | 1 | 4 | 0 |
| C5 – Validation | 2 | 2 | 1 |
| C6 – Evaluation metrics | 3 | 1 | 1 |
| C7 – Reproducibility | 0 | 0 | 5 |
| C8 – Limitations | 0 | 0 | 5 |

The assessment indicates that research objectives are generally clearly reported. However, information regarding representativeness, reproducibility, and methodological limitations is insufficient in the available source material.

The results should be interpreted cautiously. Four publications were assessed using abstracts only, which restricts the available evidence. The ratings are AI-assisted and require expert interpretation; they do not constitute a validated risk-of-bias evaluation.

---

## 7. RAG Evaluation and Citation Validation

### 7.1 Retrieval Configuration

The RAG component uses the `healthreview_articles` ChromaDB collection, containing 141 document chunks.

The embedding model used for indexing is `sentence-transformers/all-MiniLM-L6-v2`.

A test query was formulated:

"How are HL7 FHIR resources transformed into the OMOP Common Data Model?"

The retrieval process returned five passages.

### 7.2 Retrieval Findings

All five retrieved passages came from the MENDS-on-FHIR publication.

The retrieved evidence described the reverse transformation direction:

**OMOP → FHIR**

The RAG answer generator correctly identified that the retrieved passages did not provide evidence about FHIR-to-OMOP transformation.

Instead of inventing an unsupported transformation methodology, the system explicitly indicated that the available evidence was insufficient to answer the question in the requested direction.

This result demonstrates the importance of evidence-grounded generation and directionality awareness.

However, retrieval diversity remains limited because all retrieved passages originated from a single publication.

### 7.3 Citation Validation

The citation validation component produced the following results:

| Metric | Result |
|---|---:|
| Total citations | 1 |
| Valid citations | 1 |
| Invalid citations | 0 |
| Validation status | PASSED |

The citation was validated against the MENDS-on-FHIR publication metadata and the retrieved passage ranks.

This confirms that the tested citation passed the implemented validation checks. It does not establish the correctness of every scientific claim in the generated answer.

---

## 8. Critic Agent and Quality Assurance

The Critic / Quality Assurance Agent reviewed the evidence synthesis for structural and scientific consistency.

The generated quality report contained:

| Metric | Result |
|---|---:|
| Articles reviewed | 5 |
| Structural issues | 0 |
| Generalization warnings | 0 |
| LLM-generated quality score | 92/100 |

The Critic Agent marked all six synthesis themes, four comparative dimensions, and three research gaps as supported by the extracted evidence.

Its recommendations focused on:

- Systematic performance benchmarking.
- Evaluation of downstream analytical and clinical impact.
- More rigorous semantic validation.

The score of 92/100 is an LLM-generated assessment and has not been independently validated. It should therefore be interpreted as an automated quality indicator rather than an objective scientific quality measure.

---

## 9. Discussion

### 9.1 Contributions

HealthReview AI demonstrates how specialized AI components can support different activities in the systematic literature review process.

The prototype combines screening, structured knowledge extraction, comparative synthesis, methodological appraisal, evidence retrieval, citation validation, and quality assurance.

The separation of these tasks into specialized components improves modularity and makes intermediate results easier to inspect.

The RAG experiment also demonstrates an important reliability behavior: the system can recognize when retrieved evidence does not support the requested transformation direction instead of generating an unsupported answer.

### 9.2 Limitations

Several limitations must be considered.

**Corpus limitations:** The experimental dataset contains only 19 screened records and five finally included publications. The findings should not be generalized to the entire healthcare interoperability literature.

**Full-text availability:** Only one of the five included studies was available as full text in the indexed corpus. Four studies were represented by abstracts, restricting extraction depth and methodological assessment.

**Screening validation:** The final dataset retains four uncertain records. The reported screening statistics represent the available project dataset rather than a fully documented PRISMA 2020 flow.

**Methodological appraisal:** The eight criteria are project-specific and AI-assisted. They do not replace validated appraisal instruments or independent expert assessment.

**RAG retrieval limitations:** The tested query returned five passages from a single publication. This limits retrieval diversity and the breadth of evidence available for answering research questions.

**Workflow automation:** The current LangGraph workflow coordinates and validates existing outputs. It does not yet represent a fully autonomous end-to-end literature review process.

**Evaluation limitations:** The quality score and methodological assessments are generated by an LLM and require further independent evaluation.

### 9.3 Future Improvements

Future development should prioritize:

1. Completing an end-to-end LangGraph workflow integrating the search, screening, extraction, synthesis, and quality assurance stages.
2. Expanding the scientific corpus and improving full-text availability.
3. Improving RAG retrieval diversity and evaluating retrieval quality using multiple research questions.
4. Introducing human-in-the-loop validation at critical methodological decision points.
5. Integrating validated methodological appraisal frameworks where appropriate.
6. Developing a complete and auditable PRISMA 2020 flow.
7. Evaluating the system using measurable criteria such as screening agreement, extraction accuracy, retrieval relevance, citation precision, and processing time.
8. Developing a simple user interface to facilitate interaction with the pipeline and visualization of its outputs.

---

## 10. Conclusion

This project presented HealthReview AI, an AI-assisted multi-agent pipeline designed to support systematic literature review activities in healthcare data interoperability.

The prototype integrates specialized processing components for screening, knowledge extraction, evidence synthesis, methodological quality assessment, RAG-based evidence retrieval, citation validation, and automated quality assurance.

Its application to a review corpus involving HL7 FHIR and OMOP CDM produced five finally included studies from 19 screened records. The analysis identified different ETL strategies, highlighted the distinction between FHIR-to-OMOP and OMOP-to-FHIR transformations, and revealed important research gaps related to scalability, semantic validation, and downstream clinical impact.

The RAG experiment demonstrated the value of grounding generated answers in retrieved scientific passages and explicitly recognizing insufficient evidence. At the same time, the limited availability of full-text publications and the restricted retrieval diversity illustrate areas requiring improvement.

Overall, HealthReview AI provides a functional foundation for AI-assisted scientific literature review. Further development, larger-scale experimentation, independent validation, and stronger human oversight are required before it can be considered a fully autonomous and methodologically validated systematic review platform.

---

## References

1. Towards the Representation of Genomic Data in HL7 FHIR and OMOP CDM. 2021. https://doi.org/10.3233/shti210545

2. FHIR-Ontop-OMOP: Building clinical knowledge graphs in FHIR RDF with the OMOP Common Data Model. 2022. https://doi.org/10.1016/j.jbi.2022.104201

3. From OpenEHR to FHIR and OMOP Data Model for Microbiology Findings. 2021. https://doi.org/10.3233/shti210189

4. Data Integration into OMOP CDM for Heterogeneous Clinical Data Collections via HL7 FHIR Bundles and XSLT. 2020. https://doi.org/10.3233/shti200138

5. MENDS-on-FHIR: leveraging the OMOP common data model and FHIR standards for national chronic disease surveillance. 2024. https://doi.org/10.1093/jamiaopen/ooae045