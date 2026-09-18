# Research Panel Presentation Brief

## 1. One-Minute System Explanation

MethodAlign IS is a decision-support engine for information systems project methodology selection. It collects project context and Likert-scale responses, calculates three construct scores, compares the project against Agile and Traditional reference profiles, and recommends the methodology with the stronger fit.

The system supports research traceability through versioned questionnaires, versioned rule configurations, stored assessment results, CSV export, and research metrics such as construct means, reliability estimates, correlations, Welch t-tests, confidence distribution, and risk flag counts.

## 2. Main Dashboard Story

Recommended presentation flow:

1. Login and access control.
2. Overview section for high-level sample and recommendation counts.
3. Research metrics for reliability and construct-level evidence.
4. Assessments section for individual result traceability.
5. Rules section for transparent decision logic and versioning.
6. Questionnaire section for instrument management and versioning.
7. Users section for governance and role-based access.

## 3. How To Explain The Recommendation

The engine calculates three construct scores:

| Construct | Plain explanation |
| --- | --- |
| FLEXIBILITY | How much the project needs and can support change, adaptation, and feedback. |
| PERFORMANCE | How strongly the project needs schedule and budget discipline. |
| STRICTNESS | How much security, compliance, integration, and governance pressure exists. |

Each project is compared with:

| Reference profile | Meaning |
| --- | --- |
| Agile baseline | A profile with high flexibility, moderate performance pressure, and lower strictness. |
| Traditional baseline | A profile with stronger performance control and strictness expectations. |

The engine calculates Agile and Traditional compatibility scores from 0 to 100 and selects the closer survey-informed reference profile. Version 2 deliberately has no single-construct override.

## 4. Key Parameters To Defend

| Parameter | Defense |
| --- | --- |
| Construct weights | They make each construct's relative influence explicit and adjustable. |
| Agile baseline | Represents expected Agile fit characteristics. |
| Traditional baseline | Represents expected Traditional fit characteristics. |
| Strictness override | Disabled so all three weighted constructs remain visible in the comparison. |
| Decision-signal rules | Provide seven descriptive views of the constructs; they are not observed outcomes. |
| Driver rules | Explain which construct signals supported the result. |
| Risk flag rules | Highlight conditions that need management attention. |
| Versioning | Preserves traceability for research validity and auditability. |

## 5. Research Metrics Talking Points

| Metric | Talking point |
| --- | --- |
| Sample size | Shows how many completed assessments are included in the current analysis. |
| Cronbach alpha | Tests internal consistency of construct question groups. |
| Construct means | Shows the average tendency of the sample across flexibility, performance, and strictness. |
| Correlations | Checks whether construct scores relate to methodology scores in expected directions. |
| Welch t-tests | Compares Agile-recommended and Traditional-recommended groups without assuming equal variance. |
| Decision-signal means | Shows derived signal averages overall and by recommendation group without claiming real-world outcomes. |
| Confidence distribution | Shows whether recommendations are mostly clear or close decisions. |
| Risk flag counts | Shows recurring delivery risks in the assessed sample. |
| Hybrid readiness | Gives advisory guidance for combining practices, while preserving Agile vs Traditional as the validated core comparison. |

## 6. Important Limitations To State Clearly

- The engine is rule-based decision support, not an automatic project success guarantee.
- The current validated comparison is Agile vs Traditional.
- Advisory practice suggestions are implementation guidance, not separate validated methodology classes.
- Results depend on self-reported input values.
- Cronbach alpha and t-test results depend on sample size and response variance.
- The dashboard reports Welch t-statistics and degrees of freedom, but not p-values.

## 7. Likely Panel Questions And Answers

### Q: Why are only Agile and Traditional used as final recommendations?

Because the system's core research design compares two primary methodology categories. Other practices such as Scrum, Kanban, PRINCE2 Agile, Disciplined Agile, or SAFe are treated as advisory implementation options, not replacement recommendation classes.

### Q: How is the final recommendation calculated?

The system averages the 12 anchored answers into FLEXIBILITY, PERFORMANCE, and STRICTNESS construct scores. It applies provisional survey effect-size weights of 1.37, 0.64, and 0.99, compares the project against survey-derived Agile and Traditional centroids, converts weighted-range-normalized gaps into 0 to 100 compatibility scores, and selects the closer profile.

The weights were calculated from the average eta-squared of the original survey factors mapped to each construct and normalized to sum to 3. They describe separation by historical methodology use and are not independently validated causal importance values.

### Q: What does confidence mean?

Confidence is based on the score gap between Agile and Traditional. A gap of 20 or more is high confidence, 10 to 19.99 is moderate, and below 10 is a close decision.

### Q: Why does high strictness not automatically force Traditional?

The exploratory evidence did not justify a hard override. High assurance/dependency pressure moves the project closer to the Traditional reference, but adaptation readiness and delivery constraints remain part of the transparent equal-weight comparison.

### Q: Why are questionnaire and rule versions important?

They preserve research traceability. Each assessment stores which questionnaire version and rules version produced the result, so historical records can be interpreted correctly even after future changes.

### Q: Can the rules be changed?

Yes, but only in Advanced mode by authorized users. Saving rules creates a new version, and previous versions can be reactivated. This supports calibration while preserving audit history.

### Q: What does Cronbach alpha show?

It estimates whether questions grouped under the same construct behave consistently. It is useful for checking instrument reliability, but it should be interpreted carefully when a construct has only two items or when sample size is small.

### Q: What do the seven derived decision signals represent?

They are descriptive relabelings of the three construct inputs, such as timeline constraint pressure, user feedback need, and integration/dependency complexity. They are not measured outcomes and do not prove methodology effectiveness.

### Q: Are the advisory strategy options empirically validated?

No. The validated decision boundary is Agile vs Traditional. Advisory options are generated from project signals to help implementation planning after the primary recommendation is known.

## 8. Demo Script

1. "This is the MethodAlign IS admin dashboard. It supports both operational review and research traceability."
2. "The Overview section shows total submissions and recommendation distribution."
3. "In Advanced mode, research metrics show reliability, construct behavior, group differences, and distributions."
4. "The Assessments section lets us inspect an individual result and confirm the profile answers, Likert answers, construct scores, rule version, and questionnaire version."
5. "The Rules section makes the decision model transparent. We can see construct weights, baselines, normalization, the disabled override, driver rules, risk rules, signal mappings, and next-step templates."
6. "Rule changes are versioned, so calibration does not destroy historical traceability."
7. "The Questionnaire section manages the research instrument. Question changes are also versioned."
8. "The Users section controls access, separating analyst, configuration editor, and super admin responsibilities."

## 9. Short Closing Statement

The dashboard is designed to make the comparative engine explainable, auditable, and research-ready. It connects questionnaire responses to construct scores, construct scores to methodology fit, and methodology fit to decision reports and aggregate research metrics.
