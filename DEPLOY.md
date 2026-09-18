# MethodAlign IS Local Deployment And Operations Guide

This guide covers the delivered Windows/Docker Desktop installation. The application is intended to run locally for research and demonstration. The optional Nginx configuration is not a complete public-production security solution.

For a beginner-friendly codebase explanation and visual system walkthrough, use the [Codebase and Application Handover Guide](docs/codebase-and-application-handover.md).

## 1. Daily Start And Stop

Open PowerShell in the project folder after Docker Desktop is running.

```powershell
# Start or resume the application
docker compose up -d

# Confirm all five services are running
docker compose ps
```

Expected access points:

| Purpose | Address |
| --- | --- |
| Participant assessment | <http://localhost:3000> |
| Administrator workspace | <http://localhost:3000/admin> |
| Backend API | <http://localhost:8000> |
| Interactive API reference | <http://localhost:8000/docs> |
| Health check | <http://localhost:8000/health> |

Stop while preserving the database and uploaded documents:

```powershell
docker compose stop
```

## 2. Fresh Installation On Windows

### Requirements

- Windows 10 or 11.
- Docker Desktop with the WSL 2 engine enabled.
- A modern web browser.
- A Gemini API key owned by the student if document analysis is required.

No local Node.js or Python installation is required for the Docker workflow.

### Create The Environment Files

The current Compose file reads both a root environment file and a backend environment file.

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
```

Generate a 32-byte encryption key:

```powershell
$keyBytes = New-Object byte[] 32
$keyGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
$keyGenerator.GetBytes($keyBytes)
[Convert]::ToBase64String($keyBytes)
$keyGenerator.Dispose()
```

Copy the output into `DOCUMENT_ENCRYPTION_KEY_BASE64` in both files. Use the same value. Also replace `JWT_SECRET` in both files with a long, unique random value.

> Keep secure backups of these environment files. Losing the encryption key makes stored documents, extracted page text, chunks, citations, and extracted facts unreadable.

### Configure Gemini

Create a student-owned key in [Google AI Studio](https://aistudio.google.com/apikey), restrict it to the Gemini API, and place it only in `backend/.env`:

```dotenv
GEMINI_API_KEY=replace-with-the-student-owned-key
GEMINI_GENERATION_MODEL=gemini-3.5-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-2
GEMINI_EMBEDDING_DIMENSIONS=768
```

The 768-dimensional embedding setting is fixed by the current database schema. Do not change it without a matching application/database migration.

The questionnaire remains available if no Gemini key is configured, but document evidence and generated Traditional sub-method advice cannot complete.

### Build And Start

```powershell
docker compose up -d --build
docker compose ps
```

The backend waits for PostgreSQL, runs `alembic upgrade head`, and then starts the API. Initial migrations seed the questionnaire, rule configuration, and local administrator account.

Default local login:

- Email: `admin@methodalign.local`
- Password: `admin123`

Create a new super administrator and deactivate the default account before storing important assessment data.

## 3. Services

| Service | Base image/runtime | Function | Exposed port |
| --- | --- | --- | --- |
| `db` | `pgvector/pgvector:pg16` | PostgreSQL database and vector search | Host `5433` → container `5432` |
| `backend` | Python 3.12 / FastAPI | API, authentication, scoring, administration | `8000` |
| `document-worker` | Python 3.12 | PDF extraction, embeddings, retrieval, and evidence suggestions | None |
| `traditional-advisor-worker` | Python 3.12 | Traditional sub-method recommendation jobs | None |
| `frontend` | Node 20 / Next.js 16 | Participant and administrator user interfaces | `3000` |
| `nginx` | Nginx Alpine | Optional single HTTP entry point | `80` |

## 4. Environment Variables

| Variable | Main source | Meaning |
| --- | --- | --- |
| `JWT_SECRET` | Root `.env` | Administrator-token signing secret. |
| `JWT_EXP_MINUTES` | Compose/default | Administrator token lifetime; currently 480 minutes. |
| `CORS_ALLOWED_ORIGINS` | Root `.env` | Comma-separated browser origins allowed by the API. |
| `NEXT_PUBLIC_API_BASE_URL` | Root `.env` | Browser-facing API address; normally `http://localhost:8000`. |
| `ASSESSMENT_DOCUMENTS_DIR` | Root `.env` | Container path backed by the document volume. |
| `DOCUMENT_ENCRYPTION_KEY_BASE64` | Root `.env` | Required Base64 value that decodes to exactly 32 bytes. |
| `DOCUMENT_ENCRYPTION_KEY_VERSION` | Root `.env` | Identifier stored with encrypted records; currently `v1`. |
| `PARTICIPANT_COOKIE_SECURE` | Root `.env` | `false` for local HTTP; `true` only when served through HTTPS. |
| `GEMINI_API_KEY` | `backend/.env` | Credential used by the two background workers. |
| `GEMINI_GENERATION_MODEL` | Both/examples | Model used for evidence extraction and advice. |
| `GEMINI_EMBEDDING_MODEL` | Both/examples | Model used to create document embeddings. |
| `GEMINI_EMBEDDING_DIMENSIONS` | Both/examples | Must remain `768` for the delivered schema. |
| `DOCUMENT_WORKER_RETRY_LIMIT` | Both/examples | Maximum attempts for document-processing jobs. |
| `TRADITIONAL_ADVISOR_RETRY_LIMIT` | Both/examples | Maximum attempts for advisor jobs. |

