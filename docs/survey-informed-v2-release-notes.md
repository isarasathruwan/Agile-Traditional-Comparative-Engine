# Survey-Informed Version 2 Release Notes

**Release date:** 27 July 2026  
**Decision classes:** Agile or Traditional  
**Research status:** Exploratory calibration; prospective validation still required

## What changed

- Replaced the seven agreement statements with 12 neutral, project-fact questions (Q11–Q22).
- Added five question-specific response anchors to every scored item.
- Kept three stored construct keys for compatibility, while presenting clearer names:
  - FLEXIBILITY: adaptation and iterative readiness;
  - PERFORMANCE: delivery constraints;
  - STRICTNESS: assurance and dependency complexity.
- Initially activated equal construct weights of 1.0; follow-up migration `20260727_0016` preserves that historical version and activates provisional survey effect-size weights of 1.37, 0.64, and 0.99.
- Activated the cleaned-survey centroids:
  - Agile: 4.06, 3.33, 2.92;
  - Traditional: 2.14, 4.44, 4.44.
- Replaced the fixed distance divisor with weighted-range normalization.
- Disabled the hard strictness override; the closer overall reference profile wins.
- Added exact server-side answer-set and construct validation.
- Isolated dashboard research calculations by questionnaire and rule version.
- Relabeled the seven calculated “outcomes” as derived decision signals in user-facing views.
- Preserved historical scoring behavior when an older stored rule lacks the new settings.

## Activation and rollback

Migration `20260727_0015` creates the questionnaire and initial equal-weight rule. Migration `20260727_0016` creates and activates a new rule version with effect-size weights. Existing versions and historical results are retained. On a fresh database, the complete migration chain leaves the 12-item questionnaire and effect-size rule active.

To deploy:

```bash
cd backend
alembic upgrade head
```

Rollback of only this release is supported with `alembic downgrade -1`. Perform rollback only under the project's normal database backup and change-control procedure.

## Reproducible survey package

Run:

```bash
python3 scripts/analyze_survey.py
```

This recreates:

- the duplicate-screened n=107 CSV;
- `docs/research_analysis/summary.json`;
- `docs/research_analysis/tables.md`;
- the deep analysis report;
- the Q11–Q22 rationale and weight matrix in Markdown and CSV;
- the preliminary qualitative codebook;
- the methodology distribution, centroid, factor-effect-size, and construct-weight figures.

The script requires Python 3 and Matplotlib for figures. Use `--no-figures` when only the CSV, JSON, and Markdown tables are needed.

## Defensible interpretation

The equal-weight centroid model agrees with the historical methodology used in 73 of 81 cleaned Agile/Traditional cases (90.1%); the effect-size-weighted rule agrees in 74 of 81 (91.4%). This one-case same-sample change is not external accuracy, causal evidence, or proof that the historical method was optimal. Hybrid responses were retained for descriptive analysis but were not used to estimate the two binary centroids.

Before stronger claims are made, complete expert content review, cognitive interviews, a pilot, independent expert labeling, and prospective or held-out evaluation.
