# Client Handover and Research Finalization Plan

**Project:** MethodAlign IS  
**Final decision classes:** Agile or Traditional  
**Recommended release position:** Explainable undergraduate research prototype and decision-support application

## 1. Finalization decision

Finalize and hand over the stable **survey-informed Version 2** questionnaire and rule configuration. Present it as a configurable decision-support prototype informed by literature and exploratory survey evidence—not as a statistically proven predictor of project success.

Version 2 contains 12 scored questions, survey effect-size construct weights of 1.37/0.64/0.99, survey-derived Agile/Traditional reference centroids, weighted-range normalization, and no hard strictness override. It is activated automatically through versioned migrations. It remains provisional until expert content validation, cognitive interviews, a pilot, and prospective evaluation are completed.

This approach produces a complete, honest deliverable now while preserving a defensible future validation path.

## 2. What is being handed over

### 2.1 Application package

- deployable frontend, backend, database migrations, and container configuration;
- public Agile/Traditional assessment workflow;
- versioned questionnaire and deterministic scoring configuration;
- decision report with scores, drivers, risks, and next-step advice;
- administrator dashboard and assessment traceability;
- optional document-evidence workflow, with its limits documented;
- source code, deployment instructions, configuration template, and test evidence;
- administrator and operational documentation;
- known limitations and Version 2 backlog.

### 2.2 Research package

- final undergraduate thesis/report;
- raw survey exported from Google Forms;
- duplicate-screened analysis dataset with source-row traceability;
- documented cleaning/exclusion log;
- original questionnaire and variable-coding table;
- descriptive, reliability, comparative, and qualitative results;
- explicit separation between exploratory evidence and model validation;
- system-question-to-research-factor mapping;
- proposed Version 2 questionnaire;
- testing evidence, screenshots, and appendices.

## 3. Version 2 research claim

Use the following wording consistently in the application documentation, thesis, demonstration, and client handover:

> MethodAlign IS is an explainable, rule-based decision-support prototype that compares an information systems project's reported characteristics with configured Agile and Traditional reference profiles. The rules are informed by literature, practitioner survey findings, and transparent expert assumptions. The output supports human decision-making and does not guarantee project success or replace professional judgment.

Do not call Version 2 an “AI predictor,” “validated methodology classifier,” or “90.1% accurate methodology selector.”

## 4. Scope freeze

### Included in Version 2

- exactly two final recommendation classes: Agile and Traditional;
- the 12-item anchored mandatory questionnaire;
- explainable construct scores and deterministic rules;
- questionnaire and rule version history;
- assessment export and research summaries;
- optional document evidence as supplemental, traceable evidence;
- Traditional sub-category advice where already implemented;
- documented limitations and manual-review guidance for close results.

### Deferred validation and future work

- further weight or threshold fitting beyond the equal-weight centroid model;
- expert-consensus ground-truth labels;
- external validation on unseen project cases;
- treating Hybrid as a recommendation class;
- claims that a methodology recommendation predicts project success;
- further major features unrelated to acceptance or defect correction.

## 5. Application completion gates

The application is handover-ready only when every critical gate passes.

| Gate | Required evidence | Pass condition |
| --- | --- | --- |
| Backend correctness | Automated test output | All backend tests pass with no unexpected skips/failures. |
| Frontend quality | Lint and production-build output | `npm run lint` and `npm run build` pass. |
| Container deployment | Clean Docker build/start log | Full stack starts from documented commands without manual code changes. |
| Database readiness | Migration output | A new database upgrades to the latest migration successfully. |
| Core assessment | Manual acceptance record | A participant can complete the assessment and receive an Agile or Traditional report. |
| Rule traceability | Admin inspection | Result retains questionnaire version, rule version, inputs, scores, and rationale. |
| Admin workflow | Manual acceptance record | Login, search, view, export, questionnaire/rule viewing, and permissions work. |
| Document workflow | Manual acceptance record | Consent, upload, analysis/skip/failure, citations, and evidence cap behave as documented. |
| Security configuration | Handover checklist | Default credentials and secrets are replaced; production origins and storage are configured. |
| Backup/recovery | Restore rehearsal | Database and uploaded-document backup/restore procedure is documented and tested. |
| Documentation | Client review | Deployment, administration, rules, questionnaire, limitations, and known issues are understandable. |

## 6. Minimum manual acceptance scenarios

1. Submit a high-change, feedback-ready project and verify an Agile recommendation and explanation.
2. Submit a fixed-scope, regulated, approval-heavy project and verify a Traditional recommendation and explanation.
3. Submit a close/borderline case and verify the close-decision warning and trade-off explanation.
4. Verify that invalid profile and Likert inputs cannot be submitted.
5. Verify that an historical result still shows the questionnaire and rule versions used at submission.
6. Save or activate a new configuration and confirm that earlier results do not change.
7. Export assessments and confirm column meanings and data completeness.
8. Exercise document consent, upload, analysis, confirmation, omission, and processing-failure paths.
9. Confirm unauthorized users cannot access administrator or another participant's documents.
10. Deploy from a clean environment using only the handover instructions.

## 7. Research-report completion gates

