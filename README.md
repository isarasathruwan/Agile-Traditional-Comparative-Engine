# MethodAlign IS — Agile vs Traditional Comparative Engine

MethodAlign IS is an explainable decision-support application for comparing the fit of Agile and Traditional delivery approaches for information-systems projects. It combines a structured questionnaire, optional document evidence, transparent scoring rules, and an administrator workspace.

> **Research boundary:** The result supports human judgment. It does not guarantee project success and should not be presented as a statistically validated predictor.

## Start With The Handover Manual

The [MethodAlign IS Codebase and Application Handover Guide](docs/codebase-and-application-handover.md) is the main guide for a new project owner. Its code-first walkthrough explains the technology stack, repository folders, frontend, backend layers, assessment/scoring flow, database, AI workers, access control, and Docker runtime with diagrams and annotated excerpts. It then links to the detailed operation, administrator, calculation, and testing references.

Detailed supporting references are indexed in [the documentation index](docs/admin-dashboard-documentation-index.md).

## Local Docker Architecture

The normal local installation runs five containers. Nginx is an optional sixth container.

| Service | Purpose | Host access |
| --- | --- | --- |
| `frontend` | Next.js 16 participant and administrator interface | `http://localhost:3000` |
| `backend` | FastAPI rules, access control, and data API | `http://localhost:8000` |
| `db` | PostgreSQL 16 with pgvector | Port `5433` |
| `document-worker` | Optional PDF extraction, embeddings, and evidence matching | Internal only |
| `traditional-advisor-worker` | Optional Traditional sub-method advice | Internal only |
| `nginx` | Optional single HTTP entry point | `http://localhost` |

## Existing Windows Installation

1. Start Docker Desktop and wait until it reports that Docker is running.
2. Open PowerShell in the project folder.
3. Start or resume the application:

   ```powershell
   docker compose up -d
   docker compose ps
   ```

4. Open:

   - Assessment: <http://localhost:3000>
   - Admin workspace: <http://localhost:3000/admin>
   - Backend health: <http://localhost:8000/health>

To stop the containers without deleting data:

```powershell
docker compose stop
```

## Fresh Windows Setup

Docker Desktop is the only runtime prerequisite. The repository currently uses two environment files: the root file for Compose-level settings and `backend/.env` for backend/worker settings.

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
```

Before starting, edit both files:

1. Replace `JWT_SECRET` with a long random value.
2. Generate one 32-byte encryption key and place the same Base64 value in `DOCUMENT_ENCRYPTION_KEY_BASE64` in both files:

   ```powershell
   $keyBytes = New-Object byte[] 32
   $keyGenerator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
   $keyGenerator.GetBytes($keyBytes)
   [Convert]::ToBase64String($keyBytes)
   $keyGenerator.Dispose()
   ```

3. Add the student's own `GEMINI_API_KEY` to `backend/.env` to enable document analysis and Traditional sub-method advice. The core questionnaire works without it.
4. Never commit either environment file or share its values in screenshots or general documentation.

Then build and start the stack:

```powershell
docker compose up -d --build
docker compose ps
```

The first startup applies all database migrations and seeds the active questionnaire, active rules, and local administrator account.

### Default Local Administrator

- Email: `admin@methodalign.local`
- Password: `admin123`

These credentials are for local development and demonstration only. Create a replacement super administrator in **Advanced tools → Users**, verify the new login, and deactivate the default account when the installation contains important data.

## Environment Responsibilities

| Setting | File | Purpose |
| --- | --- | --- |
| `JWT_SECRET` | Both | Signs administrator login tokens. |
| `DOCUMENT_ENCRYPTION_KEY_BASE64` | Both | Encrypts uploaded files and extracted evidence. Losing it makes existing document data unreadable. |
| `GEMINI_API_KEY` | `backend/.env` | Enables optional Google AI document features. |
| `CORS_ALLOWED_ORIGINS` | Root `.env` | Lists browser origins allowed to call the backend. |
| `NEXT_PUBLIC_API_BASE_URL` | Root `.env` | Selects the browser-facing backend URL. |
| `PARTICIPANT_COOKIE_SECURE` | Root `.env` | Should be `false` for local HTTP and `true` only behind HTTPS. |

See [DEPLOY.md](DEPLOY.md) for the complete variable list, backup/recovery procedures, logs, and troubleshooting.

## Project Structure

```text
backend/                 FastAPI API, business services, persistence, migrations, and workers
frontend/                Next.js pages, components, API clients, tests, and browser journeys
docs/                    Handover, administration, scoring, research, and test documentation
nginx/                   Optional HTTP reverse-proxy configuration
docker-compose.yml       Five-service local stack
docker-compose.nginx.yml Optional Nginx override
DEPLOY.md                Detailed operating and recovery guide
```

The backend follows `controller → service → repository → entity`. The frontend uses Next.js App Router pages with reusable components and API helpers.

## Safe Operating Commands

```powershell
# Status
docker compose ps

# Recent logs
docker compose logs --tail 100

# Follow one service
docker compose logs -f backend

# Restart without deleting data
docker compose restart

# Stop and remove containers, but retain named volumes
docker compose down

# Apply migrations manually
docker compose exec backend alembic upgrade head
```

> **Data-loss warning:** `docker compose down -v` deletes the PostgreSQL and uploaded-document volumes. Use it only for an intentional clean reset after confirming backups are usable.

## Quality Checks

```bash
# Backend unit/API tests and coverage gate
cd backend
pip install -r requirements-dev.txt
pytest -m "not integration" --cov=app --cov-branch --cov-fail-under=75

# Frontend lint, component tests, coverage, and production build
cd ../frontend
npm ci
npm run lint
npm run test:coverage
npm run build

# Production-build Chromium journeys
npx playwright install chromium
npm run test:e2e
```

See the [quality assurance plan](docs/testing/quality-assurance-plan.md) and [latest execution report](docs/testing/test-execution-report.md) for coverage and residual risks.

## Optional Nginx Setup

The Nginx override provides a single HTTP entry point for a controlled local demonstration:

```powershell
# Set NEXT_PUBLIC_API_BASE_URL=/api in .env first
docker compose -f docker-compose.yml -f docker-compose.nginx.yml up -d --build
```

This configuration is HTTP-only. It is not, by itself, a complete internet-production deployment; public hosting also requires TLS, secure credentials, restricted database exposure, backups, monitoring, access policy, and an approved data-retention process.

## Local Development Without Docker

- [Backend development](backend/README.md)
- [Frontend development](frontend/README.md)
