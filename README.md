# Smart Greenhouse

A three-tier Smart Greenhouse application for the XAMK Design Patterns course. It has a FastAPI backend, a PostgreSQL database with Alembic migrations, and a React + TypeScript dashboard, and applies one design pattern per phase (Factory Method, Abstract Factory, Builder, Adapter, Strategy, Facade, State and Decorator so far).

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

The expected revision is `aed8dbcb6b7c` (head). The migration chain is listed in [docs/phases/README.md](docs/phases/README.md).

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

## What the dashboard does

| Section | Phase | What you can do |
| --- | --- | --- |
| Overview | 7 | Pick a location; see assigned device counts, the saved strategy, the recommendation and one card per zone |
| Configuration | 4 | Create, list and delete locations; add, edit and delete zones; see each zone's devices |
| Devices | 3, 4, 8 | Provision a family, place a device in a zone, see and change actuator state |
| Execution log | 9 | See every actuator attempt with its result, policies and message |
| Sensors | 2, 5 | Read now, change the sampling interval and tracking; cards refresh every 5 seconds |
| Automation | 6 | Save a strategy per location and evaluate every zone from its own sensors |

The backend runs a simulation sampler in the background: every tracked `simulation` sensor gets a new reading when its sampling interval has passed. Set `SAMPLER_ENABLED=false` in `.env` to switch it off.
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

See [the phase documentation](docs/phases/README.md) for the phase order, answers, pattern notes and migration chain.