| Chapter/output | Completion condition |
| --- | --- |
| Chapter 1 | Problem, gap, one main research question, aim, four objectives, scope, and proposed workflow agree with each other. |
| Chapter 2 | Recent literature supports each construct and explains why existing selection approaches are insufficient. |
| Chapter 3 | Sampling, instrument, ethics, collection, cleaning, coding, statistical methods, design-science workflow, and limitations are reproducible. |
| Chapter 4 | Survey/literature factors map directly to system requirements, use cases, architecture, and questionnaire fields. |
| Chapter 5 | The contribution-specific implementation—versioning, scoring, explanation, evidence traceability—is explained with diagrams and selected evidence. |
| Chapter 6 | Functional/non-functional tests, survey results, preliminary engine agreement, sensitivity analysis, usability evidence, and limitations are reported numerically. |
| Conclusion | Each objective is answered using evidence already presented; limitations and Version 2 validation are explicit. |
| Appendices | Instruments, coding table, cleaned-data log, detailed test cases, screenshots, and supporting outputs are attached. |

## 8. How the current survey should appear in the final report

Use the duplicate-screened `n = 107` analysis as primary and the raw `n = 111` analysis as a sensitivity check.

Report that:

- requirements change and flexibility show the strongest Agile-oriented separation;
- documentation, security, risk, size, and governance-related conditions show Traditional-oriented separation;
- Hybrid cases occupy an intermediate profile but are not an application output class;
- project success did not differ convincingly by methodology;
- the sample is dominated by IT/Software and early-career respondents;
- industry and methodology are confounded;
- the earlier engine's 84.0%, equal-weight centroid model's 90.1%, and effect-size-weighted model's 91.4% historical-method agreement are illustrative same-sample diagnostics, not validated accuracy;
- independent expert-labelled cases are future validation work.

The research report may still conclude that the objectives were met if the objective is to **design, implement, and preliminarily evaluate an explainable prototype**. It should not conclude that universal methodology-selection accuracy has been established.

## 9. Application/report alignment matrix

| Research evidence | Application treatment | Handover statement |
| --- | --- | --- |
| Requirement change and flexibility strongly distinguish groups. | Flexibility construct affects methodology compatibility. | Supported by exploratory survey patterns. |
| Stakeholder involvement differs across groups. | Stakeholder feedback availability is assessed. | Related evidence exists, but availability/authority needs future validation. |
| Deadline and budget differ across groups. | Performance construct captures delivery constraints. | Rename descriptively in the report as delivery-constraint pressure. |
| Security, risk, documentation, and integration distinguish groups. | Strictness affects Traditional compatibility. | Rule is explainable but the hard override remains an expert assumption. |
| Team maturity/culture appears in open responses. | Q14 now captures short-cycle team capability. | The wording still requires expert and cognitive validation. |
| Hybrid cases sit between profiles. | Application still returns Agile or Traditional. | Mixed signals generate overlays/manual-review guidance, not a third class. |
| Success scores have a ceiling effect. | No claim that the recommendation guarantees success. | Explicit limitation in UI/report/documentation. |

## 10. Handover folder/index

Create one final release directory or archive containing:

```text
MethodAlign-IS-Handover/
├── 01-Application-Source/
├── 02-Deployment/
│   ├── deployment-guide
│   ├── environment-variable-template
│   ├── backup-and-restore-guide
│   └── production-security-checklist
├── 03-Application-Documentation/
│   ├── user-guide
│   ├── admin-guide
│   ├── architecture-and-data-model
│   ├── questionnaire-reference
│   ├── scoring-rule-reference
│   └── known-limitations-and-backlog
├── 04-Test-Evidence/
│   ├── automated-test-results
│   ├── acceptance-test-record
│   └── screenshots
├── 05-Research/
│   ├── final-thesis
│   ├── original-survey-instrument
│   ├── raw-data
│   ├── cleaned-data
│   ├── cleaning-log
│   ├── analysis-tables
│   └── ethics-and-consent-materials
└── 06-Handover/
    ├── release-notes
    ├── credentials-transfer-record
    ├── asset-inventory
    ├── known-issues
    └── client-acceptance-signoff
```

Credentials and secrets must be transferred through an appropriate secure channel, not committed to the repository or included in the general archive.

## 11. Recommended execution order

### Workstream A — Research freeze

1. Approve the research question, aim, objectives, and Version 2 claim.
2. Freeze the raw and cleaned datasets.
3. Create thesis-ready statistical tables and figures.
4. Complete the documented qualitative codebook and sample coding review.
5. Write Chapters 3, 4, and 6 around the actual evidence.
6. Complete literature citations and then finalize Chapters 1, 2, and the conclusion.

### Workstream B — Application freeze

1. Stop new feature development.
2. Run the full automated and manual acceptance suite.
3. Fix only release-blocking defects and repeat affected tests.
4. Freeze questionnaire and rule versions used in the report/demo.
5. verify deployment, backup/restore, configuration, and security.
6. Capture final screenshots and test evidence from the frozen release.

### Workstream C — Handover

1. Assemble and review the handover inventory.
2. Conduct a client walkthrough: deployment, participant assessment, administrator review, rule traceability, export, and limitations.
3. Transfer production configuration and ownership securely.
4. Record open limitations and the validation backlog.
5. Obtain written acceptance/sign-off against the agreed scope.

## 12. Definition of done

The project is finalized when:

- the application builds, deploys, and passes documented acceptance tests;
- a clean installation can be reproduced by the client;
- the Version 2 questionnaire and rules used in the research are frozen and identifiable;
- the thesis makes only claims supported by the collected evidence;
- raw and cleaned datasets, exclusions, and analysis are traceable;
- known limitations are visible rather than hidden;
- all documentation and operational ownership have been transferred;
- the client signs off against the frozen Version 2 scope.
