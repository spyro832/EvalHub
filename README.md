<div align="center">

# 🧪 EvalHub

### The open-source platform for AI model evaluation, benchmarking and cost analysis.

Compare GPT-4o, Claude, Gemini and local Llama models side-by-side — latency, cost, quality — in one self-hosted dashboard.

[![CI](https://github.com/spyro832/EvalHub/actions/workflows/ci.yml/badge.svg)](https://github.com/spyro832/EvalHub/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](docker-compose.yml)

[**Quick Start**](#-quick-start) · [**Features**](#-features) · [**Screenshots**](#-screenshots) · [**Contributing**](#-contributing)

---

<!-- Add your demo GIF here once you record it -->
<!-- ![EvalHub Demo](docs/demo.gif) -->

</div>

---

## Why EvalHub?

Picking the right LLM for your use case is hard. LangSmith is expensive. Vendor dashboards are siloed. Spreadsheets don't scale.

**EvalHub is the open-source alternative** — runs on your machine or server, works with every major provider, stores nothing in the cloud, and gives you the data to make confident model decisions.

```
Same prompt → GPT-4o, Claude Sonnet, Llama 3.2 → side-by-side results + cost
```

---

## ✨ Features

| | Feature | Description |
|---|---|---|
| ⚡ | **Model Comparison** | Run any prompt across multiple providers simultaneously. See responses, latency, tokens and cost side-by-side. |
| 🔬 | **Prompt Playground** | A/B test prompt variants. Iterate fast, measure the difference. |
| 🧪 | **Test Suites** | Create structured test datasets. Run them against any model with real-time progress. |
| 📉 | **Regression Detection** | Catch quality regressions before they reach production. Track pass rates over time. |
| 💰 | **Cost Analytics** | Know exactly what you're spending per model and per call. No surprise bills. |
| 📦 | **Community Benchmarks** | Import and export benchmark datasets. Share with your team or the community. |
| 🏠 | **Self-Hosted** | One `docker compose up`. Your data never leaves your infrastructure. |
| 🔒 | **Privacy-First** | Zero telemetry. Zero tracking. API keys encrypted at rest. |

---

## 🖥 Screenshots

> **Model Comparison** — same prompt, 3 models, instant side-by-side results with latency and cost

<!-- Replace with real screenshots -->
```
┌─────────────────────────────────────────────────────────────────────┐
│  Prompt: "Explain async/await in Python in 2 sentences"             │
├───────────────────┬───────────────────┬─────────────────────────────┤
│  GPT-4o           │  Claude Sonnet    │  Llama 3.2 (local)          │
│  312ms · $0.0008  │  287ms · $0.0006  │  891ms · $0.00              │
│                   │                   │                              │
│  Async/await is…  │  In Python…       │  Async/await allows…        │
└───────────────────┴───────────────────┴─────────────────────────────┘
```

> **Test Suites** — automated regression testing for LLMs

> **Cost Analytics** — spend breakdown by model and provider

---

## 🚀 Quick Start

**Requirements:** Docker & Docker Compose. That's it.

```bash
git clone https://github.com/spyro832/EvalHub.git
cd EvalHub
cp .env.example .env
```

Add your API keys to `.env`:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
# Google, HuggingFace optional — Ollama works with no key
```

```bash
docker compose up
```

Open **http://localhost:3000** → done. 🎉

> **Using Ollama?** Start it with `ollama serve` before running docker compose. No API key needed.

### Seed sample data (optional)

```bash
make seed   # adds 3 sample benchmarks + test suite + prompts
```

---

## 🤖 Supported Models

| Provider | Example Models | Key Required |
|---|---|---|
| **OpenAI** | GPT-4o, GPT-4o-mini, o1, o3-mini | Yes |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus | Yes |
| **Google** | Gemini 1.5 Pro, Gemini 2.0 Flash | Yes |
| **Ollama** | Llama 3.2, Mistral, Qwen, Phi-3, any local model | No |
| **HuggingFace** | Open-source models via Inference API | Yes |
| **100+ more** | Powered by [LiteLLM](https://github.com/BerriAI/litellm) | Varies |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────┐
│               Browser (Next.js 15)              │
│   Dashboard · Compare · Playground · Cost       │
└──────────────────────┬──────────────────────────┘
                       │ REST + SSE
┌──────────────────────▼──────────────────────────┐
│            FastAPI Backend (Python 3.13)         │
│   Routers · Services · LiteLLM · Encryption     │
└────────┬─────────────────────────┬──────────────┘
         │                         │
┌────────▼──────────┐   ┌──────────▼──────────────┐
│  PostgreSQL 16    │   │  Celery + Redis 7        │
│  (all data)       │   │  (async LLM tasks)       │
└───────────────────┘   └─────────────────────────┘
```

**How evaluations work:**
1. You submit a prompt + model selection → API returns `pending` instantly
2. Celery worker calls all LLMs in parallel
3. Results stream back to the UI via Server-Sent Events in real time

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS 4 |
| UI | Radix UI, Recharts, Lucide Icons, Zustand |
| Backend | FastAPI 0.115, Python 3.13, Uvicorn |
| ORM | SQLAlchemy 2.x (async) + Alembic |
| Database | PostgreSQL 16 |
| Queue | Celery 5.4 + Redis 7 |
| AI | LiteLLM 1.56+ |
| Security | Fernet encryption for API keys |
| Testing | pytest, httpx, SQLite (in-memory) |
| Containers | Docker + Docker Compose |

---

## 🧑‍💻 Development

```bash
# Start everything with hot reload
make dev

# Backend only
cd backend && uvicorn app.main:app --reload

# Frontend only
cd frontend && npm run dev

# Run tests
make test-backend   # pytest with coverage
make test-frontend  # vitest

# Database migrations
make migrate                      # apply
make migrate-create msg="my change"  # create new

# Seed sample data
make seed

# Lint & format
make lint
make format
```

### Project structure

```
EvalHub/
├── backend/
│   ├── app/
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic (EvalService, CostService…)
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   ├── tasks/         # Celery async tasks
│   │   └── core/          # Config, DB, security
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/(dashboard)/   # All pages
│       ├── components/        # Shared components
│       └── lib/               # API client, utils, toast
└── docker/                    # Dockerfiles
```

---

## 🗺 Roadmap

- [x] Model comparison with real-time streaming
- [x] Prompt playground
- [x] Test suites with live run progress
- [x] Cost analytics dashboard
- [x] Community benchmarks (import/export)
- [x] Async LLM execution via Celery
- [x] API key encryption
- [ ] Regression detection charts
- [ ] Search & filtering across all lists
- [ ] Frontend test suite (Vitest)
- [ ] OpenTelemetry integration
- [ ] CLI tool for terminal-based evals
- [ ] Authentication (optional, for team deployments)

---

## 🤝 Contributing

Contributions are welcome — bug fixes, new features, docs improvements, anything.

1. Fork the repo
2. Create a branch: `git checkout -b feat/your-feature`
3. Make your changes + add tests
4. Open a PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

**Ways to contribute without code:**
- ⭐ Star the repo (helps others find it)
- 🐛 Report bugs via [Issues](https://github.com/spyro832/EvalHub/issues)
- 💡 Suggest features
- 📣 Share with your team or on social media

---

## 📄 License

[MIT](LICENSE) — use it, fork it, build on it.

---

<div align="center">

**Built for developers who want to evaluate LLMs without handing data to a third party.**

If EvalHub saves you time or money, consider giving it a ⭐

</div>
