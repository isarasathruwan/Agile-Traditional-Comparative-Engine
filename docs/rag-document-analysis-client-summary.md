# MethodAlign IS: Document Analysis and Delivery-Method Advisory

**Prepared for:** Client documentation  
**Report date:** 26 July 2026

## Overview

MethodAlign IS includes an optional document-analysis capability that supplements its Agile-versus-Traditional methodology assessment. It identifies directly supported project evidence from participant-provided documents, presents the evidence with traceable citations, and allows the participant to decide whether eligible evidence should be used in the assessment.

The capability is designed to improve explanation, traceability, and decision support. It does not replace participant input or make an autonomous final decision.

## Document-analysis capability

The current implementation provides an assessment-scoped retrieval-augmented generation (RAG) workflow for PDF documents containing selectable text:

1. **Consent and secure collection.** Before upload or analysis, a participant must explicitly accept Google AI processing and confirm that the document is appropriate to submit. The system accepts up to five PDF files, each below 10 MB, and rejects duplicates within the same assessment.
2. **Encrypted storage.** Original document bytes are encrypted before storage. Extracted page text, chunks, citations, and extracted facts are also encrypted at rest using authenticated encryption. Access to a draft is tied to the participant’s browser-session token; administrators have separate controlled review access.
3. **Asynchronous analysis.** When the participant selects **Analyze documents**, the uploaded set is sealed and sent to a background worker. The worker extracts selectable PDF text, divides it into bounded overlapping chunks, creates 768-dimensional semantic embeddings, and stores them in PostgreSQL with pgvector for similarity retrieval.
4. **Structured evidence extraction.** Retrieval is limited to the current assessment. A configurable Google AI generation model evaluates only retrieved source chunks against ten document-only evidence questions covering flexibility, performance, and strictness. It may also produce concise, source-addressable observations about scope, delivery constraints, dependencies, governance, and risk.
5. **Citation-backed review.** Each suggested answer is shown with its document name, page number, and supporting excerpt. The participant can confirm an eligible suggestion or omit it; free score editing is not permitted.
6. **Auditable result.** The final result retains questionnaire scores, document scores, coverage, contribution, citations, processing trace, and evidence status. Administrators can review files, evidence, and processing information within the assessment workspace.

## Decision safeguards

The document component is deliberately separate from the mandatory assessment questions so that documentary evidence remains supplementary and transparent.

- The mandatory Likert questions remain the primary source for construct measurement.
- Document evidence is evaluated through a separate optional D01–D10 instrument rather than pre-filling or replacing participant answers.
- An item can influence a result only when it has a citation, carries moderate or high confidence, and is explicitly confirmed by the participant.
- Omitted, uncited, low-confidence, or unsupported suggestions contribute **0%** to the result.
- Confirmed document evidence is coverage-capped. For each construct, its maximum contribution to the decision construct score is **25%**; partial coverage produces a proportionally smaller contribution.
- Evidence adoption, coverage, and adjustment activity are recorded separately so that the source and extent of any adjustment remain visible.

## Traditional delivery sub-category suggestions

When the main assessment outcome is **Traditional**, MethodAlign IS can generate a separate delivery-method advisory. This advisory does not reconsider the Agile-versus-Traditional decision; it helps select an appropriate Traditional sub-category for implementation.

The advisor selects one primary method from the following controlled catalogue:

| Sub-category | Typical fit |
| --- | --- |
| Waterfall | Stable requirements, fixed dependencies, and sequential milestones. |
| V-Model | High verification, validation, traceability, and assurance needs. |
| PRINCE2 | Defined governance roles, business justification, and controlled stages. |
| Stage-Gate | Investment decisions, phase approvals, and formal go/no-go controls. |
| PMBOK Predictive Governance | Baselined scope, schedule, cost, risk, and change control. |

For each applicable assessment, the advisory returns:

- one recommended sub-category and a concise rationale;
- two distinct alternatives with reasons they were considered;
- a practical three-phase rollout with actions and control artefacts;
- trade-offs and stated limitations; and
- document citations where submitted documents support a claim.

The advisory uses the existing assessment outcome, participant responses, confirmed document evidence, extracted facts, and bounded document retrieval. Where no supporting document is available, it states that limitation rather than presenting an unsupported claim as fact.

## Transparency and operational controls

- Processing states are visible to participants and administrators: secure preparation, text extraction, retrieval-index creation, evidence matching, ready, or failed.
- Each suggested answer and advisory claim can be traced to an excerpt and page reference when supporting source material is available.
- The model is instructed to use only supplied chunks, avoid unsupported inference, and return no answer when evidence is insufficient.
- The workflow is bounded to the individual assessment, uses finite chunk sizes and retrieval limits, and records processing traces and durations.
- Questionnaire and rule versions remain attached to assessment records, supporting consistent interpretation and audit of results.
- Automated tests cover consent enforcement, encryption and associated-data protection, participant access isolation, cited-evidence confirmation rules, and the coverage cap.

## Current boundaries and limitations

- The delivered pipeline supports PDFs with usable selectable text. Scanned PDFs with no selectable text are marked unsupported; OCR and image-document processing are not yet part of the delivered workflow.
- Document analysis is optional. An assessment can proceed without documentary evidence if processing fails or the participant chooses not to use it.
- RAG output is evidence support, not proof of project truth. Its usefulness depends on the quality, completeness, and currency of the submitted documents.
- Human confirmation is required before eligible document evidence can affect an assessment. The feature does not independently make a final methodology recommendation.
- The core decision-support model remains a rule-based Agile-versus-Traditional comparison. Document analysis and sub-category suggestions enrich the evidence trail and delivery planning without replacing that primary outcome.
