# Questionnaire And Research Metrics Reference

## 1. Questionnaire Purpose

The questionnaire collects two kinds of data:

- Profile data: describes the respondent, organization, and project context.
- Likert data: produces the research construct scores used by the decision engine.

The active questionnaire is versioned. Each assessment stores the questionnaire version used at submission time.

## 2. Profile Questions

Profile questions describe the project context. They support assessment records, reporting, CSV export, and some advisory strategy logic.

Default profile questions:

| ID | Profile key | Kind | Prompt | Options or placeholder | Purpose |
| --- | --- | --- | --- | --- | --- |
| Q1 | name | text | What's your name? | Your full name | Identifies the respondent. |
| Q2 | role | pill | What is your role? | Project Manager, Software Developer, System Architect, IS Practitioner, Executive, Other | Captures the respondent's perspective. |
| Q3 | company | text | What's your company name? | Company or organization name | Identifies the organization. |
| Q4 | industry | pill | What industry are you in? | Government, Banking & Finance, Healthcare, Technology, Telecom, Education, Retail, Other | Enables industry-level grouping. |
| Q5 | orgSize | pill | How large is your organization? | 1-10, 11-50, 51-200, 201-1,000, 1,000+ | Helps identify organizational scale. |
| Q6 | projectName | text | What's the name of your project? | Project name | Identifies the assessed project. |
| Q7 | projectType | pill | What type of project is this? | New System, System Integration, Upgrade & Migration, Maintenance, Other | Supports complexity and delivery-context analysis. |
| Q8 | duration | pill | What is the expected project duration? | < 3 months, 3-6 months, 6-12 months, 1-2 years, 2+ years | Captures project time scale. |
| Q9 | teamSize | pill | How large is your project team? | 1-5, 6-15, 16-30, 30+ | Helps detect coordination complexity. |
| Q10 | budget | pill | What is the approximate budget range? | < $10K, $10K-$50K, $50K-$200K, $200K-$1M, $1M+, Prefer not to say | Captures budget scale. |

## 3. Profile Key Mapping

The admin questionnaire editor uses frontend-style profile keys. The backend maps those keys to stored submission fields.

| Questionnaire profile key | Stored field |
| --- | --- |
| name | name |
| role | role |
| company | company |
| industry | industry |
| orgSize | org_size |
| projectName | project_name |
| projectType | project_type |
| duration | duration |
| teamSize | team_size |
| budget | budget |

## 4. Likert Questions

Likert questions are scored from 1 to 5. These answers are grouped by construct and averaged.

The survey-informed Version 2 uses 12 neutral, project-specific questions. Each question has its own observable answer anchors rather than agreement labels.

| ID | Reporting construct | Prompt summary | 1 anchor | 5 anchor |
| --- | --- | --- | --- | --- |
| Q11 | Adaptation and iterative readiness | Expected requirements change | Stable | Constant or substantial change |
| Q12 | Adaptation and iterative readiness | Uncertainty in solution and acceptance criteria | Fully defined | Substantial discovery required |
| Q13 | Adaptation and iterative readiness | Authorized stakeholder review frequency | Major milestones only | Whenever needed |
| Q14 | Adaptation and iterative readiness | Team capability for short delivery cycles | No capability | Highly experienced |
| Q15 | Delivery constraints | How fixed the delivery date is | Flexible | Immovable |
| Q16 | Delivery constraints | How fixed the budget/funding ceiling is | Flexible | No overrun permitted |
| Q17 | Delivery constraints | Approval required to change the plan | Team discretion | Contractual or board approval |
| Q18 | Assurance and dependency complexity | Regulatory, legal, or audit obligations | None | Extensive mandatory obligations |
| Q19 | Assurance and dependency complexity | Credible consequence of failure/compromise | Low and reversible | Severe or legally significant |
| Q20 | Assurance and dependency complexity | Controlled documentation and traceability | Working notes | Complete audit-grade traceability |
| Q21 | Assurance and dependency complexity | External vendor, legacy, or interface dependency | Self-contained | Many critical external dependencies |
| Q22 | Assurance and dependency complexity | Cross-team/organization sequencing | One small team | Tightly coupled multi-organization delivery |

## 5. Likert Scale Interpretation

The UI stores each answer as an integer from 1 to 5, but the meaning is defined by the five anchors attached to that specific question. The selected anchor is shown in review and result views. Questionnaire versions cannot be saved with blank anchors or identical endpoints.

