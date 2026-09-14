# Every target runs inside the api container, so the host only needs Docker.
DC := docker compose

.DEFAULT_GOAL := help
.PHONY: help up down logs build migrate revision test lint fmt

help:
	@echo "up        start api + postgres + redis"
	@echo "down      stop the stack"
	@echo "logs      follow api logs"
	@echo "build     rebuild images"
	@echo "migrate   alembic upgrade head"
	@echo "revision  create a migration:  make revision m=\"message\""
	@echo "test      run pytest"
	@echo "lint      ruff check + format check"
	@echo "fmt       ruff format + autofix"

up:
	$(DC) up -d

down:
	$(DC) down

logs:
	$(DC) logs -f api

build:
	$(DC) build

# Requires Alembic — added on Day 2.
migrate:
	$(DC) exec api alembic upgrade head

revision:
	@test -n "$(m)" || (echo "usage: make revision m=\"message\"" && exit 1)
	$(DC) exec api alembic revision --autogenerate -m "$(m)"

# Requires pytest — added on Day 5.
test:
	$(DC) exec api pytest

lint:
	$(DC) exec api ruff check .
	$(DC) exec api ruff format --check .

fmt:
	$(DC) exec api ruff format .
	$(DC) exec api ruff check --fix .
