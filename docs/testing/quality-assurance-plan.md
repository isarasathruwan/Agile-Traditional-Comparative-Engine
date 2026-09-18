# MethodAlign IS Quality Assurance Plan

## Purpose

This plan protects the client-facing decision journey and the research data it produces. A passing suite should give confidence that a participant can submit a valid assessment, receive a reproducible Agile or Traditional recommendation, use optional document evidence safely, and that an administrator can review and export the resulting records.

The automated suite is deterministic. It never calls Gemini or another paid external AI service. AI responses and transient provider failures are replaced with controlled test doubles, while the application-owned database, scoring, validation, authorization, and UI state transitions remain under test.

## Development and release plan

| Phase | Deliverable | Completion rule | Status |
|---|---|---|---|
| 1. Baseline | Inventory existing tests, runtime versions, high-risk journeys, and known document-processing incident | Risks and current checks documented | Complete |
| 2. Backend protection | API contracts, authorization, assessment round trip, document lifecycle, worker retry/failure, advisor state tests | Fast suite passes with at least 75% combined branch coverage | Complete |
| 3. Frontend protection | Input validation, question controls, document states, review editing, and responsive journey tests | Component coverage thresholds and production build pass | Complete |
| 4. Infrastructure protection | Clean PostgreSQL 16 migration, pgvector, single Alembic head, and active seed verification | Empty database reaches head twice without error | Complete |
| 5. Browser acceptance | Desktop participant journey, terminal document failure, mobile overflow, admin login, console/network review, Lighthouse | Chromium journeys pass and no unexpected browser errors remain | Complete |
| 6. Continuous integration | Required checks on pull requests and pushes to `main`, with reports retained | Workflow syntax validates and all jobs are reproducible locally | Complete |
| 7. Handover | Commands, case rationale, results, limitations, and maintenance policy | Client can rerun and interpret every gate | Complete |

## Test layers and meaningful cases

### Backend service and HTTP contract tests

| Case | What it proves | Why it matters |
|---|---|---|
| API-01 Health and request ID | `/health` responds and preserves the request correlation ID | Operations can trace failed requests after handover |
| API-02 Active questionnaire | The active version exposes exactly the expected 12 scored Likert questions | Prevents an accidental questionnaire/config mismatch from changing the research instrument |
| API-03 Assessment round trip | A complete 22-question submission is accepted, scored, versioned, stored, and retrievable | Protects the application's main research outcome |
| API-04 Incomplete submission | Missing Q22 is rejected with a useful error | Prevents incomplete observations entering analysis data |
| API-05 Event validation | Valid session events are recorded and malformed question events are rejected | Protects funnel and completion-rate research metrics |
| AUTH-01 Admin boundary | Missing and invalid tokens are rejected; a valid login returns the authorized operator | Protects participant and document data |
| ADMIN-01 Workspace contracts | Analytics, assessments, rules, questionnaire versions, users, trends, distributions, and CSV export respond under authorization | Protects the complete client administration handover, not only login |
| DOC-01 Participant document lifecycle | Consent, PDF upload, encrypted preview contract, status, evidence/facts, ownership denial, deletion, and explicit processing start work | Exercises the highest-risk optional evidence workflow |
| DOC-02 Transient provider failure | A retryable provider failure requeues the job and retains a processing state | Avoids false permanent failures during short outages |
| DOC-03 Terminal provider failure | The exhausted job, draft, and document all become `failed` atomically | Regression test for the reported “processing forever” defect |
| ADV-01 Traditional advisor success | A queued Traditional result becomes ready using a controlled generated recommendation | Protects the Traditional branch without a live AI dependency |
| ADV-02 Traditional advisor retry | A failed advisor result can return to the queue and finish | Protects operational recovery |
| ADV-03 Advisor validation | Duplicate or unsupported methodology output is rejected | Prevents malformed generated advice being presented as research output |

The broader pre-existing backend suite continues to verify scoring, versioning, evidence influence, research metrics, authorization, encryption, and draft behavior. These cases supplement that suite instead of replacing it.

### PostgreSQL integration test

| Case | What it proves | Why it matters |
|---|---|---|
| DB-01 Clean migration | An empty PostgreSQL 16 database upgrades to the single Alembic head | Detects migrations that only work on a developer's existing database |
| DB-02 Idempotent head | Running `alembic upgrade head` a second time makes no changes and does not fail | Protects repeatable deployment startup |
| DB-03 pgvector and seed data | The `vector` extension, critical tables, active questionnaire, and rule configuration are present | Verifies prerequisites for document retrieval and reproducible scoring |

### Frontend component and validation tests