Do not commit `.env` or `backend/.env`. Do not put API keys or encryption keys in screenshots, issue trackers, or the handover manual.

## 5. Routine Operations

```powershell
# Status and health
docker compose ps
Invoke-RestMethod http://localhost:8000/health

# Last 100 log lines from every service
docker compose logs --tail 100

# Follow a specific service
docker compose logs -f backend
docker compose logs -f document-worker
docker compose logs -f traditional-advisor-worker

# Restart all services without deleting data
docker compose restart

# Rebuild after receiving source changes
docker compose up -d --build

# Apply pending migrations manually
docker compose exec backend alembic upgrade head

# View migration history
docker compose exec backend alembic history
```

## 6. Data Persistence

Two Docker named volumes retain state:

- `postgres_data`: users, assessments, results, versions, traces, and document metadata.
- `assessment_documents`: encrypted original PDF files.

`docker compose stop`, `restart`, and `down` retain these volumes. `docker compose down -v` deletes both.

### Database Backup

```powershell
New-Item -ItemType Directory -Force backups
docker compose exec db pg_dump -U postgres -d methodalign -Fc -f /tmp/methodalign-db.dump
docker compose cp db:/tmp/methodalign-db.dump .\backups\methodalign-db.dump
```

### Encrypted Document Backup

```powershell
docker compose exec backend tar -czf /tmp/assessment-documents.tar.gz -C /var/lib/methodalign/documents .
docker compose cp backend:/tmp/assessment-documents.tar.gz .\backups\assessment-documents.tar.gz
```

Copy `.env` and `backend/.env` separately to an access-controlled secret store. Do not add those copies to the normal handover archive. A document backup without the matching encryption key cannot be decrypted.

### Restore Rehearsal

Restore only into a controlled test installation first. The following database step replaces the target database.

```powershell
docker compose stop frontend backend document-worker traditional-advisor-worker
docker compose up -d db
docker compose cp .\backups\methodalign-db.dump db:/tmp/methodalign-db.dump

# DESTRUCTIVE: replace the target database
docker compose exec db dropdb -U postgres --if-exists --force methodalign
docker compose exec db createdb -U postgres methodalign
docker compose exec db pg_restore -U postgres -d methodalign --clean --if-exists /tmp/methodalign-db.dump

docker compose up -d backend
docker compose cp .\backups\assessment-documents.tar.gz backend:/tmp/assessment-documents.tar.gz
docker compose exec backend tar -xzf /tmp/assessment-documents.tar.gz -C /var/lib/methodalign/documents
docker compose up -d
```

Restore the matching environment secrets before opening an encrypted document. Confirm the health endpoint, administrator login, one historical assessment, and one document preview after recovery.

## 7. Troubleshooting

| Symptom | Check | Action |
| --- | --- | --- |
| `docker` is not recognized | Docker Desktop installation and terminal restart | Start Docker Desktop, then reopen PowerShell. |
| Docker daemon connection error | Docker Desktop status | Wait until Docker reports that the engine is running. |
| Backend repeatedly restarts | `docker compose logs backend` | Correct missing/invalid environment values, especially the encryption key. |
| Port already allocated | Ports 3000, 8000, or 5433 | Stop the conflicting program; avoid changing repository configuration unless ownership approves it. |
| Frontend opens but API calls fail | <http://localhost:8000/health> and backend logs | Restart backend and confirm `NEXT_PUBLIC_API_BASE_URL`. Rebuild frontend after changing that variable. |
| PDF upload is rejected | File type, file size, consent, and PDF text | Use a selectable-text PDF under 10 MB; maximum five per assessment. Scanned/image-only PDFs are unsupported. |
| Document remains failed | Worker logs and Gemini key/quota | Correct the key/quota issue, then use the available retry or continue manually. |
| Traditional advice does not appear | Final outcome and advisor worker logs | It applies only to Traditional results and requires a working Gemini key. |
| Administrator login fails | Correct account, active status, and backend health | Try the verified replacement admin; use the default only on an unchanged local seed. |
| Uploaded documents cannot be opened after restore | Encryption-key version and value | Restore the exact key used when the documents were encrypted. |

## 8. Intentional Clean Reset

This operation permanently deletes local application data and uploaded documents:

```powershell
# DESTRUCTIVE — verify backups first
docker compose down -v
docker compose up -d --build
```

Migrations recreate the schema and seeded defaults, but deleted assessments and documents are not recoverable without backups.

## 9. Optional Nginx Demonstration Entry Point

Set this value in root `.env`:

```dotenv
NEXT_PUBLIC_API_BASE_URL=/api
```

Then rebuild using the override:

```powershell
docker compose -f docker-compose.yml -f docker-compose.nginx.yml up -d --build
```

Open <http://localhost>. Nginx proxies `/api`, `/docs`, and `/openapi.json` to the backend and other traffic to the frontend.

This remains HTTP-only. Public internet deployment additionally requires TLS, non-default database credentials, restricted port exposure, secure secret management, firewall/access rules, monitoring, tested backups, and an approved privacy/retention policy.
