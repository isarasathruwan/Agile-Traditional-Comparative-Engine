# Reproducible survey tables

Primary cleaned sample: n=107; excluded probable duplicates: [64, 79, 83, 97].
Valid extreme responses were retained; no scale-value outliers were removed.

## Methodology distribution

| Methodology | n |
| --- | ---: |
| Agile | 54 |
| Hybrid | 26 |
| Traditional | 27 |

## Project-factor means and effect sizes

| Factor | Overall | Agile | Hybrid | Traditional | Eta-squared | 95% bootstrap CI | Holm p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Requirements Change | 3.21 | 4.02 | 2.92 | 1.89 | 0.682 | 0.580–0.786 | 0.0022 |
| Stakeholder Involvement | 3.42 | 3.93 | 3.15 | 2.67 | 0.337 | 0.203–0.502 | 0.0022 |
| Deadline Pressure | 3.68 | 3.22 | 4.00 | 4.30 | 0.222 | 0.112–0.375 | 0.0022 |
| Budget Pressure | 3.92 | 3.44 | 4.19 | 4.59 | 0.299 | 0.183–0.442 | 0.0022 |
| Project Risk | 3.37 | 2.91 | 3.38 | 4.30 | 0.399 | 0.263–0.554 | 0.0022 |
| Integration Complexity | 3.46 | 3.11 | 3.46 | 4.15 | 0.253 | 0.130–0.407 | 0.0022 |
| Security Requirements | 3.63 | 3.04 | 3.73 | 4.70 | 0.416 | 0.298–0.569 | 0.0022 |
| Documentation Need | 3.36 | 2.61 | 3.58 | 4.63 | 0.542 | 0.437–0.657 | 0.0022 |
| Project Size | 2.06 | 1.56 | 2.23 | 2.89 | 0.415 | 0.276–0.563 | 0.0022 |
| Flexibility Need | 3.37 | 4.22 | 3.19 | 1.85 | 0.651 | 0.551–0.749 | 0.0022 |
| Success | 4.04 | 4.13 | 3.96 | 3.93 | 0.034 | 0.003–0.139 | 0.1834 |

Eta-squared is the proportion of observed factor variance associated with the three reported-methodology groups. It is not a causal effect. P-values use 5,000 label permutations and Holm correction.

## Provisional survey-derived centroids

| Methodology | Adaptation/readiness | Delivery constraints | Assurance/dependencies |
| --- | ---: | ---: | ---: |
| Agile | 4.06 | 3.33 | 2.92 |
| Traditional | 2.14 | 4.44 | 4.44 |

## Effect-size-derived provisional weights

| Construct | Mean source eta-squared | Weight | Total influence | Per questionnaire item | Per item with full document coverage | 95% bootstrap CI |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| FLEXIBILITY | 0.556 | 1.37 | 45.64% | 11.41% | 8.56% | 1.15–1.61 |
| PERFORMANCE | 0.260 | 0.64 | 21.35% | 7.12% | 5.34% | 0.44–0.83 |
| STRICTNESS | 0.402 | 0.99 | 33.01% | 6.60% | 4.95% | 0.85–1.12 |

The per-question figures are effective maximum contributions because questions are averaged equally within a construct; they are not independently estimated item weights. Full confirmed document coverage can contribute 25% of a construct.

## Historical-methodology agreement diagnostics

| Model | Correct / n | Agreement | 95% Wilson CI | Balanced accuracy | Cohen kappa |
| --- | ---: | ---: | ---: | ---: | ---: |
| Equal weights | 73/81 | 90.1% | 81.70%–94.91% | 0.907 | 0.786 |
| Effect-size weights | 74/81 | 91.4% | 83.22%–95.75% | 0.907 | 0.807 |

These are same-sample calibration diagnostics against the methodology historically used. They are not prospective accuracy or proof that the historical choice was suitable.
