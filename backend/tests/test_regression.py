"""Tests for the regression router and RegressionService."""

from datetime import UTC, datetime, timedelta

import pytest

from app.models.model_config import ModelConfig
from app.models.test_suite import TestRun, TestRunStatus, TestSuite

# ── Helpers ────────────────────────────────────────────────────────────────────

_BASE_TIME = datetime(2024, 1, 1, tzinfo=UTC)


async def _create_suite(db_session, suite_id: str, name: str) -> None:
    suite = TestSuite(id=suite_id, name=name, category="coding")
    db_session.add(suite)
    await db_session.flush()


async def _create_model(db_session, model_id: str, name: str) -> None:
    model = ModelConfig(id=model_id, name=name, provider="openai", model_id="gpt-4o")
    db_session.add(model)
    await db_session.flush()


async def _create_run(
    db_session,
    run_id: str,
    suite_id: str,
    model_id: str,
    pass_count: int,
    fail_count: int,
    offset_hours: int = 0,
) -> None:
    ts = _BASE_TIME + timedelta(hours=offset_hours)
    run = TestRun(
        id=run_id,
        suite_id=suite_id,
        model_config_id=model_id,
        status=TestRunStatus.COMPLETED,
        pass_count=pass_count,
        fail_count=fail_count,
        created_at=ts,
        updated_at=ts,
    )
    db_session.add(run)


# ── Empty-state tests ──────────────────────────────────────────────────────────


async def test_regression_suites_empty(client):
    """No completed runs yet → empty list."""
    response = await client.get("/api/v1/regression/suites")
    assert response.status_code == 200
    assert response.json() == []


async def test_regression_trend_not_found(client):
    """Suite that does not exist → 404."""
    response = await client.get("/api/v1/regression/suites/does-not-exist/trend")
    assert response.status_code == 404


# ── Data-present tests ─────────────────────────────────────────────────────────


async def test_regression_suites_with_regression(client, db_session):
    """
    Two runs where pass_rate drops ≥10 pp → has_regression = True.

    Run 1: 8/10 = 80%
    Run 2: 5/10 = 50% → delta = -30% → regression
    """
    await _create_suite(db_session, "reg-s1", "Regression Suite Alpha")
    await _create_model(db_session, "reg-m1", "TestModel-A")
    await _create_run(db_session, "reg-r1", "reg-s1", "reg-m1", 8, 2, offset_hours=0)
    await _create_run(db_session, "reg-r2", "reg-s1", "reg-m1", 5, 5, offset_hours=1)
    await db_session.commit()

    response = await client.get("/api/v1/regression/suites")
    assert response.status_code == 200

    suites = response.json()
    reg = next((s for s in suites if s["suite_id"] == "reg-s1"), None)
    assert reg is not None, "Regression Suite Alpha not returned"
    assert reg["has_regression"] is True
    assert len(reg["models"]) == 1

    m = reg["models"][0]
    assert m["model_name"] == "TestModel-A"
    assert m["has_regression"] is True
    assert m["run_count"] == 2
    assert abs(m["latest_pass_rate"] - 0.5) < 0.01
    assert abs(m["peak_pass_rate"] - 0.8) < 0.01
    assert abs(m["delta"] - (-0.3)) < 0.01
    assert m["sparkline"] == [0.8, 0.5]


async def test_regression_suites_no_regression(client, db_session):
    """
    Two runs where pass_rate stays stable → has_regression = False.

    Run 1: 7/10 = 70%
    Run 2: 8/10 = 80% → delta = +10% (improvement, not regression)
    """
    await _create_suite(db_session, "reg-s2", "Stable Suite Beta")
    await _create_model(db_session, "reg-m2", "TestModel-B")
    await _create_run(db_session, "reg-r3", "reg-s2", "reg-m2", 7, 3, offset_hours=0)
    await _create_run(db_session, "reg-r4", "reg-s2", "reg-m2", 8, 2, offset_hours=1)
    await db_session.commit()

    response = await client.get("/api/v1/regression/suites")
    assert response.status_code == 200

    suites = response.json()
    stable = next((s for s in suites if s["suite_id"] == "reg-s2"), None)
    assert stable is not None
    assert stable["has_regression"] is False
    m = stable["models"][0]
    assert m["has_regression"] is False
    # delta = latest - peak; since latest IS the peak, delta is 0
    assert m["delta"] >= 0


async def test_regression_suites_single_run_no_regression(client, db_session):
    """A single run can never be a regression (no prior baseline)."""
    await _create_suite(db_session, "reg-s3", "Single Run Suite")
    await _create_model(db_session, "reg-m3", "TestModel-C")
    await _create_run(db_session, "reg-r5", "reg-s3", "reg-m3", 3, 7, offset_hours=0)
    await db_session.commit()

    response = await client.get("/api/v1/regression/suites")
    assert response.status_code == 200
    suites = response.json()
    single = next((s for s in suites if s["suite_id"] == "reg-s3"), None)
    assert single is not None
    # Only 1 run → no regression possible
    assert single["models"][0]["has_regression"] is False


async def test_regression_trend_with_data(client, db_session):
    """
    GET /regression/suites/{id}/trend should return runs in chronological order.
    Uses data from test_regression_suites_with_regression.
    """
    response = await client.get("/api/v1/regression/suites/reg-s1/trend")
    assert response.status_code == 200
    data = response.json()
    assert data["suite_id"] == "reg-s1"
    assert data["suite_name"] == "Regression Suite Alpha"
    assert len(data["runs"]) == 2

    run_a, run_b = data["runs"][0], data["runs"][1]
    assert run_a["pass_count"] == 8
    assert run_b["pass_count"] == 5
    assert abs(run_a["pass_rate"] - 0.8) < 0.01
    assert abs(run_b["pass_rate"] - 0.5) < 0.01
    assert run_a["model_name"] == "TestModel-A"
    assert run_a["total"] == 10


async def test_regression_trend_empty_suite(client, db_session):
    """A suite with no completed runs should return an empty runs list."""
    await _create_suite(db_session, "reg-s4", "Empty Trend Suite")
    await db_session.commit()

    response = await client.get("/api/v1/regression/suites/reg-s4/trend")
    assert response.status_code == 200
    data = response.json()
    assert data["suite_id"] == "reg-s4"
    assert data["runs"] == []
