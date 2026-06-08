from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import benchmarks, cost, evaluations, models, prompts, test_suites


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="EvalHub API",
    description="Open Source Platform for AI Evaluation, Benchmarking and Cost Analysis",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evaluations.router, prefix="/api/v1/evaluations", tags=["evaluations"])
app.include_router(models.router, prefix="/api/v1/models", tags=["models"])
app.include_router(prompts.router, prefix="/api/v1/prompts", tags=["prompts"])
app.include_router(test_suites.router, prefix="/api/v1/test-suites", tags=["test-suites"])
app.include_router(cost.router, prefix="/api/v1/cost", tags=["cost"])
app.include_router(benchmarks.router, prefix="/api/v1/benchmarks", tags=["benchmarks"])


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
