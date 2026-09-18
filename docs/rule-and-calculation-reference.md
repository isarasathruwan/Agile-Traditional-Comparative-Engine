# Rule And Calculation Reference

## 1. Purpose Of The Rule Engine

The rule engine converts questionnaire responses into a comparative methodology recommendation. The output is either:

- Agile
- Traditional

The engine does not claim that one methodology is universally better. It evaluates which reference profile the submitted project is closer to, based on the configured rules.

## 2. Research Constructs

The engine uses three constructs:

| Construct | Meaning | High score suggests |
| --- | --- | --- |
| FLEXIBILITY | Adaptation and iterative-delivery readiness. | The project has both a need and practical readiness for iterative delivery. |
| PERFORMANCE | Timeline, budget, and delivery-change constraints. | The project needs predictable delivery and controlled plan changes. |
| STRICTNESS | Assurance, consequence, traceability, dependency, and coordination complexity. | The project requires stronger governance and dependency control. |

Each construct score is the average of its related Likert answers.

Formula:

```text
construct_score = sum(answers_for_construct) / number_of_answers_for_construct
```

Example:

```text
FLEXIBILITY answers = 5, 4, 4
FLEXIBILITY score = (5 + 4 + 4) / 3 = 4.33
```

## 3. Construct Weights

Active provisional values:

| Construct | Weight | Nominal model influence | Meaning |
| --- | ---: | ---: | --- |
| FLEXIBILITY | 1.37 | 45.64% | Adaptation/readiness was the strongest methodology-group separator in the cleaned survey. |
| PERFORMANCE | 0.64 | 21.35% | Deadline and budget constraints separated the groups less strongly in this sample. |
| STRICTNESS | 0.99 | 33.01% | Assurance and dependency factors showed substantial group separation. |

The weights are derived from the duplicate-screened Google Forms sample. For each construct, the eta-squared values of its mapped source factors were averaged and normalized so the three weights sum to 3:

```text
construct_effect = mean(eta_squared values for mapped source factors)
construct_weight = 3 x construct_effect / sum(all construct effects)
```

The unrounded weights are 1.369286, 0.640480, and 0.990235. The active rule uses 1.37, 0.64, and 0.99. Repeating the calculation on all 111 raw responses produces 1.36, 0.66, and 0.98, showing that the four duplicate exclusions do not materially determine the result.

These are **survey-derived provisional weights**, not independently validated importance coefficients. They describe separation by methodology historically used, and the sample is confounded by industry.

Weights adjust how strongly each construct contributes to the distance between the project and each methodology baseline.

Weighted score:

```text
weighted_construct_score = construct_score * construct_weight
```

Panel explanation:

The weights represent the relative importance of constructs in methodology fit. A higher weight means a mismatch in that construct affects the final compatibility score more strongly.

### 3.1 Effective Question Influence

The application does not fit or store 12 separate questionnaire coefficients. Questions are averaged equally inside their construct. Their nominal maximum contributions to the questionnaire-only decision distance are therefore:

| Questions | Construct | Nominal contribution per question | With full confirmed document coverage |
| --- | --- | ---: | ---: |
| Q11–Q14 | FLEXIBILITY | 11.41% each | 8.56% each |
| Q15–Q17 | PERFORMANCE | 7.12% each | 5.34% each |
| Q18–Q22 | STRICTNESS | 6.60% each | 4.95% each |

The second percentage applies when confirmed document evidence supplies the maximum 25% contribution for that construct. Q1–Q10 are profile questions and have zero weight in the Agile-versus-Traditional compatibility calculation.

## 4. Baseline Profiles

The engine compares the project against two reference profiles.

### 4.1 Agile Baseline

Default values:

| Construct | Agile baseline | Interpretation |
| --- | ---: | --- |
| FLEXIBILITY | 4.06 | Cleaned Agile cases showed high adaptation/readiness. |
| PERFORMANCE | 3.33 | Cleaned Agile cases showed moderate delivery-constraint pressure. |
| STRICTNESS | 2.92 | Cleaned Agile cases showed lower assurance/dependency pressure. |

