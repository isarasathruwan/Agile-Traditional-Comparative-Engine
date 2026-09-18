# Backend Service (Pattern-Aligned)

FastAPI backend for MethodAlign IS using strict layered architecture:
`controller -> service -> repository -> entity` with shared config, exception handlers, and response envelope contracts.

## Local Development

### Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Run

```bash
uvicorn main:app --reload --port 8000
```

Health check: `GET /health`

### Migrations

```bash
alembic upgrade head
alembic downgrade -1
```

## Docker Deployment

The backend is containerized and runs via the root `docker-compose.yml`. **No local Python required** — the build happens entirely inside Docker.

```bash
# From project root — starts database, backend, two workers, and frontend
docker compose up -d --build
```

The backend container automatically:
1. Waits for the database to be ready
2. Runs `alembic upgrade head` (creates tables & seeds initial data)
3. Starts the FastAPI server

### Container Details

- **Image:** `python:3.12-slim`
- **Port:** 8000
- **User:** `app` (non-root)
- **Entrypoint:** `entrypoint.sh`

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `db` | PostgreSQL host (use `db` in Docker, `localhost` locally) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `postgres` | Database user |
| `POSTGRES_PASSWORD` | `postgres` | Database password |
| `POSTGRES_DB` | `methodalign` | Database name |
| `JWT_SECRET` | — | JWT signing secret (required) |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `JWT_EXP_MINUTES` | `480` | Token expiry in minutes |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Allowed frontend origins |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DOCUMENT_ENCRYPTION_KEY_BASE64` | — | Required 32-byte Base64 key for encrypted document data |
| `GEMINI_API_KEY` | — | Enables optional document analysis and Traditional sub-method advice |

For Docker, configure both the root `.env` and `backend/.env` as described in the [deployment guide](../DEPLOY.md). Keep the same valid encryption key in both files. Compose-level security values come from the root file, while the Gemini key is read from `backend/.env`.

## Default Local Admin

- Email: `admin@methodalign.local`
- Password: `admin123`
- Role: `super_admin`

## RBAC (Admin API)

- Permissions are enforced per endpoint via route dependencies.
- Current built-in roles:
  - `super_admin`: full access (bypass)
  - `analyst`: analytics/research/read/export
  - `config_editor`: rules/questionnaire management + analytics read

## Admin User Management API

- `GET /api/v1/admin/users` -> list admin users
- `POST /api/v1/admin/users` -> create admin user (`email`, `password`, `role`)
- `PUT /api/v1/admin/users/{user_id}` -> update admin user (`role`, `is_active`)

## Response Contract

All JSON APIs return:

```json
{
  "status_code": 200,
  "success": true,
  "message": "Operation successful.",
  "error_code": null,
  "data": {}
}
```

Paginated endpoints additionally include:

```json
{
  "page": 1,
  "page_size": 20,
  "total_records": 100,
  "total_pages": 5
}
```

## Request ID + Auth Middleware

- Every request gets `X-Request-ID` (input preserved or generated).
- Request ID is included in response headers and log lines.
- JWT auth is enforced globally except whitelisted paths from `AUTH_WHITELIST_PATHS`.

## CORS

- Configure allowed frontend origins with `CORS_ALLOWED_ORIGINS` (comma-separated).
- Local default:
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
- `OPTIONS` preflight requests are passed through auth middleware.
