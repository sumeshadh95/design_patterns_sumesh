# Phase 1 — Skeleton questions and answers

**Pattern / focus:** Course introduction and an empty-but-running three-tier skeleton. No GoF pattern is implemented in this phase.

## A. Pattern

### 1. What is a design pattern? What is it not?

A design pattern is a named, reusable approach to a recurring software-design problem. It gives developers a shared way to discuss a design and helps separate code that is stable from behaviour likely to change. It is not a library to install, a finished piece of code to copy, or extra classes added only because a pattern has a name.

### 2. What are the three GoF pattern families? Where do Factory Method and Strategy belong?

- **Creational patterns** address how objects are created without coupling all callers to concrete constructors. **Factory Method** is creational.
- **Structural patterns** address how classes and objects are composed so their responsibilities and interfaces fit together cleanly.
- **Behavioral patterns** address how objects collaborate and how behaviour can vary. **Strategy** is behavioral.

### 3. When should a pattern be skipped? What is the risk of applying one too early?

A pattern should be skipped when a feature is small, unlikely to change, and a simple function or class solves the problem clearly. Applying a pattern too early adds indirection, more files, and more concepts for a developer to understand. This makes the code harder to maintain without solving a real problem.

## B. This phase of the application

### 4. Why does Phase 1 ship a vertical slice with almost no greenhouse business logic?

Phase 1 verifies the whole stack instead of only proving that folders exist. It shows that PostgreSQL starts, Alembic can connect and migrate, FastAPI can serve an endpoint, the frontend can call the API, and the dashboard can display the result. A folder of unimplemented classes cannot prove configuration, imports, networking, database connectivity, or startup instructions work together.

### 5. What belongs in each backend layer?

- **`domain`** contains business concepts, entities, and later pattern abstractions. A future `Sensor` business concept belongs here.
- **`application`** contains use cases and orchestration. A future service that coordinates sensor operations belongs here.
- **`infrastructure`** contains technical details, including settings, SQLAlchemy database access, repositories, and external adapters.
- **`interfaces/api`** contains FastAPI routes and HTTP request/response wiring, such as the `GET /health` route.

FastAPI route functions, SQLAlchemy sessions and models, database connection code, and HTTP Pydantic schemas must not live in `domain`. Domain code should express greenhouse rules rather than depend on a web framework or a database library.

### 6. What does `GET /health` return? Why check the database? Why Scalar and not `/docs`?

When the database is reachable, `GET /health` returns `{"status": "ok", "db": "ok"}`. If the database cannot be reached, it returns `{"status": "degraded", "db": "fail"}`. Checking the database is important because the FastAPI process can be running while the application cannot store or retrieve data.

Scalar is available at `/scalar` as the project’s interactive API reference and shared OpenAPI contract. The built-in Swagger UI at `/docs` is disabled so the project uses one intended documentation interface.

### 7. Why introduce a baseline migration before business tables exist?

Alembic is introduced early so the project starts with a version-controlled and repeatable process for changing the database schema. The empty baseline proves that migrations can connect to PostgreSQL and records the initial schema state. Creating tables manually first would make developer databases inconsistent, lose migration history, and make it difficult to add a trustworthy first migration later.

## C. Compare, contrast, and scenarios

### 8. Explain dependency direction in this skeleton.

Dependencies should flow inward. The API layer can call application code; application code can use domain abstractions and coordinate infrastructure; infrastructure implements technical details such as database access. The domain layer should be the most independent layer.

Domain code must not import FastAPI, SQLAlchemy, or Pydantic models used as HTTP schemas. Otherwise, greenhouse rules become coupled to the selected web and database technologies, which makes the rules harder to test, reuse, or change.

### 9. The frontend health badge is not healthy. What should be checked first?

First, check that Docker Compose shows PostgreSQL as healthy and that the backend is running. Next, open `GET /health` directly and confirm that it returns the required JSON. Then inspect the browser network request and verify the frontend API base URL, Vite proxy configuration if used, and CORS configuration.

This is a Phase 1 concern because it is a stack integration and configuration issue. It must work before later phases add design patterns or more greenhouse behaviour.

### 10. What is missing after Phase 1, and how can later phases grow without rewriting the foundation?

After Phase 1, the project still lacks devices, sensors, actuators, locations, automation logic, richer API endpoints, WebSockets, and schema hardening. Later phases can add each feature in its appropriate layer: business concepts and patterns in `domain`, use cases in `application`, persistence and adapters in `infrastructure`, and HTTP endpoints in `interfaces/api`. This preserves the Phase 1 foundation instead of requiring a repository restructure.