### 4.2 Traditional Baseline

Default values:

| Construct | Traditional baseline | Interpretation |
| --- | ---: | --- |
| FLEXIBILITY | 2.14 | Cleaned Traditional cases showed lower adaptation/readiness. |
| PERFORMANCE | 4.44 | Cleaned Traditional cases showed high delivery-constraint pressure. |
| STRICTNESS | 4.44 | Cleaned Traditional cases showed high assurance/dependency pressure. |

Panel explanation:

The baselines are not user answers. They are reference profiles representing expected characteristics of Agile and Traditional methodology fit.

## 5. Gap Calculation

The engine calculates how far the project is from each methodology baseline.

For Agile:

```text
agile_gap = sum(abs(weighted_project_construct - weighted_agile_baseline_construct))
```

For Traditional:

```text
traditional_gap = sum(abs(weighted_project_construct - weighted_traditional_baseline_construct))
```

Where:

```text
weighted_project_construct = project_construct_score * construct_weight
weighted_baseline_construct = baseline_construct_score * construct_weight
```

Interpretation:

- Smaller gap means the project profile is closer to that methodology.
- Larger gap means the project profile is less similar to that methodology.

## 6. Compatibility Scores

The gaps are converted into 0 to 100 compatibility scores.

Formula:

```text
gap_scale = 4 * sum(construct_weights)
methodology_score = max(0, 100 - (methodology_gap / gap_scale) * 100)
```

Meaning:

| Score range | Interpretation |
| --- | --- |
| 80 to 100 | Very strong compatibility. |
| 60 to 79 | Good compatibility. |
| 40 to 59 | Moderate compatibility. |
| Below 40 | Weak compatibility. |

The weighted range is the maximum possible distance across three 1–5 constructs. This keeps the score normalized if weights change. Historical rule versions retain the legacy divisor of 15.

## 7. Recommendation Logic

The active survey-informed rule selects the reference profile with the higher compatibility score.

```text
if agile_score >= traditional_score:
    recommendation = Agile
else:
    recommendation = Traditional
```

`strictness_override_enabled` is `false` in Version 2. The stored threshold remains available for legacy versions or an explicitly configured future rule, but it does not override the Version 2 distance comparison.

## 8. Confidence Level

Confidence is based on the absolute score gap between Agile and Traditional.

Formula:

```text
score_gap = abs(agile_score - traditional_score)
```

| Confidence level | Rule | Meaning |
| --- | --- | --- |
| high | score gap >= 20 | One methodology is clearly stronger. |
| moderate | score gap >= 10 and < 20 | One methodology is stronger, but review is still useful. |
| close | score gap < 10 | The result is narrow and should be reviewed carefully. |

Panel explanation:

Confidence is not statistical confidence. It is decision confidence based on the difference between the two compatibility scores.

## 9. Derived Decision-Signal Rules

The dashboard includes seven descriptive decision signals calculated from the same construct scores. They are not measured project outcomes and must not be used as evidence that the selected methodology caused success.

Default mapping:

| API key / display meaning | Default construct mapping | Meaning |
| --- | --- | --- |
| timeline_adherence / Timeline constraint pressure | PERFORMANCE: 1.0 | Schedule constraint signal. |
| budget_accuracy / Budget constraint pressure | PERFORMANCE: 1.0 | Funding constraint signal. |
| product_quality / Quality assurance pressure | PERFORMANCE: 0.5, STRICTNESS: 0.5 | Combined delivery-control and assurance signal. |
| user_satisfaction / User feedback need | FLEXIBILITY: 1.0 | Iterative feedback signal. |
| communication_effectiveness / Collaboration readiness | FLEXIBILITY: 1.0 | Stakeholder/team collaboration signal. |
| security_integration / Security and assurance criticality | STRICTNESS: 1.0 | Assurance-control signal. |
| system_integration_effectiveness / Integration and dependency complexity | STRICTNESS: 1.0 | External dependency and coordination signal. |

Formula:

