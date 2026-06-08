# Contributing to EvalHub

Thank you for your interest in contributing to EvalHub!

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Node.js 22+
- Python 3.13+
- Git

### Local Setup

```bash
git clone https://github.com/yourusername/evalhub
cd evalhub
cp .env.example .env
docker compose up
```

The app will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Running Tests

```bash
# All tests
make test

# Backend only
docker compose run --rm backend pytest

# Frontend only
cd frontend && npm test
```

## Project Structure

```
EvalHub/
├── frontend/          # Next.js application
├── backend/           # FastAPI application
├── docker/            # Dockerfiles
├── benchmarks/        # Sample benchmark datasets
├── docs/              # Documentation
├── .github/           # GitHub Actions CI/CD
├── docker-compose.yml
└── Makefile
```

## Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Write or update tests
5. Run `make test` — all tests must pass
6. Run `make lint` — no lint errors
7. Submit a Pull Request

## Adding a New API Endpoint

1. Create Pydantic schema in `backend/app/schemas/`
2. Add SQLAlchemy model in `backend/app/models/` if needed
3. Create/update service in `backend/app/services/`
4. Add router in `backend/app/routers/`
5. Register router in `backend/app/main.py`
6. Write tests in `backend/tests/`
7. Create Alembic migration if schema changed: `make migrate-create msg="add_table"`

## Code Style

### Python
- Formatter: `ruff format`
- Linter: `ruff check`
- Type hints everywhere
- Pydantic v2 for all schemas

### TypeScript
- Strict TypeScript — no `any`
- ESLint + Prettier
- Functional components with hooks

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add prompt versioning
fix: correct token count calculation
docs: update quick start guide
chore: upgrade litellm to 1.60
```

## Reporting Bugs

Open an issue with:
- Steps to reproduce
- Expected vs actual behavior
- Your OS, Docker version
- Relevant logs

## Code of Conduct

Be respectful. This project follows the [Contributor Covenant](https://www.contributor-covenant.org/).