| Case | What it proves | Why it matters |
|---|---|---|
| UI-01 Human-text validation | Empty, one-character, repeated-character, symbol-heavy, and vowel-less values are rejected; meaningful names and project text pass | Improves the quality of research responses at collection time |
| UI-02 Text question | Error feedback appears and a valid answer is submitted | Protects participant progression and accessible validation |
| UI-03 “Other” choice | A custom option requires meaningful supporting text | Avoids ambiguous categorical data |
| UI-04 Likert lock | One scored answer is recorded and the control locks while advancing | Prevents double submission and score corruption |
| UI-05 Review editing | Stored answers render and the edit action targets the correct question | Allows participants to correct data before final submission |
| UI-06 Consent and PDF upload | Both consents are required, invalid input is rejected, and a valid PDF is uploaded | Protects consent and evidence integrity |
| UI-07 Explicit document batch | Collected documents trigger one explicit processing request | Prevents duplicate AI work and inconsistent states |
| UI-08 Terminal document state | A failed document stops showing as processing and exposes the manual continuation path | Frontend regression protection for the client-reported incident |
| UI-09 Ready evidence | Ready processing advances to evidence review | Protects the successful document branch |

Coverage gates are scoped to decision-critical interactive modules rather than inflated by generated or presentational code. The minimums are 60% statements, 60% lines, 60% functions, and 50% branches. Current coverage is materially above every threshold.

### Chromium end-to-end and live acceptance tests

| Case | What it proves | Why it matters |
|---|---|---|
| E2E-01 Participant recommendation | A participant completes the short mocked questionnaire journey and receives an Agile recommendation; the submitted request body is asserted | Verifies integration between screens, state, request construction, and result rendering |
| E2E-02 Failed evidence | A terminal document failure is displayed as failed instead of processing indefinitely | Browser-level regression for the reported defect |
| E2E-03 Mobile layout | Landing and assessment shell have no horizontal overflow on a Pixel 7 viewport | Keeps the undergraduate participant journey usable on phones |
| LIVE-01 Public production build | The Docker-served page loads its questionnaire with successful network responses and no console errors | Confirms the deployed composition, not only mocked tests |
| LIVE-02 Admin workspace | Default development login reaches overview and all initial API requests return 200 | Confirms the operational handover path |
| LIVE-03 Accessibility | Desktop and mobile Lighthouse accessibility, best-practices, SEO, and agentic-browsing audits pass | Establishes a repeatable browser quality baseline |

## CI policy

The workflow at `.github/workflows/ci.yml` runs on pull requests targeting `main`, pushes to `main`, and manual dispatch. It contains four independently named jobs suitable for branch protection:

- `backend-tests`: Python 3.12, pytest, JUnit, branch coverage, and a 75% gate.
- `frontend-quality`: Node 20, clean `npm ci`, critical vulnerability gate, ESLint, Vitest/JUnit/coverage, TypeScript, and production build.
- `postgres-integration`: PostgreSQL 16 with pgvector, clean and repeated migrations, then the integration marker.
- `browser-e2e`: waits for the other gates, installs only Chromium, and runs the production-build Playwright journeys with one CI worker and retry diagnostics.

Actions are pinned to full commit SHAs, permissions are read-only, duplicate branch runs are cancelled, jobs have timeouts, and reports are retained for 14 days. Configure all four job names as required branch-protection checks before client sign-off.

## Commands

```bash
# Backend fast suite and gate
cd backend
pytest -m "not integration" --junitxml=test-results/backend-junit.xml \
  --cov=app --cov-branch --cov-report=term --cov-report=xml:coverage.xml \
  --cov-report=html:htmlcov --cov-fail-under=75

# PostgreSQL integration (after providing a clean PostgreSQL/pgvector database)
RUN_POSTGRES_TESTS=1 pytest -m integration

# Frontend quality
cd ../frontend
npm ci
npm audit --audit-level=critical
npm run lint
npm run test:coverage
npm run build

# Chromium journeys
npx playwright install chromium
CI=true npm run test:e2e
```

## Maintenance rules

- Every scoring or questionnaire change must add or update a deterministic expected-result case and preserve the stored rule/questionnaire version assertions.
- Every production defect must first be reproduced by a failing automated case, then fixed until that case passes.
- Do not place live AI calls in pull-request CI. Evaluate model quality separately with a versioned, consent-safe dataset and a recorded rubric.
- Raise coverage thresholds gradually as new decision-critical modules gain tests; do not lower a gate simply to merge a change.
- Review dependency audit findings on every dependency update. Critical findings block CI; lower-severity findings require triage because automated downgrade suggestions can be incompatible.
- Keep JUnit, coverage, trace, screenshot, and video artifacts free of participant documents and secrets.