```text
decision_signal = sum(construct_score * signal_weight) / sum(signal_weights)
```

Example:

```text
product_quality = (PERFORMANCE * 0.5 + STRICTNESS * 0.5) / 1.0
```

Panel explanation:

The seven signals provide alternate descriptive views of the same three inputs. The stable API keys are retained for backward compatibility.

## 10. Driver Rules

Driver rules identify factors that supported the recommendation.

Default driver rules:

| Rule key | Construct | Methodology | Threshold | Label | Meaning |
| --- | --- | --- | ---: | --- | --- |
| requirements_change | FLEXIBILITY | Agile | 3.8 | High change adaptability | Flexibility is high enough to support Agile. |
| delivery_control | PERFORMANCE | Traditional | 3.8 | Strong timeline and budget control need | Performance pressure is high enough to support stronger control. |
| security_control | STRICTNESS | Traditional | 3.8 | Security and compliance pressure | Strictness is high enough to support Traditional governance. |

Trigger formula:

```text
if construct_score >= driver_threshold:
    show_driver
```

Driver fields:

| Field | Meaning |
| --- | --- |
| rule key | Stable internal name for the rule. |
| label | Human-readable explanation displayed in the report. |
| construct | Construct evaluated by the rule. |
| methodology | Methodology supported by the driver. |
| threshold | Minimum construct score needed to trigger the driver. |

## 11. Risk Flag Rules

Risk flags identify conditions that need attention before the recommendation is applied.

Default risk flags:

| Rule key | Metric or construct | Operator | Threshold | Label |
| --- | --- | --- | ---: | --- |
| close_call | score_gap | lte | 10 | Recommendation is close; review tradeoffs before committing. |
| security_sensitive | STRICTNESS | gte | 3.8 | Security, compliance, or integration controls need explicit planning. |
| low_adaptability | FLEXIBILITY | lte | 2.5 | Low adaptability may limit iterative delivery benefits. |

Operators:

| Operator | Meaning |
| --- | --- |
| gte | Greater than or equal to threshold. |
| lte | Less than or equal to threshold. |

Available risk metrics:

| Metric | Meaning |
| --- | --- |
| score_gap | Difference between Agile and Traditional scores. |
| agile_score | Agile compatibility score. |
| traditional_score | Traditional compatibility score. |
| FLEXIBILITY | Flexibility construct score. |
| PERFORMANCE | Performance construct score. |
| STRICTNESS | Strictness construct score. |

Panel explanation:

Risk flags do not necessarily reject the recommendation. They identify conditions the project team should manage during delivery.

## 12. Explanation Templates

Explanation templates provide the summary text shown in the result report.

Default Agile explanation:

```text
The project profile is closer to Agile where adaptability, stakeholder feedback, and communication drive success.
```

Default Traditional explanation:

```text
The project profile is closer to Traditional where planning discipline, documentation, security, and integration control drive success.
```

Panel explanation:

These templates convert the engine's numeric result into a stakeholder-readable rationale.

## 13. Next Step Templates

Next steps are recommendation-specific action items shown in the decision report.

Default Agile next steps:

| Step | Meaning |
| --- | --- |
| Confirm stakeholder availability for frequent reviews. | Agile depends on regular feedback. |
| Define short iteration goals and feedback checkpoints. | Work should be managed in short cycles. |
| Track scope changes openly so budget and timeline impact stays visible. | Adaptability must still be controlled. |

Default Traditional next steps:

| Step | Meaning |
| --- | --- |
| Lock critical requirements and approval gates before implementation. | Traditional delivery depends on upfront clarity. |
| Document security, compliance, and integration dependencies early. | Control-heavy work should be identified early. |
| Use milestone reviews to control timeline and budget variance. | Progress should be monitored against planned milestones. |

## 14. Rule Preview

The Preview Rules button tests the draft rule payload on two built-in sample projects:

| Scenario | Profile pattern |
| --- | --- |
| Dynamic Project | High flexibility, moderate performance pressure, low strictness. |
| Control Heavy Project | Low flexibility, high performance pressure, high strictness. |

