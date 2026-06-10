"""
Unit tests for TestSuiteService — mocking LiteLLM so no real API calls happen.
"""

from unittest.mock import patch

import pytest

from app.models.model_config import ModelConfig
from app.models.test_suite import TestCase, TestRunStatus, TestSuite
from app.services.litellm_service import ModelCallResult
from app.services.test_suite_service import TestSuiteService


def _mock_call(response: str = "def foo(): pass") -> ModelCallResult:
    return ModelCallResult(
        response=response,
        latency_ms=100,
        input_tokens=5,
        output_tokens=10,
        cost_usd=0.0005,
        model_id="gpt-4o",
    )


async def _seed_suite_and_model(db_session, suite_id: str, model_id: str) -> None:
    """Insert a TestSuite + ModelConfig + two TestCases into the test DB."""
    suite = TestSuite(id=suite_id, name=f"Suite {suite_id}", category="coding")
    model = ModelConfig(
        id=model_id,
        name=f"Model {model_id}",
        provider="openai",
        model_id="gpt-4o",
    )
    db_session.add_all([suite, model])
    await db_session.flush()

    cases = [
        TestCase(
            suite_id=suite_id,
            input="Write a fibonacci function",
            expected_tags="def,return",
        ),
        TestCase(
            suite_id=suite_id,
            input="What is the capital of France?",
            expected_output="Paris",
        ),
    ]
    db_session.add_all(cases)
    await db_session.flush()


async def test_run_suite_success(db_session):
    """run_suite() should create a COMPLETED TestRun with correct pass/fail counts."""
    await _seed_suite_and_model(db_session, "svc-s1", "svc-m1")
    await db_session.commit()

    svc = TestSuiteService(db_session)
    with patch.object(svc, "llm") as mock_llm_obj:
        # Both responses satisfy their criteria
        mock_llm_obj.call_model.side_effect = [
            _mock_call("def fibonacci(): return [1,1,2,3]"),  # has def + return → pass
            _mock_call("The capital is Paris."),              # has "Paris" → pass
        ]
        run = await svc.run_suite("svc-s1", "svc-m1")

    assert run.status == TestRunStatus.COMPLETED
    assert run.pass_count == 2
    assert run.fail_count == 0
    assert run.avg_latency_ms == 100.0
    assert run.total_cost_usd == pytest.approx(0.001)


async def test_run_suite_partial_failure(db_session):
    """run_suite() should correctly count fails when some responses don't match."""
    await _seed_suite_and_model(db_session, "svc-s2", "svc-m2")
    await db_session.commit()

    svc = TestSuiteService(db_session)
    with patch.object(svc, "llm") as mock_llm_obj:
        mock_llm_obj.call_model.side_effect = [
            _mock_call("import foo"),       # no "def" or "return" → fail (case 1)
            _mock_call("London"),           # "Paris" not in response → fail (case 2)
        ]
        run = await svc.run_suite("svc-s2", "svc-m2")

    assert run.status == TestRunStatus.COMPLETED
    assert run.pass_count == 0
    assert run.fail_count == 2


async def test_run_suite_llm_exception(db_session):
    """If LiteLLM raises for a case, that case should be marked as failed."""
    await _seed_suite_and_model(db_session, "svc-s3", "svc-m3")
    await db_session.commit()

    svc = TestSuiteService(db_session)
    with patch.object(svc, "llm") as mock_llm_obj:
        mock_llm_obj.call_model.side_effect = [
            RuntimeError("API rate limit"),   # first case errors
            _mock_call("Paris"),              # second case succeeds
        ]
        run = await svc.run_suite("svc-s3", "svc-m3")

    assert run.status == TestRunStatus.COMPLETED
    assert run.pass_count == 1
    assert run.fail_count == 1


async def test_run_suite_not_found_suite(db_session):
    """run_suite() with a non-existent suite ID should raise ValueError."""
    svc = TestSuiteService(db_session)
    with pytest.raises(ValueError, match="not found"):
        await svc.run_suite("nonexistent-suite", "any-model")


async def test_run_suite_not_found_model(db_session):
    """run_suite() with a non-existent model ID should raise ValueError."""
    suite = TestSuite(id="svc-s4", name="Suite S4", category="coding")
    db_session.add(suite)
    await db_session.commit()

    svc = TestSuiteService(db_session)
    with pytest.raises(ValueError, match="not found"):
        await svc.run_suite("svc-s4", "nonexistent-model")


async def test_list_runs_empty(db_session):
    """list_runs() for a suite with no runs should return []."""
    suite = TestSuite(id="svc-s5", name="Suite S5")
    db_session.add(suite)
    await db_session.commit()

    svc = TestSuiteService(db_session)
    runs = await svc.list_runs("svc-s5")
    assert runs == []


async def test_list_runs_after_run(db_session):
    """list_runs() should return the run created by run_suite()."""
    await _seed_suite_and_model(db_session, "svc-s6", "svc-m6")
    await db_session.commit()

    svc = TestSuiteService(db_session)
    with patch.object(svc, "llm") as mock_llm_obj:
        mock_llm_obj.call_model.return_value = _mock_call("def foo(): return 1")
        await svc.run_suite("svc-s6", "svc-m6")

    runs = await svc.list_runs("svc-s6")
    assert len(runs) == 1
    assert runs[0].suite_id == "svc-s6"
    assert runs[0].status == TestRunStatus.COMPLETED
