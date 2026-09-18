# MethodAlign IS Test Execution Report

## Run summary

| Field | Value |
|---|---|
| Execution date | 30 July 2026 |
| Branch | `agent/assessment-workspace-refinement` |
| Base commit at execution | `c20c9dd` plus the uncommitted implementation under review |
| Application runtime | Docker Compose; Node 20 frontend; Python 3.12 backend; PostgreSQL 16 with pgvector |
| External AI calls | 0; controlled test doubles were used |
| Overall result | Pass, with dependency-audit follow-up documented below |

## Results

| Gate | Result | Evidence |
|---|---|---|
| Backend pytest in Python 3.12 container | **Pass** | 48 passed, 1 PostgreSQL-only test skipped; 167 deprecation warnings |
| Backend branch coverage | **Pass** | 75.03% total against a 75% gate |
| Clean PostgreSQL migration integration | **Pass** | 1 passed; empty pgvector/PostgreSQL 16 database migrated to head and seed/config checks succeeded |
| Frontend component tests | **Pass** | 18 passed across 3 files |
| Frontend scoped coverage | **Pass** | 86.27% statements, 79.91% branches, 94.73% functions, 87.12% lines |
| ESLint | **Pass** | 0 errors and 0 warnings after generated-report paths were excluded |
| Next.js production build | **Pass** | Next.js 16.2.12 compiled, type-checked, and generated all routes under Node 20-compatible dependencies |
| Playwright Chromium | **Pass** | 3 passed: participant recommendation, terminal document failure, and mobile layout |
| Docker Compose health | **Pass** | Database, backend, and frontend healthy; both worker processes running |
| Live public Chrome check | **Pass** | Active questionnaire request returned 200; assessment started and advanced; no console warnings/errors |
| Live admin Chrome check | **Pass** | Login and initial admin endpoints returned 200; overview rendered |
| Mobile Chrome check | **Pass** | 412 px viewport had no horizontal overflow (`397 <= 412`) |
| Lighthouse desktop | **Pass** | Accessibility 100, Best Practices 100, SEO 100, Agentic Browsing 100 |
| Lighthouse mobile | **Pass** | Accessibility 100, Best Practices 100, SEO 100, Agentic Browsing 100 |

## Defects discovered and corrected

### Document remains in “processing” after terminal failure

The worker previously set only the job and draft to `failed` when retry attempts were exhausted. The document itself could remain `embedding`, causing the participant UI to poll and display processing indefinitely.

The terminal failure transaction now marks every transient document in that draft as `failed` before the job is saved. Backend and browser regression cases cover both retryable and exhausted failures.

### Public-page secondary text contrast

Chrome Lighthouse identified secondary text at a 4.48:1 contrast ratio, just below the 4.5:1 threshold. The affected assessment header and path labels now use the next darker slate token. Desktop and mobile audits subsequently reached 100 accessibility with zero failed audits.

### Node runtime compatibility

The first test dependency selection included DOM packages requiring Node 22 while the production image and CI contract use Node 20. `jsdom` and `@testing-library/jest-dom` are now pinned to Node 20-compatible releases, and a clean Docker build confirms that dependency installation and production compilation work on the intended runtime.

## Residual risks and follow-up

1. `npm audit --omit=dev` reports three high findings through `next`, `postcss`, and `sharp`. The installed Next.js was upgraded from 16.2.2 to 16.2.12, but npm currently proposes the incompatible downgrade `next@9.3.3` as its automated fix. No forced downgrade was applied. Critical findings are blocked in CI; the high findings should be reviewed again when a compatible patched Next.js release or corrected advisory range is available.
2. The backend suite emits deprecation warnings for `datetime.utcnow()`, FastAPI `on_event`, Pydantic `GenericModel`, and Python's `crypt` path in passlib. They do not fail the current Python 3.12 run, but should be removed before upgrading to Python 3.13/Pydantic 3.
3. Browser end-to-end tests deliberately mock API responses so pull requests remain deterministic and do not consume Gemini quota. The live Chrome acceptance check covers the real Docker API and admin login, but not a paid document-analysis completion. Model-output quality requires a separate, consent-safe evaluation dataset and rubric.
4. The current backend coverage gate is combined coverage. Future work should add per-module thresholds for scoring, authorization, and evidence processing once those modules have a stable test baseline.

## Handover decision

The application is ready for client test execution: all deterministic gates pass, the previously reported indefinite-processing state is regression-tested, the Docker deployment is healthy, and CI will repeat the suite on branch changes that reach a pull request or `main`. Client sign-off should additionally require enabling the four workflow jobs as protected checks and scheduling the dependency/deprecation follow-ups above.