Preview output:

| Field | Meaning |
| --- | --- |
| scenario | Sample project name. |
| recommendation | Agile or Traditional result under the draft rules. |
| agile_score | Agile compatibility score under the draft rules. |
| traditional_score | Traditional compatibility score under the draft rules. |
| confidence_level | high, moderate, or close based on score gap. |

Panel explanation:

Preview is a safety check. It lets the admin see whether rule changes behave sensibly before saving a new active version.

## 15. Rule Versioning

Every saved rules change creates a new version.

| Field | Meaning |
| --- | --- |
| version | Numeric rule version. |
| payload | Full rule configuration. |
| changed_by | Admin email or system user that created or activated the version. |
| change_note | Human explanation for the change. |
| created_at | When the version was created. |

Why versioning matters:

- It provides auditability.
- It allows rollback by activating an earlier version.
- It preserves which rule set was used for each submitted assessment.

## 16. Decision Report Fields

Each assessment stores a decision report with these fields:

| Field | Meaning |
| --- | --- |
| recommendation | Final Agile or Traditional recommendation. |
| confidence_level | high, moderate, or close based on score gap. |
| score_gap | Absolute difference between Agile and Traditional scores. |
| methodology_fit_summary | Template explanation for the selected methodology. |
| outcome_scores | Seven dependent variable scores. |
| drivers | Triggered driver rules. |
| risk_flags | Triggered risk warning rules. |
| tradeoffs | Strengths, watch areas, and methodology notes. |
| hypothesis_evidence | Scores mapped to research hypotheses H1 to H5. |
| strategy_profile | Advisory hybrid and delivery-practice guidance. |
| next_steps | Recommended actions based on final methodology. |
| limitations | Boundaries explaining that the output is decision support, not a guarantee. |

## 17. Hybrid Readiness And Advisory Strategy

Hybrid readiness is an advisory score from 0 to 100. It is not the main Agile vs Traditional recommendation.

Inputs:

| Input | Contribution |
| --- | --- |
| Score gap | Smaller Agile vs Traditional gap increases hybrid readiness. |
| Minimum of flexibility and strictness | Projects with both adaptability and governance pressure are more hybrid-ready. |
| Performance | Delivery pressure contributes to hybrid readiness. |
| Complexity signal | Integration, migration, upgrade, large team, or large organization increases hybrid readiness. |

Formula summary:

```text
hybrid_score =
  max(0, 1 - score_gap / 40) * 40
  + (min(FLEXIBILITY, STRICTNESS) / 5) * 25
  + (PERFORMANCE / 5) * 15
  + 20 if complexity signal exists
```

Hybrid levels:

| Level | Rule |
| --- | --- |
| high | hybrid_score >= 70 |
| moderate | hybrid_score >= 45 and < 70 |
| low | hybrid_score < 45 |

Delivery strategy labels:

| Strategy | When used |
| --- | --- |
| agile_led_with_governance | High hybrid readiness and Agile recommendation. |
| traditional_led_with_iterative_validation | High hybrid readiness and Traditional recommendation. |
| primary_with_targeted_practices | Moderate hybrid readiness. |
| adaptive_agile | Low hybrid readiness and Agile recommendation. |
| predictive_traditional | Low hybrid readiness and Traditional recommendation. |

Advisory practice options:

| Option | Trigger logic |
| --- | --- |
| Scrum | Flexibility >= 3.8 and strictness < 3.8. |
| Kanban | Performance >= 3.8 or project type includes maintenance. |
| PRINCE2 Agile | Strictness >= 3.8, performance >= 3.5, and flexibility >= 3.0. |
| Disciplined Agile | Hybrid score >= 45. |
| SAFe | Complexity signal exists. |
| Agile or Traditional core fallback | Used when no advisory option is triggered. |

Panel explanation:

The research engine validates Agile vs Traditional as the primary comparison. Hybrid and framework suggestions are advisory practices generated from project conditions and should be discussed as implementation guidance, not as separate empirically validated methodology classes.