## 6. Construct Scores

The system calculates:

| Construct | Based on | Formula |
| --- | --- | --- |
| FLEXIBILITY | Q11–Q14 | Average adaptation/readiness score. |
| PERFORMANCE | Q15–Q17 | Average delivery-constraint score. |
| STRICTNESS | Q18–Q22 | Average assurance/dependency score. |

If the questionnaire is edited, the construct score uses the current active questions assigned to that construct.

### 6.1 Why These Questions Were Selected

Question selection is traceable to three evidence types:

- direct or related closed-survey factors and their methodology-group effect sizes;
- recurring themes in the two open-text survey questions;
- conceptual gaps exposed by the survey, such as team capability, change authority, regulatory obligation, failure consequence, and cross-team coordination.

The detailed evidence, limitation, and effective weight for every item are recorded in `docs/research_analysis/question-rationale-and-weights.md`. The evidence is explicitly labelled direct, indirect, related, proxy, or qualitative so newly introduced wording is not misrepresented as having been measured by the original Google Form.

### 6.2 Active Provisional Weights

| Construct | Active weight | Nominal influence | Effective influence per question |
| --- | ---: | ---: | ---: |
| FLEXIBILITY | 1.37 | 45.64% | 11.41% for each of Q11–Q14 |
| PERFORMANCE | 0.64 | 21.35% | 7.12% for each of Q15–Q17 |
| STRICTNESS | 0.99 | 33.01% | 6.60% for each of Q18–Q22 |

The weights are proportional to the average eta-squared of the mapped original survey factors and normalized to sum to 3. They are provisional because the source outcome is methodology historically used, not an independent expert judgment of methodology suitability.

## 7. Document-Only Evidence Questions

Uploaded documents are evaluated against a separate optional evidence instrument. These questions do not replace, prefill, or become part of the mandatory Q11-Q22 questionnaire. A document question has no effect unless the system finds a cited, moderate-or-high-confidence answer and the participant confirms it.

| ID | Construct | Document evidence prompt |
| --- | --- | --- |
| D01 | FLEXIBILITY | The document shows that requirements are expected to materially change after delivery begins. |
| D02 | FLEXIBILITY | The document requires discovery, prototyping, piloting, or phased validation before the scope is settled. |
| D03 | FLEXIBILITY | The document commits named business stakeholders to recurring reviews, demonstrations, or feedback. |
| D04 | PERFORMANCE | The document establishes a fixed or externally committed delivery date. |
| D05 | PERFORMANCE | The document establishes a fixed budget, funding ceiling, or explicit cost-overrun constraint. |
| D06 | PERFORMANCE | The document requires fixed milestones, predefined deliverables, or formal acceptance before release. |
| D07 | STRICTNESS | The document identifies mandatory regulatory, legal, audit, or records-retention obligations. |
| D08 | STRICTNESS | The document requires formal security, privacy, safety, or assurance controls. |
| D09 | STRICTNESS | The document shows delivery depends on external vendors, legacy platforms, or multiple system interfaces. |
| D10 | STRICTNESS | The document requires formal change, procurement, architecture, or release approval gates. |

The participant first collects the full PDF set, then selects **Analyze documents**. Until that action, files are encrypted at rest but no text extraction, embeddings, facts, or evidence calls run. Analysis seals the set: the worker extracts all valid documents, builds the complete retrieval index, then generates facts and D01-D10 suggestions against that corpus. The participant can confirm the proposed value or omit it; score editing is intentionally not available.

## 8. Decision Use Of Document Evidence

Document evidence is supplemental and coverage-capped. For each construct:

```text
coverage = confirmed document-question weight / configured document-question weight
contribution = 0.25 x coverage
decision score = questionnaire score x (1 - contribution) + document score x contribution
```

The maximum document contribution is 25% for a fully covered construct. Unconfirmed, omitted, low-confidence, or uncited evidence contributes 0%. The assessment result records questionnaire scores, document scores, coverage, contribution, and final decision scores for auditability.

## 9. Research Metrics Separation

Core research metrics, including construct means, correlations, reliability, and t-tests, use the mandatory questionnaire answers only. They are filtered by both questionnaire version and rule version. The dashboard separately reports document-evidence adoption, coverage, and score-adjustment counts so supplemental evidence does not contaminate the research instrument.

## 10. Questionnaire Validation Rules

When an admin saves a questionnaire version, the backend checks:

| Rule | Reason |
| --- | --- |
| All question IDs must be unique. | Prevents answer mapping conflicts. |
| Profile and Likert sections must both exist. | The system requires context and scored answers. |
| Profile keys must be supported keys. | Ensures answers can be stored correctly. |
| Pill questions need at least two options. | Single-option choices are not valid survey inputs. |
| Text questions cannot include options. | Text fields and option lists are separate input types. |
| Likert questions must include FLEXIBILITY, PERFORMANCE, and STRICTNESS. | The engine requires all three constructs to calculate recommendations. |
| Each Likert question must have five non-empty, distinct endpoint anchors. | Makes the numerical response observable and interpretable. |
| A submitted assessment must contain each active Likert question exactly once with the configured construct. | Prevents incomplete or mismatched scoring. |

## 11. Questionnaire Versioning

Each saved questionnaire creates a new version.

| Field | Meaning |
| --- | --- |
| version | Numeric questionnaire version. |
| title | Human-readable title for the questionnaire version. |
| payload | Full question definition. |
| changed_by | Admin email or system user that created or activated the version. |
| change_note | Explanation for why the version changed. |
| created_at | Date and time the version was created. |

Why versioning matters:

- It protects historical traceability.
- It lets researchers explain which questions produced each result.
- It supports rollback to older questionnaires.

## 12. Research Metrics Overview

Research metrics are shown in the Overview section when Advanced Tools are enabled and the user has permission to view research data.

The metrics are calculated from stored assessment results and answers.

## 13. Sample Size

| Metric | Meaning |
| --- | --- |
| sample_size | Number of assessment results included in the research metric calculation. |

Panel explanation:

Sample size is the number of valid completed assessments available for current research analysis.

## 14. Cronbach Alpha

Cronbach alpha is calculated separately for each construct:

- FLEXIBILITY
- PERFORMANCE
- STRICTNESS

Meaning:

| Value range | Common interpretation |
| --- | --- |
| 0.9 and above | Excellent internal consistency. |
| 0.8 to 0.89 | Good internal consistency. |
| 0.7 to 0.79 | Acceptable internal consistency. |
| 0.6 to 0.69 | Questionable internal consistency. |
| Below 0.6 | Weak internal consistency. |
| n/a | Not enough complete data or no variance. |

Panel explanation:

Cronbach alpha checks whether the questions assigned to the same construct behave consistently as a group. If there are fewer than two complete responses or insufficient variance, the dashboard shows `n/a`.

Important limitation:

Cronbach alpha describes internal consistency, not validity. It must be interpreted with item content, sample composition, and version-specific results.

## 15. Construct Score Means

| Metric | Meaning |
| --- | --- |
| FLEXIBILITY mean | Average flexibility score across all results. |
| PERFORMANCE mean | Average performance score across all results. |
| STRICTNESS mean | Average strictness score across all results. |

Panel explanation:

Construct means show the overall tendency of the sample. For example, a high STRICTNESS mean suggests many projects in the sample involve security, compliance, or integration pressure.

## 16. Correlations

The dashboard calculates Pearson correlation values for:

| Correlation key | Meaning |
| --- | --- |
| flexibility_vs_agile | Relationship between flexibility construct scores and Agile compatibility scores. |
| performance_vs_agile | Relationship between performance construct scores and Agile compatibility scores. |
| strictness_vs_traditional | Relationship between strictness construct scores and Traditional compatibility scores. |
| agile_vs_traditional | Relationship between Agile and Traditional compatibility scores. |

Interpretation:

| Value | Meaning |
| --- | --- |
| Close to 1 | Strong positive relationship. |
| Close to -1 | Strong negative relationship. |
| Close to 0 | Weak or no linear relationship. |
| n/a | Not enough data or no variance. |

Panel explanation:

Correlations help explain whether the construct behavior aligns with the expected methodology score behavior.

## 17. Independent Sample t-Tests (Welch)

The dashboard compares Agile-recommended and Traditional-recommended groups for:

| Test key | Compares |
| --- | --- |
| flexibility_agile_vs_traditional | FLEXIBILITY scores between Agile-recommended and Traditional-recommended groups. |
| performance_agile_vs_traditional | PERFORMANCE scores between Agile-recommended and Traditional-recommended groups. |
| strictness_agile_vs_traditional | STRICTNESS scores between Agile-recommended and Traditional-recommended groups. |

Fields shown for each t-test:

