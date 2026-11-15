# HealthReview AI - Scientific RAG Answer

**Question:** How are HL7 FHIR resources transformed into the OMOP Common Data Model?

**Evidence status:** RETRIEVED

**Direct answer**  
The retrieved scientific evidence does **not** describe a method for converting HL7 FHIR resources into the OMOP Common Data Model (CDM). All of the cited material concerns the *reverse* transformation (OMOP → FHIR) and therefore cannot be used to answer how FHIR resources are mapped into OMOP.

---

### Main findings from the available evidence
| Finding | Evidence (title, DOI, year, rank) |
|---------|-----------------------------------|
| The MENDS‑on‑FHIR project implements an **OMOP‑to‑FHIR** transformation pipeline that takes OMOP data in JSON format and produces FHIR R4 Bundle JSON. | *MENDS‑on‑FHIR: leveraging the OMOP common data model and FHIR standards for national chronic disease surveillance*, 10.1093/jamiaopen/ooae045, 2024, rank 5 |
| The transformation is performed with an open‑source **JSON‑to‑JSON engine** that executes specifications written in the functional language **Whistle**. | Same as above, rank 5 |
| Whistle files map each OMOP table/row (e.g., the PERSON table) to one or more FHIR resources (e.g., Patient), using functions that translate OMOP fields into FHIR elements and wrap the results into a FHIR Bundle. | Same as above, rank 5 |
| The pipeline is limited to the OMOP data elements required for the MENDS use case and to the US Core Implementation Guide; source codes are retained as extensions for provenance. | *MENDS‑on‑FHIR…*, 10.1093/jamiaopen/ooae045, 2024, rank 3 |
| The authors note that a CDM (OMOP) simplifies mapping **from** the CDM **into** FHIR, but they also acknowledge that the CDM may not contain all domains needed to generate certain FHIR resources. | *MENDS‑on‑FHIR…*, 10.1093/jamiaopen/ooae045, 2024, rank 1 |

All of these findings come from a **single** article (the MENDS‑on‑FHIR 2024 paper).

---

### Technical explanation (as described in the evidence)

1. **Source format** – OMOP data are exported as **OMOP JSON** (a JSON representation of the OMOP CDM tables).  
2. **Transformation engine** – An open‑source **JSON‑to‑JSON engine** runs **Whistle** transformation scripts.  
3. **Whistle specification** – Each script defines a mapping:  
   * Left‑hand side = internal variable or FHIR JSON key.  
   * Right‑hand side = OMOP field, Whistle function, or constant.  
   * Example: a PERSON record is mapped to a FHIR **Patient** resource; functions such as `USCore_Birthsex()` convert OMOP gender/sex codes to the US Core representation.  
4. **Row‑wise processing** – The engine iterates over each row in an OMOP JSON array, applying the mapping rules to generate one or more FHIR resources.  
5. **Bundling** – A terminal function aggregates the generated resources into a single **FHIR R4 Bundle** JSON document, which can then be loaded into a FHIR server.  
6. **Scope & extensions** – The transformation is limited to the OMOP elements required for the MENDS surveillance use case and follows the US Core IG; source system codes are added as FHIR extensions when allowed.

---

### Limitations of the available evidence
* **Directionality** – The evidence only covers **OMOP → FHIR** conversion; no description of **FHIR → OMOP** mapping is provided.  
* **Single source** – All details come from one 2024 article (MENDS‑on‑FHIR); no corroborating studies are available in the supplied set.  
* **Scope restriction** – The transformation is tailored to the MENDS project’s data requirements and the US Core IG, which may not generalize to other domains or to a full bidirectional mapping.  
* **Missing methodological details** – The evidence does not specify how complex FHIR resources (e.g., Observations with nested components) would be de‑normalized into OMOP tables, nor does it discuss handling of terminology mapping (e.g., SNOMED → OMOP concept IDs).

Because of these gaps, a complete answer to the research question cannot be derived from the provided material.

---

### References
1. **MENDS‑on‑FHIR: leveraging the OMOP common data model and FHIR standards for national chronic disease surveillance**. DOI: 10.1093/jamiaopen/ooae045, 2024.  
   * Rank 5 – Methods > Dataflow 2.0: OMOP JSON to FHIR R4 bundle JSON (OMOP‑to‑FHIR).  
   * Rank 3 – Discussion > Limitations and challenges (scope of OMOP‑to‑FHIR).  
   * Rank 1 – Discussion > Limitations and challenges (advantages of CDM, mapping direction).  

*All statements above are directly drawn from the cited passages; no additional information has been inferred or invented.*

## Retrieved references

- MENDS-on-FHIR: leveraging the OMOP common data model and FHIR standards for national chronic disease surveillance (2024). DOI: 10.1093/jamiaopen/ooae045. Evidence ranks: 1, 2, 3, 4, 5.