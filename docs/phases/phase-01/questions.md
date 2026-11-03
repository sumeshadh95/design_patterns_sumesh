# Phase 1 — Skeleton questions

**Pattern / focus:** Course intro and an empty-but-running three-tier skeleton (no GoF pattern this phase).

**Read first:** [Guide 01](../../materials/guides/01-course-patterns-and-skeleton.md) · [Requirements](requirements.md)

## How to answer

- Use your own wording. Do not paste textbook definitions or teaching-example class names as if they were your greenhouse types.
- When a question asks about *this application*, refer to what you built (or what the lab required): layers, routes, and tooling.
- Short answers are fine when the question is narrow. Write a few sentences when it asks you to explain or compare.
- Write each answer inside the matching **Your Answer** note. Replace the placeholder; leave the question text unchanged.

## A. Pattern

1. In your own words, what is a design pattern? What is it *not*?

> [!NOTE]
> ***Your Answer***
>
> A design pattern is a named, reusable approach to a recurring software-design problem. It gives developers a shared way to discuss a design and helps separate code that is stable from behaviour likely to change. It is not a library to install, a finished piece of code to copy, or extra classes added only because a pattern has a name.

2. Name the three GoF pattern families. For each family, give one-sentence: what kind of design problem it addresses. Then place **Factory Method** and **Strategy** into the correct family.

> [!NOTE]
> ***Your Answer***
>
> - **Creational patterns** address how objects are created without coupling all callers to concrete constructors. **Factory Method** is creational.
> - **Structural patterns** address how classes and objects are composed so their responsibilities and interfaces fit together cleanly.
> - **Behavioral patterns** address how objects collaborate and how behaviour can vary. **Strategy** is behavioral.

3. A teammate wants to add a pattern “because it is on the course list,” even though the feature is small and unlikely to grow. When should you **skip** a pattern? What risk do you take if you apply one too early?

> [!NOTE]
> ***Your Answer***
>
> A pattern should be skipped when a feature is small, unlikely to change, and a simple function or class solves the problem clearly. Applying a pattern too early adds indirection, more files, and more concepts for a developer to understand. This makes the code harder to maintain without solving a real problem.

## B. This phase of the application

4. Why does Phase 1 ship a vertical slice that does almost no greenhouse business logic? What does “empty but running” prove that a folder of unimplemented classes would not?

> [!NOTE]
> ***Your Answer***
>
> Phase 1 verifies the whole stack instead of only proving that folders exist. It shows that PostgreSQL starts, Alembic can connect and migrate, FastAPI can serve an endpoint, the frontend can call the API, and the dashboard can display the result. A folder of unimplemented classes cannot prove configuration, imports, networking, database connectivity, or startup instructions work together.

5. List the four backend layer packages used in this course (`domain`, `application`, `infrastructure`, `interfaces/api`). For each, state what belongs there and give one example of something that must **not** live in `domain`.

> [!NOTE]
> ***Your Answer***
>
> - **`domain`** contains business concepts, entities, and later pattern abstractions. A future `Sensor` business concept belongs here.
> - **`application`** contains use cases and orchestration. A future service that coordinates sensor operations belongs here.
> - **`infrastructure`** contains technical details, including settings, SQLAlchemy database access, repositories, and external adapters.
> - **`interfaces/api`** contains FastAPI routes and HTTP request/response wiring, such as the `GET /health` route.
>
> FastAPI route functions, SQLAlchemy sessions and models, database connection code, and HTTP Pydantic schemas must not live in `domain`. Domain code should express greenhouse rules rather than depend on a web framework or a database library.

6. What does `GET /health` return, and why does it check the database instead of only reporting that the HTTP process is up? Why is API documentation served at `/scalar`, and why is `/docs` disabled?

> [!NOTE]
> ***Your Answer***
>
> When the database is reachable, `GET /health` returns `{"status": "ok", "db": "ok"}`. If the database cannot be reached, it returns `{"status": "degraded", "db": "fail"}`. Checking the database is important because the FastAPI process can be running while the application cannot store or retrieve data.
>
> Scalar is available at `/scalar` as the project’s interactive API reference and shared OpenAPI contract. The built-in Swagger UI at `/docs` is disabled so the project uses one intended documentation interface.

7. Phase 1 requires Alembic (or equivalent) with a **baseline** migration and **no** business tables such as `devices`. Why introduce the migration toolchain before any product schema? What would go wrong if you created tables by hand in Postgres and only added migrations later?

> [!NOTE]
> ***Your Answer***
>
> Alembic is introduced early so the project starts with a version-controlled and repeatable process for changing the database schema. The empty baseline proves that migrations can connect to PostgreSQL and records the initial schema state. Creating tables manually first would make developer databases inconsistent, lose migration history, and make it difficult to add a trustworthy first migration later.

## C. Compare, contrast, and scenarios

8. Explain **dependency direction** in this skeleton: which layers may import which? Why must domain code not import FastAPI, SQLAlchemy, or Pydantic models used as HTTP schemas?

> [!NOTE]
> ***Your Answer***
>
> Dependencies should flow inward. The API layer can call application code; application code can use domain abstractions and coordinate infrastructure; infrastructure implements technical details such as database access. The domain layer should be the most independent layer.
>
> Domain code must not import FastAPI, SQLAlchemy, or Pydantic models used as HTTP schemas. Otherwise, greenhouse rules become coupled to the selected web and database technologies, which makes the rules harder to test, reuse, or change.

9. The frontend cannot show a healthy badge. A classmate blames “the patterns.” What should you check first (stack, CORS/proxy, health JSON), and why is that a Phase 1 concern rather than a later pattern concern?

> [!NOTE]
> ***Your Answer***
>
> First, check that Docker Compose shows PostgreSQL as healthy and that the backend is running. Next, open `GET /health` directly and confirm that it returns the required JSON. Then inspect the browser network request and verify the frontend API base URL, Vite proxy configuration if used, and CORS configuration.
>
> This is a Phase 1 concern because it is a stack integration and configuration issue. It must work before later phases add design patterns or more greenhouse behaviour.

10. Course completion is at **Phase 12**, not Phase 1. What is still missing after a successful skeleton, and how do later phases add behaviour without rewriting the foundations you laid here?

> [!NOTE]
> ***Your Answer***
>
> After Phase 1, the project still lacks devices, sensors, actuators, locations, automation logic, richer API endpoints, WebSockets, and schema hardening. Later phases can add each feature in its appropriate layer: business concepts and patterns in `domain`, use cases in `application`, persistence and adapters in `infrastructure`, and HTTP endpoints in `interfaces/api`. This preserves the Phase 1 foundation instead of requiring a repository restructure.