| Field | Meaning |
| --- | --- |
| n_group_a | Number of records in the first group. In this implementation, Agile-recommended records. |
| n_group_b | Number of records in the second group. In this implementation, Traditional-recommended records. |
| mean_group_a | Average construct score for group A. |
| mean_group_b | Average construct score for group B. |
| t_statistic | Welch t statistic comparing group means. |
| df | Welch-Satterthwaite degrees of freedom. |

Panel explanation:

Welch's t-test is used because it does not assume the two groups have equal variance. The dashboard currently reports t-statistic and degrees of freedom, not p-values.

## 18. Derived Decision-Signal Means

The dashboard reports means for seven derived decision signals. They are alternate labels calculated from the three constructs, not independently observed project outcomes:

| Stable API key | Display meaning |
| --- | --- |
| timeline_adherence | Timeline constraint pressure. |
| budget_accuracy | Budget constraint pressure. |
| product_quality | Quality assurance pressure. |
| user_satisfaction | User feedback need. |
| communication_effectiveness | Collaboration readiness. |
| security_integration | Security and assurance criticality. |
| system_integration_effectiveness | Integration and dependency complexity. |

Groups:

| Group | Meaning |
| --- | --- |
| overall | Average across all assessment results. |
| agile_recommended | Average across records where Agile was recommended. |
| traditional_recommended | Average across records where Traditional was recommended. |

Panel explanation:

These means describe how derived signals differ across records and recommendation groups. They do not test real-world outcomes.

## 19. Confidence Distribution

| Category | Rule | Meaning |
| --- | --- | --- |
| high | Score gap >= 20 | Clear recommendation difference. |
| moderate | Score gap >= 10 and < 20 | Noticeable recommendation difference. |
| close | Score gap < 10 | Narrow decision that needs review. |

Panel explanation:

This distribution tells the panel how many recommendations were clear versus borderline.

## 17. Risk Flag Counts

Risk flag counts show how often each risk rule triggered across all results.

Default risk flags:

| Risk flag | Meaning |
| --- | --- |
| close_call | Agile and Traditional scores are close. |
| security_sensitive | Strictness is high enough to require explicit security, compliance, or integration planning. |
| low_adaptability | Flexibility is low, which may reduce the practical benefit of Agile practices. |

Panel explanation:

Risk flag counts show recurring delivery concerns in the sample.

## 18. Hybrid Readiness Distribution

| Category | Meaning |
| --- | --- |
| high | Project profile may benefit from combining the primary recommendation with selected practices from the other approach. |
| moderate | Some targeted hybrid practices may be useful. |
| low | The primary Agile or Traditional recommendation should remain the dominant guidance. |

Panel explanation:

Hybrid readiness is advisory. It supports delivery planning but does not replace the Agile vs Traditional classification.

## 19. Delivery Strategy Distribution

Delivery strategy counts show how often each advisory strategy appeared.

Possible strategies:

| Strategy | Meaning |
| --- | --- |
| agile_led_with_governance | Agile primary direction with stronger governance controls. |
| traditional_led_with_iterative_validation | Traditional primary direction with iterative validation checkpoints. |
| primary_with_targeted_practices | Primary recommendation plus selected supporting practices. |
| adaptive_agile | Agile as the main direction with low hybrid complexity. |
| predictive_traditional | Traditional as the main direction with low hybrid complexity. |

## 20. Advisory Practices

Advisory practice counts show how often practices such as Scrum, Kanban, PRINCE2 Agile, Disciplined Agile, or SAFe were suggested.

Important panel statement:

These practices are not treated as separate validated recommendation classes in this system. They are practical guidance layered on top of the validated Agile vs Traditional decision.

## 21. Hypothesis Evidence In Assessment Reports

The decision report maps outcome scores to five research hypotheses:

| Hypothesis | Label | Score source |
| --- | --- | --- |
| H1 | Timeline adherence differs by methodology fit. | timeline_adherence |
| H2 | Agile is expected to improve user satisfaction when adaptability is high. | user_satisfaction |
| H3 | Traditional is expected to perform better in security-sensitive environments. | security_integration |
| H4 | Methodology choice influences system integration effectiveness. | system_integration_effectiveness |
| H5 | Methodology fit relates to overall IS project success. | Higher of Agile and Traditional score |

Panel explanation:

The hypothesis evidence section provides a research trace from individual assessment output back to the study's conceptual claims.
