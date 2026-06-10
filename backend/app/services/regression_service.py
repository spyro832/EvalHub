"""
Regression service — computes pass-rate trends across TestRun history and
surfaces model-quality regressions.

A *regression* is defined as the latest run's pass_rate dropping 10 or more
percentage points below the suite/model peak.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_config import ModelConfig
from app.models.test_suite import TestRun, TestRunStatus, TestSuite

_REGRESSION_THRESHOLD = 0.10  # ≥10 pp drop from peak triggers an alert


# ── Data classes (used as response objects; router maps to Pydantic) ──────────


@dataclass
class ModelTrend:
    model_config_id: str
    model_name: str
    run_count: int
    latest_pass_rate: float
    peak_pass_rate: float
    delta: float            # latest − peak (negative = degraded)
    has_regression: bool
    sparkline: list[float]  # pass_rates in chronological order


@dataclass
class SuiteSummary:
    suite_id: str
    suite_name: str
    category: str | None
    has_regression: bool
    models: list[ModelTrend] = field(default_factory=list)


@dataclass
class RunPoint:
    run_id: str
    model_config_id: str
    model_name: str
    pass_rate: float
    pass_count: int
    fail_count: int
    total: int
    avg_latency_ms: float | None
    total_cost_usd: float
    created_at: str  # ISO-8601


@dataclass
class SuiteTrend:
    suite_id: str
    suite_name: str
    runs: list[RunPoint]


# ── Service ───────────────────────────────────────────────────────────────────


class RegressionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Suite-level summary ───────────────────────────────────────────────────

    async def get_suites_summary(self) -> list[SuiteSummary]:
        """
        Return a summary for every suite that has at least one completed run.
        Suites with regressions are sorted first; ties resolved alphabetically.
        """
        result = await self.db.execute(
            select(TestRun, TestSuite, ModelConfig)
            .join(TestSuite, TestRun.suite_id == TestSuite.id)
            .join(ModelConfig, TestRun.model_config_id == ModelConfig.id)
            .where(TestRun.status == TestRunStatus.COMPLETED)
            .order_by(TestRun.created_at)
        )
        rows = result.all()

        # { suite_id → {"name": str, "category": str|None} }
        suite_meta: dict[str, dict] = {}
        # { suite_id → { model_id → [{"model_name": str, "pass_rate": float}] } }
        suite_model_runs: dict[str, dict[str, list[dict]]] = defaultdict(
            lambda: defaultdict(list)
        )

        for run, suite, model in rows:
            if suite.id not in suite_meta:
                suite_meta[suite.id] = {"name": suite.name, "category": suite.category}

            total = run.pass_count + run.fail_count
            pass_rate = (run.pass_count / total) if total > 0 else 0.0
            suite_model_runs[suite.id][model.id].append(
                {"model_name": model.name, "pass_rate": pass_rate}
            )

        summaries: list[SuiteSummary] = []

        for suite_id, meta in suite_meta.items():
            model_trends: list[ModelTrend] = []
            suite_has_regression = False

            for model_id, run_list in suite_model_runs[suite_id].items():
                sparkline = [r["pass_rate"] for r in run_list]
                latest = sparkline[-1]
                peak = max(sparkline)
                delta = latest - peak
                has_reg = len(sparkline) >= 2 and delta <= -_REGRESSION_THRESHOLD

                if has_reg:
                    suite_has_regression = True

                model_trends.append(
                    ModelTrend(
                        model_config_id=model_id,
                        model_name=run_list[0]["model_name"],
                        run_count=len(run_list),
                        latest_pass_rate=round(latest, 4),
                        peak_pass_rate=round(peak, 4),
                        delta=round(delta, 4),
                        has_regression=has_reg,
                        sparkline=[round(v, 4) for v in sparkline],
                    )
                )

            if model_trends:
                summaries.append(
                    SuiteSummary(
                        suite_id=suite_id,
                        suite_name=meta["name"],
                        category=meta["category"],
                        has_regression=suite_has_regression,
                        models=model_trends,
                    )
                )

        # Regressions first, then alphabetical by suite name
        summaries.sort(key=lambda s: (not s.has_regression, s.suite_name.lower()))
        return summaries

    # ── Per-suite trend ───────────────────────────────────────────────────────

    async def get_suite_trend(self, suite_id: str) -> SuiteTrend | None:
        """
        Return all completed runs for a suite, in chronological order.
        Returns None if the suite does not exist.
        """
        suite_row = await self.db.execute(
            select(TestSuite).where(TestSuite.id == suite_id)
        )
        suite = suite_row.scalar_one_or_none()
        if suite is None:
            return None

        result = await self.db.execute(
            select(TestRun, ModelConfig)
            .join(ModelConfig, TestRun.model_config_id == ModelConfig.id)
            .where(
                TestRun.suite_id == suite_id,
                TestRun.status == TestRunStatus.COMPLETED,
            )
            .order_by(TestRun.created_at)
        )
        rows = result.all()

        run_points: list[RunPoint] = []
        for run, model in rows:
            total = run.pass_count + run.fail_count
            pass_rate = (run.pass_count / total) if total > 0 else 0.0
            run_points.append(
                RunPoint(
                    run_id=run.id,
                    model_config_id=model.id,
                    model_name=model.name,
                    pass_rate=round(pass_rate, 4),
                    pass_count=run.pass_count,
                    fail_count=run.fail_count,
                    total=total,
                    avg_latency_ms=run.avg_latency_ms,
                    total_cost_usd=run.total_cost_usd,
                    created_at=run.created_at.isoformat(),
                )
            )

        return SuiteTrend(
            suite_id=suite.id,
            suite_name=suite.name,
            runs=run_points,
        )
