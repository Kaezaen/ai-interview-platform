# AI Interview Platform

Backend for an AI-powered interview preparation platform. The AI generates interview
questions for a given position, level, and skill set; the user answers; the AI evaluates
each answer against a structured rubric. Aggregate scores are computed by the backend,
never by the model.

This is a production-oriented portfolio project. The emphasis is on architecture,
validation of AI output, failure handling, and testing — not on feature count.

## Stack

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL 16 ·
Redis 7 · Gemini (behind a provider abstraction) · Docker Compose · pytest · Ruff

## Prerequisites

Docker Desktop is the only requirement. Python, dependencies, and tooling all live
inside the container — nothing is installed on the host.

## Running from zero

```bash
git clone <repository-url>
cd ai-interview-platform

# Create your local environment file. .env is gitignored and never committed.
cp .env.example .env

docker compose up -d --build
docker compose ps          # api, postgres, and redis should all report healthy
```

Then open:

| URL | What it is |
|---|---|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/health | Liveness probe |
| http://localhost:8000/health/ready | Readiness probe |

Stop the stack with `docker compose down`, or `docker compose down -v` to also drop the
database volume.

## Health endpoints

Liveness and readiness are deliberately separate:

- **`GET /health`** — is the process alive? It touches no dependency, so a database
  outage can never cause the container to be restarted pointlessly. This is what the
  container healthcheck polls.
- **`GET /health/ready`** — can the process serve traffic? It reports on each backing
  service and returns 503 when one fails its probe.

Dependencies that are not wired up yet report `not_configured` rather than `ok`; the
database probe arrives with the database layer, the Redis probe with the Redis layer.

## Project layout

```
app/
  main.py           FastAPI app factory, lifespan, OpenAPI metadata
  core/             settings, shared cross-cutting concerns
  api/routers/      HTTP layer — no business logic, no SQL
  services/         business logic, transactions, AI orchestration
    ai/             AIProvider abstraction; vendor SDKs confined here
  repositories/     the only place SQLAlchemy queries live
  models/           SQLAlchemy ORM models
  schemas/          Pydantic schemas for every boundary
docs/PROJECT_SPEC.md  full specification
```

Dependencies point one way only: `Router → Service → Repository → Database`.

## Commands

The `Makefile` wraps the common tasks; each runs inside the api container.

```bash
make up          # start the stack
make down        # stop it
make logs        # follow api logs
make lint        # ruff check + format check
make fmt         # ruff format + autofix
make test        # pytest
make migrate     # alembic upgrade head
make revision m="add users table"
```

If `make` is not installed (common on Windows), run the underlying command directly —
for example `docker compose exec api ruff check .`.

## Configuration

All configuration comes from the environment; see `.env.example` for the full list.
`SECRET_KEY`, `DATABASE_URL`, and `REDIS_URL` are required and have no defaults, so a
missing value fails at startup rather than surfacing later inside a request.

Never commit `.env`. Only `.env.example` belongs in git.
