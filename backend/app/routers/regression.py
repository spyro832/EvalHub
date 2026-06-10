"""
Regression detection endpoints.

GET /api/v1/regression/suites             — suite-level summary with per-model trends
GET /api/v1/regression/suites/{id}/trend  — all completed runs for one suite (for charts)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.regression_service import RegressionService

router = APIRouter()


# ── Response schemas ──────────────────────────────────────────────────────────


class ModelTrendOut(BaseModel):
    model_config_id: str
    model_name: str
    run_count: int
    latest_pass_rate: float
    peak_pass_rate: float
    delta: float
    has_regression: bool
    sparkline: list[float]

    model_config = {"protected_namespaces": ()}


class SuiteSummaryOut(BaseModel):
    suite_id: str
    suite_name: str
    category: str | None
    has_regression: bool
    models: list[ModelTrendOut]


class RunPointOut(BaseModel):
    run_id: str
    model_config_id: str
    model_name: str
    pass_rate: float
    pass_count: int
    fail_count: int
    total: int
    avg_latency_ms: float | None
    total_cost_usd: float
    created_at: str


class SuiteTrendOut(BaseModel):
    suite_id: str
    suite_name: str
    runs: list[RunPointOut]


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/suites", response_model=list[SuiteSummaryOut])
async def list_regression_suites(db: AsyncSession = Depends(get_db)):
    """Return regression summary for all suites that have completed runs."""
    service = RegressionService(db)
    suites = await service.get_suites_summary()
    # Convert dataclasses → dicts for Pydantic serialisation
    return [
        SuiteSummaryOut(
            suite_id=s.suite_id,
            suite_name=s.suite_name,
            category=s.category,
            has_regression=s.has_regression,
            models=[
                ModelTrendOut(
                    model_config_id=m.model_config_id,
                    model_name=m.model_name,
                    run_count=m.run_count,
                    latest_pass_rate=m.latest_pass_rate,
                    peak_pass_rate=m.peak_pass_rate,
                    delta=m.delta,
                    has_regression=m.has_regression,
                    sparkline=m.sparkline,
                )
                for m in s.models
            ],
        )
        for s in suites
    ]


@router.get("/suites/{suite_id}/trend", response_model=SuiteTrendOut)
async def get_suite_trend(suite_id: str, db: AsyncSession = Depends(get_db)):
    """Return all completed runs for a suite in chronological order (for charts)."""
    service = RegressionService(db)
    trend = await service.get_suite_trend(suite_id)
    if trend is None:
        raise HTTPException(status_code=404, detail="Suite not found")
    return SuiteTrendOut(
        suite_id=trend.suite_id,
        suite_name=trend.suite_name,
        runs=[
            RunPointOut(
                run_id=r.run_id,
                model_config_id=r.model_config_id,
                model_name=r.model_name,
                pass_rate=r.pass_rate,
                pass_count=r.pass_count,
                fail_count=r.fail_count,
                total=r.total,
                avg_latency_ms=r.avg_latency_ms,
                total_cost_usd=r.total_cost_usd,
                created_at=r.created_at,
            )
            for r in trend.runs
        ],
    )
