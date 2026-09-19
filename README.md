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

Dependencies that are not wired up yet report `not_configured` rather than `ok`. The
database probe runs a `SELECT 1` against the pool the application actually uses; the
Redis probe arrives with the Redis layer.

## Database and migrations

The schema is owned by Alembic. `Base.metadata.create_all()` is never called in the
application, so the database can only ever change through a reviewed migration.

```bash
make migrate                      # alembic upgrade head
make revision m="add questions"   # autogenerate a revision, then read it before keeping it
```

Both commands run inside the api container, and `alembic/` is mounted from the host, so a
generated revision lands in the repository.

Two tables exist today:

| Table | Notable columns |
|---|---|
| `users` | `email` (unique, stored lowercased), `password_hash`, `is_active` |
| `interviews` | `user_id` (FK, `ON DELETE CASCADE`), `position`, `level`, `skills` (`text[]`), `status` |

`level` and `status` are native PostgreSQL enums, so the database rejects a value outside
the vocabulary. The cost of that choice is that Alembic's autogenerate does not notice a
new enum value: adding one means writing `ALTER TYPE ... ADD VALUE` by hand.

`skills` is a `text[]` rather than a relation. Skills are free-form labels that steer
question generation, there is no skill catalogue to reference, and no endpoint filters by
skill — so the join table would carry no queries. The trade-off accepted is that nothing
enforces canonical naming: "Postgres" and "PostgreSQL" are different strings.

## Authentication

| Endpoint | Behaviour |
|---|---|
| `POST /auth/register` | 201, or 409 if the email is already registered |
| `POST /auth/login` | 200 with an access token, or 401 |
| `GET /auth/me` | The current user; 401 without a valid token |

Passwords are hashed with Argon2id (argon2-cffi defaults: t=3, m=64 MiB, p=4). No
endpoint, schema, or log line ever carries the hash.

Access tokens are HS256 JWTs signed with `SECRET_KEY` and valid for
`ACCESS_TOKEN_EXPIRE_MINUTES`, 30 by default. Thirty minutes is long enough to finish a
practice interview without logging in again, and short enough that a leaked token stops
working on its own.

**Known limitations, stated rather than hidden:**

- **There is no refresh token.** When the access token expires the user logs in again.
  Adding refresh tokens properly means storing them, rotating them on use, and detecting
  reuse — worth doing, but not worth doing badly.
- **There is no revocation list.** A token stays valid until it expires, even if the
  account is disabled in the meantime; `is_active` is checked when the token is used, so a
  disabled account is rejected at the next request, not at the moment it is disabled.
- Failed logins answer identically for an unknown address, a wrong password and a disabled
  account, and always verify a hash, so neither the response nor its timing reveals which
  addresses are registered.

## Interviews

| Endpoint | Behaviour |
|---|---|
| `POST /interviews` | 201; creates an interview owned by the caller |
| `GET /interviews` | The caller's interviews, newest first, `?limit=` (max 100) and `?offset=` |
| `GET /interviews/{id}` | 200, or **404 if it belongs to someone else** |

Ownership is part of the query, not a check performed afterwards: another user's row is
never loaded. The answer for "not yours" is deliberately the same 404 as for "does not
exist", so the API cannot be used to find out which ids are real.

## Errors

Every non-2xx response has the same shape:

```json
{
  "error": {
    "code": "INTERVIEW_NOT_FOUND",
    "message": "Interview tidak ditemukan",
    "request_id": "0f9c1d2e..."
  }
}
```

`request_id` is also returned as the `X-Request-ID` header and appears in the logs, which
is what connects a 500 the user saw to the stack trace the server kept. It is always
generated server-side; an inbound `X-Request-ID` is ignored. Validation failures add a
`details` array naming each offending field — never the value it carried.

Services raise domain exceptions and never `HTTPException`; the mapping from exception to
status code lives in one module, `app/api/errors.py`.

## Project layout

```
app/
  main.py           FastAPI app factory, lifespan, OpenAPI metadata
  core/             settings, security primitives, domain exceptions
  db/               declarative base, async engine, request-scoped session
  api/              HTTP layer — no business logic, no SQL
    routers/        endpoints
    deps.py         auth dependency and service wiring
    errors.py       the one place an exception becomes a status code
  services/         business logic, transactions, AI orchestration
    ai/             AIProvider abstraction; vendor SDKs confined here
  repositories/     the only place SQLAlchemy queries live
  models/           SQLAlchemy ORM models
  schemas/          Pydantic schemas for every boundary
alembic/            migrations; the only way the schema changes
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
`ACCESS_TOKEN_EXPIRE_MINUTES` defaults to 30.

Never commit `.env`. Only `.env.example` belongs in git.
