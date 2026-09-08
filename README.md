# Smart Greenhouse

A three-tier Smart Greenhouse application for the XAMK Design Patterns course. Phase 1 establishes a runnable FastAPI backend, PostgreSQL database with Alembic migrations, and a React + TypeScript dashboard shell.

## Stack

- Python 3.11+
- FastAPI, SQLAlchemy 2, Alembic, and psycopg
- PostgreSQL 16 through Docker Compose
- React, TypeScript, Vite, Tailwind CSS v4, and React Router
- Scalar API reference

## Prerequisites

Install Python 3.11+, Node.js 20 LTS+, Docker Desktop, and Git. Verify them with:

```powershell
python --version
node --version
docker --version
git --version
```

## First-time setup

Run these commands from the repository root.

### 1. Create local environment settings

```powershell
Copy-Item .env.example .env
```

The `.env` file contains local credentials and is intentionally ignored by Git.

### 2. Start PostgreSQL

```powershell
docker compose up -d
docker compose ps
```

Wait until `greenhouse-postgres` reports `healthy`.

### 3. Install the backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 4. Apply the Alembic baseline migration

From `backend/`, with the virtual environment activated:

```powershell
alembic upgrade head
alembic current
```

The expected revision is `001`. Phase 1 creates no business tables; `alembic_version` is the only database table.

### 5. Install the frontend

Open a new terminal at the repository root:

```powershell
cd frontend
npm install
```

The frontend reads its backend URL from `frontend/.env.example`. Copy it to `.env` only when you need local overrides:

```powershell
Copy-Item .env.example .env
```

## Daily start

Use three terminals.

### Terminal 1 — database

```powershell
docker compose up -d
```

### Terminal 2 — backend API

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
cd src
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 3 — frontend

```powershell
cd frontend
npm run dev
```

## URLs

| Service | URL |
| --- | --- |
| API root | http://localhost:8000/ |
| Health endpoint | http://localhost:8000/health |
| Scalar API reference | http://localhost:8000/scalar |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| Frontend dashboard | http://localhost:5173/dashboard |

Swagger UI is deliberately disabled at `/docs`; use Scalar at `/scalar` instead.

## Testing and quality checks

Run the optional health smoke test from `backend/`:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "src"
python -m pytest tests -q
```

Run Python linting:

```powershell
.\.venv\Scripts\ruff.exe check src tests
```

Build the frontend from `frontend/`:

```powershell
npm run build
```

## Project structure

```text
backend/
  src/
    domain/             # Business concepts and pattern abstractions
    application/        # Use cases and orchestration
    infrastructure/     # Settings, database, and external adapters
    interfaces/api/     # FastAPI routes and HTTP wiring
  alembic/              # Database migration history
  tests/                # Backend tests
frontend/
  src/
    components/         # Shared UI components
    pages/              # Routed pages
    services/           # API client functions
docs/phases/            # Phase notes and answers


```
## Course phases

See [the phase documentation](docs/phases/README.md) for the Phase 1 answers and future phase notes.

