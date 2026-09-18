# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MethodAlign IS** — a Deterministic Rule-Engine Decision-Support Dashboard that helps organizations select between Agile and Traditional project management methodologies for Information Systems development. This is an academic artefact built under Design Science Research (DSR) methodology.

## Stack

- **Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts
- **Backend:** Python, FastAPI — deterministic rule engine, statistical computations (averages, correlations, composite scores)
- **Database:** PostgreSQL via Docker
- **Auth:** None (public tool — Phase 1)
- **Repo structure:** Monorepo — `/frontend` and `/backend`

## Architecture

The core architectural decision is a **deterministic rule engine**, not AI or LLM. This is intentional and must not be changed — it guarantees transparency, data privacy, and predictable outputs required for academic rigor and IS security environments (government, banking, healthcare).

Data flow:
1. User rates project constraints via a structured questionnaire (Likert 1–5 scale)
2. Inputs are grouped into three constructs: **Flexibility** (adaptability/human factors), **Performance** (time/budget), **Strictness** (security/integration)
3. Python engine computes aggregated composite scores per construct using descriptive/inferential statistics
4. Scores are compared against empirical baseline weights derived from survey data
5. Dashboard renders comparative charts and outputs a methodology recommendation

The seven dependent variables the engine evaluates:
- Timeline Adherence
- Budget Accuracy
- Product Quality
- User Satisfaction
- Communication Effectiveness
- Security Integration
- System Integration Effectiveness

Statistical methods used in the engine: independent sample t-tests, Cronbach's Alpha reliability assessment, normalization across scale variations.

Recommendation logic:
- **Agile** → dynamic IS projects with flexible requirements
- **Traditional** → security-sensitive, compliance-driven, or integration-heavy environments

## Development Commands

```bash
# Frontend (Next.js)
cd frontend
npm install
npm run dev          # development server → http://localhost:3000
npm run build        # production build
npm run lint         # ESLint

# Backend (FastAPI)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload   # dev server → http://localhost:8000
python -m pytest            # run all tests
python -m pytest tests/test_engine.py  # single test file

# Database (Docker)
docker compose up -d         # start PostgreSQL
docker compose down          # stop
```

## Research Context

The NotebookLM notebook **"Evaluating Agile and Traditional Methodologies in Information Systems Development"** (notebook ID: `b20688b9-cc79-4534-882a-fc1ed60f8873`) contains the research proposal, survey instrument design, conceptual framework, and all domain logic. Query it for clarification on scoring weights, hypotheses (H1–H5), or variable definitions before making engine logic decisions.

## Development Workflow

### Orchestration Model
Claude Code acts as **orchestrator and senior developer**. Codex CLI is directed to handle implementation tasks. Claude Code intervenes directly for bug fixes, complex logic, and architectural decisions.

### NotebookLM Feature Logging (Required)
After every feature is implemented and verified, log it to the NotebookLM notebook above using the `notebooklm-mcp` tool:

```
mcp: notebooklm-mcp → note (add)
notebook_id: b20688b9-cc79-4534-882a-fc1ed60f8873
content: [Feature name] — [brief description of what was built, key files/modules, and any domain decisions made]
```

This keeps the research notebook in sync with the implementation and provides an audit trail for the DSR artefact evaluation.