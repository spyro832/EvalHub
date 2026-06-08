# EvalHub

> The Open Source Platform for AI Evaluation, Benchmarking and Cost Analysis.

**Self-hosted · Vendor-neutral · Privacy-first · Local-first**

---

## What is EvalHub?

EvalHub lets developers, startups and AI teams compare AI models, prompts and workflows without vendor dependency.

Run the same prompt across GPT, Claude, Gemini and local Ollama models. See responses, latency, token usage and cost — side by side.

## Features

- **Model Comparison** — Run prompts across multiple providers and see results side by side
- **Prompt Playground** — A/B test prompts across models and measure quality, cost and latency
- **AI Test Suites** — Create automated test datasets and run regression benchmarks
- **Regression Detection** — Track quality changes across versions, like unit tests for LLMs
- **Cost Analytics** — Daily/monthly spend breakdown by model, provider, feature and prompt
- **Community Benchmarks** — Share and import benchmark datasets from the community
- **Local First** — Works on your machine, Docker or self-hosted server
- **Privacy First** — Zero telemetry, zero tracking, all data stays yours

## Supported Models

| Provider     | Models                                          |
|--------------|-------------------------------------------------|
| OpenAI       | GPT-4o, GPT-4o-mini, o1, o3-mini               |
| Anthropic    | Claude 3.5 Sonnet, Claude 3.5 Haiku, Claude 3 Opus |
| Google       | Gemini 1.5 Pro, Gemini 2.0 Flash               |
| Ollama       | Any local model (Llama, Mistral, Qwen, etc.)    |
| HuggingFace  | Open-source models via Inference API            |

Powered by [LiteLLM](https://github.com/BerriAI/litellm) — supports 100+ providers.

## Quick Start

### Prerequisites

- Docker & Docker Compose
- API keys for the providers you want to use

### Run with Docker Compose

```bash
git clone https://github.com/yourusername/evalhub
cd evalhub
cp .env.example .env
# Edit .env and add your API keys
docker compose up
```

Open [http://localhost:3000](http://localhost:3000)

## Tech Stack

- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query
- **Backend**: FastAPI, Python 3.13, SQLAlchemy 2.x, Alembic
- **Database**: PostgreSQL 16
- **Queue**: Redis 7 + Celery
- **AI Layer**: LiteLLM (100+ providers)

## Development

```bash
# Start all services with hot reload
make dev

# Run tests
make test

# Seed sample data
make seed

# Run database migrations
make migrate
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full development guide.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

[MIT License](LICENSE)
