
import json
from pathlib import Path
from collections import Counter

import streamlit as st

# =========================================================
# CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="HealthReview AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE = Path(__file__).parent
DATA = BASE / "data" / "processed"


def load_json(filename):
    path = DATA / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


screening = load_json("final_screening_results.json") or {}
knowledge = load_json("extracted_knowledge.json") or {}
synthesis_data = load_json("evidence_synthesis.json") or {}
quality = load_json("methodological_quality_assessment.json") or {}
critic = load_json("quality_report.json") or {}
rag = load_json("rag_answer.json") or {}
citation = load_json("citation_validation.json") or {}

articles = screening.get("articles", [])
extracted = knowledge.get("articles", [])
synthesis = synthesis_data.get("synthesis", {})
assessments = quality.get("assessments", [])

# =========================================================
# STYLE
# =========================================================

st.markdown("""
<style>
    .main-title {
        font-size: 2.1rem;
        font-weight: 750;
        color: #176B87;
        margin-bottom: 0;
    }
    .subtitle {
        color: #718096;
        margin-top: 5px;
        margin-bottom: 25px;
    }
    .section-title {
        color: #176B87;
        font-weight: 700;
    }
    [data-testid="stMetric"] {
        background: #F5F9FC;
        border: 1px solid #E1EAF0;
        padding: 15px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("# 🏥 HealthReview AI")
    st.caption("Agentic AI for Scientific Literature Review")
    st.divider()

    page = st.radio(
        "NAVIGATION",
        [
            "Dashboard",
            "Screening",
            "Knowledge Extraction",
            "Evidence Synthesis",
            "Quality Assessment",
            "RAG Assistant",
            "Scientific Report"
        ]
    )

    st.divider()
    st.caption("Research domain")
    st.write("Healthcare Interoperability")
    st.caption("FHIR ↔ OMOP CDM")
    st.divider()
    st.caption("HealthReview AI · Prototype")


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<p class="main-title">HealthReview AI</p>',
    unsafe_allow_html=True
)
st.markdown(
    '<p class="subtitle">An AI-assisted multi-agent platform for systematic literature reviews.</p>',
    unsafe_allow_html=True
)

# =========================================================
# DASHBOARD
# =========================================================

if page == "Dashboard":

    st.subheader("Research Overview")

    final_counts = Counter(
        a.get("final_decision", "UNKNOWN") for a in articles
    )

    total = screening.get("total_articles", len(articles))
    included = final_counts.get("INCLUDE", 0)
    excluded = final_counts.get("EXCLUDE", 0)
    uncertain = final_counts.get("UNCERTAIN", 0)

    full_text = sum(
        1 for a in extracted
        if a.get("source_type") == "FULL_TEXT"
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Screened articles", total)
    c2.metric("Included", included)
    c3.metric("Excluded", excluded)
    c4.metric("Uncertain", uncertain)

    st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("### Screening distribution")
        st.bar_chart({
            "Articles": {
                "Included": included,
                "Excluded": excluded,
                "Uncertain": uncertain
            }
        })

    with right:
        st.markdown("### Knowledge extraction")
        st.metric("Articles processed", knowledge.get("total_articles", len(extracted)))
        st.metric("Full-text sources", full_text)
        st.metric("Abstract-only sources", len(extracted) - full_text)

    st.divider()
    st.markdown("### Pipeline status")

    stages = [
        ("Article screening", bool(articles)),
        ("Knowledge extraction", bool(extracted)),
        ("Evidence synthesis", bool(synthesis)),
        ("Methodological assessment", bool(assessments)),
        ("RAG answer generation", bool(rag.get("answer"))),
        ("Citation validation", citation.get("validation_status") == "PASSED")
    ]

    for name, completed in stages:
        st.write(
            ("✅ " if completed else "⏳ ") + name
        )

    st.info(
        "The dashboard displays existing project outputs. "
        "It does not automatically rerun the agents."
    )


# =========================================================
# SCREENING
# =========================================================

elif page == "Screening":

    st.subheader("Article Screening")

    if not articles:
        st.warning("Screening results are unavailable.")
    else:
        counts = Counter(
            a.get("final_decision", "UNKNOWN") for a in articles
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Included", counts.get("INCLUDE", 0))
        c2.metric("Excluded", counts.get("EXCLUDE", 0))
        c3.metric("Uncertain", counts.get("UNCERTAIN", 0))

        decisions = ["ALL", "INCLUDE", "EXCLUDE", "UNCERTAIN"]
        selected = st.selectbox("Filter by final decision", decisions)

        filtered = [
            a for a in articles
            if selected == "ALL"
            or a.get("final_decision") == selected
        ]

        rows = []
        for a in filtered:
            rows.append({
                "Title": a.get("title", ""),
                "Year": a.get("year", ""),
                "DOI": a.get("doi", ""),
                "AI decision": a.get("decision", ""),
                "Human decision": a.get("human_decision", ""),
                "Final decision": a.get("final_decision", ""),
            })

        st.dataframe(rows, use_container_width=True, hide_index=True)

        with st.expander("Screening methodology"):
            st.write(
                "The final decisions incorporate human validation "
                "and temporal eligibility checks for the 2014–2024 period."
            )


# =========================================================
# KNOWLEDGE EXTRACTION
# =========================================================

elif page == "Knowledge Extraction":

    st.subheader("Knowledge Extraction")

    if not extracted:
        st.warning("No extraction results found.")
    else:
        st.metric("Processed articles", len(extracted))

        for i, article in enumerate(extracted, start=1):
            title = article.get("title", f"Article {i}")

            with st.expander(title):
                st.write("**Year:**", article.get("year", "Not available"))
                st.write("**DOI:**", article.get("doi", "Not available"))
                st.write("**Source:**", article.get("source_type", "Unknown"))

                extracted_knowledge = article.get("knowledge", {})

                if isinstance(extracted_knowledge, dict):
                    for key, value in extracted_knowledge.items():
                        st.markdown(f"**{key.replace('_', ' ').title()}**")
                        st.write(value)
                else:
                    st.write(extracted_knowledge)


# =========================================================
# EVIDENCE SYNTHESIS
# =========================================================

elif page == "Evidence Synthesis":

    st.subheader("Evidence Synthesis")

    if not synthesis:
        st.warning("Synthesis results are unavailable.")
    else:
        overview = synthesis.get("research_overview")
        if overview:
            st.markdown("### Research Overview")
            st.write(overview)

        st.divider()
        st.markdown("### Main Themes")

        for i, theme in enumerate(synthesis.get("main_themes", []), start=1):
            with st.expander(
                f"{i}. {theme.get('theme', 'Theme')}"
            ):
                st.write(theme.get("description", ""))
                st.write(
                    "**Supporting articles:**",
                    ", ".join(theme.get("supporting_articles", []))
                )

        st.divider()
        st.markdown("### Comparative Analysis")

        for item in synthesis.get("comparative_analysis", []):
            st.markdown(f"**{item.get('dimension', '')}**")
            st.write(item.get("observations", ""))

        st.divider()
        st.markdown("### Research Gaps")

        for gap in synthesis.get("research_gaps", []):
            st.markdown(f"**{gap.get('gap', '')}**")
            st.write(gap.get("explanation", ""))

        st.divider()
        st.markdown("### Future Research Directions")

        for direction in synthesis.get("future_research_directions", []):
            st.write(direction.get("direction", ""))

        st.divider()
        st.markdown("### Overall Conclusion")
        st.write(synthesis.get("overall_conclusion", ""))


# =========================================================
# QUALITY ASSESSMENT
# =========================================================

elif page == "Quality Assessment":

    st.subheader("Methodological Quality Assessment")

    if not assessments:
        st.warning("No methodological assessment available.")
    else:
        st.caption(
            "AI-assisted appraisal using eight project-specific criteria. "
            "This is not a validated Risk of Bias instrument."
        )

        ratings = Counter()

        for assessment in assessments:
            for criterion in assessment.get("criteria", {}).values():
                ratings[criterion.get("rating", "UNKNOWN")] += 1

        c1, c2, c3 = st.columns(3)
        c1.metric("YES", ratings.get("YES", 0))
        c2.metric("PARTIAL", ratings.get("PARTIAL", 0))
        c3.metric("UNCLEAR", ratings.get("UNCLEAR", 0))

        st.divider()

        for assessment in assessments:
            with st.expander(assessment.get("article_title", "Article")):
                criteria = assessment.get("criteria", {})

                rows = []
                for key, value in criteria.items():
                    rows.append({
                        "Criterion": key,
                        "Rating": value.get("rating", ""),
                        "Justification": value.get("justification", "")
                    })

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True
                )

                st.markdown("**Overall comment**")
                st.write(assessment.get("overall_comment", ""))

        st.divider()
        st.markdown("### Critic Agent")

        if critic:
            review = critic.get("scientific_review", {})
            st.metric(
                "LLM-generated quality score",
                f"{review.get('quality_score', 'N/A')}/100"
            )
            st.write(
                review.get("overall_assessment", "No assessment available.")
            )
        else:
            st.info("Critic report not found.")


# =========================================================
# RAG ASSISTANT
# =========================================================

elif page == "RAG Assistant":

    st.subheader("RAG Research Assistant")

    st.caption(
        "Consult the previously generated evidence-grounded answer."
    )

    answer = rag.get("answer")

    if answer:
        st.markdown(answer)
    else:
        st.warning("No RAG answer found.")

    st.divider()
    st.markdown("### Citation Validation")

    if citation:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total citations", citation.get("total_citations", 0))
        c2.metric("Valid citations", citation.get("valid_citations", 0))
        c3.metric("Invalid citations", citation.get("invalid_citations", 0))

        st.write(
            "Validation status:",
            citation.get("validation_status", "Unknown")
        )

        for item in citation.get("citation_results", []):
            st.write(item.get("title", "Unknown article"))
            st.write("DOI:", item.get("doi", ""))
            st.write("Status:", item.get("status", ""))
    else:
        st.info("Citation validation file not found.")

    st.info(
        "This initial interface displays the saved RAG result. "
        "Interactive question submission will be integrated in a later step."
    )


# =========================================================
# SCIENTIFIC REPORT
# =========================================================

elif page == "Scientific Report":

    st.subheader("Scientific Report")

    report_path = DATA / "final_report.md"

    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")
        st.markdown(report)

        st.download_button(
            "Download Scientific Report",
            data=report,
            file_name="HealthReview_AI_Final_Report.md",
            mime="text/markdown"
        )
    else:
        st.warning("Final report not found.")
