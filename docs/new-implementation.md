# Development Plan: Company Grouping, Input Validation, and OCR RAG

## Summary

Build three scoped upgrades:

- Add an admin-only grouped company view for assessment submissions.
- Add balanced frontend and backend validation to reduce junk profile input.
- Add optional public-user document upload before scoring, with OCR + RAG enrichment using PostgreSQL/pgvector and Google AI Studio for LLM/embeddings.

Core Agile/Traditional scoring remains deterministic. RAG evidence enriches the final report with citations, risks, and supporting context; it does not change numeric rule scores in v1.

## Key Changes

### 1. Admin Company Grouping

- Extend admin assessments API with `group_by=company`.
- Return grouped records shaped like:
  - `company`
  - `normalized_company`
  - `submission_count`
  - `latest_submission_at`
  - `agile_count`
  - `traditional_count`
  - `avg_agile_score`
  - `avg_traditional_score`
  - `items`
- Normalize company names on submission using trimmed lowercase, whitespace collapse, and punctuation cleanup.
- Add admin UI toggle: `List view` / `Grouped by company`.
- Preserve existing search, sort, pagination, CSV export, and detail drilldown.

### 2. Balanced User Input Validation

- Add Pydantic validation to assessment profile fields:
  - required non-empty strings
  - min/max lengths
  - trim whitespace
  - reject repeated-character junk like `aaaaaaa`
  - reject mostly-symbol input
  - enforce pill-option values where questionnaire options exist
- Add matching frontend validation in the public assessment flow:
  - disable continue on invalid input
  - show short inline validation messages
  - trim values before submit
- Keep validation balanced: avoid overly strict company/project-name rules that could reject real users.

### 3. Public Document Upload + OCR/RAG

- Add an optional document-upload step before final scoring.
- Support v1 file types: PDF, PNG, JPG, JPEG, TIFF.
- Keep original files with the submission for admin review.
- Add upload limits:
  - max files per submission: 5
  - max file size: 10 MB each
  - max OCR pages/images per submission: 30
- Use async processing:
  - create assessment draft/session
  - upload documents
  - process OCR/chunking/embedding in background
  - allow final scoring only when document status is `ready`, `failed`, or user skips documents
- OCR provider policy:
  - `auto`: use Google Cloud Vision OCR only while configured and within app-tracked free monthly unit limit; otherwise fallback to local OCR
  - `local`: use local extraction/OCR only
  - `vision`: force Google Cloud Vision OCR
- Use Google AI Studio via `google-genai`:
  - embeddings: `gemini-embedding-001`
  - generation: `gemini-2.5-flash`
- Add PostgreSQL vector support with `pgvector`.
- Replace current DB image with a pgvector-enabled Postgres image or custom Postgres image.
- Add document tables:
  - `assessment_drafts`
  - `assessment_documents`
  - `document_chunks`
  - `ocr_usage_monthly`
- Add RAG output into `decision_report.document_evidence`:
  - cited excerpts
  - source document/page
  - confidence notes
  - document-derived risk observations
- Do not feed untrusted document text directly into score calculation in v1.

## Public APIs / Interfaces

- `POST /api/v1/assessment-drafts`
  - creates a temporary public assessment draft/session.
- `POST /api/v1/assessment-drafts/{draft_id}/documents`
  - multipart upload for allowed files.
- `GET /api/v1/assessment-drafts/{draft_id}/documents/status`
  - returns per-file processing status.
- `POST /api/v1/assessments`
  - accepts optional `draft_id`; if present, attaches processed document evidence to the final submission/result.
- `GET /api/v1/admin/assessments?group_by=company`
  - returns grouped company data.
- `GET /api/v1/admin/assessments/{submission_id}/documents`
  - lists stored documents and processing metadata for admins.
- `GET /api/v1/admin/assessments/{submission_id}/documents/{document_id}/download`
  - admin-only original file download.

New environment variables:

- `GOOGLE_AI_API_KEY`
- `GOOGLE_GENAI_MODEL=gemini-2.5-flash`
- `GOOGLE_EMBEDDING_MODEL=gemini-embedding-001`
- `OCR_PROVIDER=auto`
- `GOOGLE_CLOUD_VISION_ENABLED=false`
- `GOOGLE_APPLICATION_CREDENTIALS`
- `VISION_FREE_UNIT_LIMIT=1000`
- `MAX_UPLOAD_FILE_MB=10`
- `MAX_UPLOAD_FILES=5`
- `MAX_UPLOAD_PAGES=30`

## Test Plan

- Backend unit tests:
  - profile validation accepts normal values and rejects junk input
  - company normalization groups equivalent company names
  - grouped admin response totals are correct
  - document upload rejects unsupported type, oversized file, and too many files
  - failed OCR does not block scoring if user skips document evidence
- Backend integration tests:
  - pgvector migration creates extension and vector index
  - chunk retrieval orders by cosine similarity
  - RAG report includes citations without changing rule scores
- Frontend tests/checks:
  - invalid text input blocks continue
  - document upload step shows pending/ready/failed states
  - grouped admin view expands company rows and opens assessment detail
- Manual acceptance:
  - submit two assessments with same company spelling variations and verify grouped admin view
  - upload a scanned PDF and verify OCR text appears as cited evidence
  - run with Vision disabled and verify local OCR fallback works
  - run with Vision enabled and monthly limit reached, then verify fallback to local OCR

## Assumptions

- Company grouping is admin-only.
- Uploads are from public assessment users.
- Upload happens before scoring.
- Original files are retained with the submission for admin review.
- RAG enriches explanations only; it does not alter deterministic rule scores in v1.
- PDF + image support is enough for v1 unless revised.
- Google Cloud Vision OCR has a free monthly tier for the first 1,000 units, while Document AI OCR is priced per page, so Vision + local fallback is the default OCR plan.
- References used: [Google Gen AI Python SDK](https://github.com/googleapis/python-genai), [pgvector Python](https://github.com/pgvector/pgvector-python), [Cloud Vision pricing](https://cloud.google.com/vision/pricing), [Document AI pricing](https://cloud.google.com/document-ai/pricing).
