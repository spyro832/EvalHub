.PHONY: dev down build test seed migrate migrate-create logs clean lint format

# ── Development ──────────────────────────────────────────────────────────────

dev:
	docker compose up --build

down:
	docker compose down

build:
	docker compose build

# ── Testing ───────────────────────────────────────────────────────────────────

test:
	docker compose run --rm backend pytest --cov=app --cov-report=term-missing
	cd frontend && npm test

test-backend:
	docker compose run --rm backend pytest --cov=app --cov-report=term-missing

test-frontend:
	cd frontend && npm test

# ── Database ──────────────────────────────────────────────────────────────────

migrate:
	docker compose run --rm backend alembic upgrade head

migrate-create:
	docker compose run --rm backend alembic revision --autogenerate -m "$(msg)"

seed:
	docker compose run --rm backend python -m app.scripts.seed

# ── Code Quality ──────────────────────────────────────────────────────────────

lint:
	docker compose run --rm backend ruff check .
	cd frontend && npm run lint

format:
	docker compose run --rm backend ruff format .
	cd frontend && npm run format

# ── Utilities ─────────────────────────────────────────────────────────────────

logs:
	docker compose logs -f

clean:
	docker compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
