"""
Celery background tasks for evaluations and test suite runs.

Both tasks use asyncio.run() with a freshly-created async engine per invocation.
We do NOT reuse the module-level engine from database.py because Celery workers
run in separate processes and may inherit stale event-loop handles.
"""

import asyncio
import statistics

from app.tasks.celery_app import celery_app


def _make_session():
    """Create a fresh async engine + session factory for this task invocation."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    from app.core.config import settings

    engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ── Evaluation task ────────────────────────────────────────────────────────────


@celery_app.task(bind=True, name="run_evaluation", max_retries=2)
def run_evaluation(self, evaluation_id: str) -> dict:
    """Run all LLM calls for an evaluation and persist results one by one.

    The Evaluation record (with placeholder EvalResult rows) must already
    exist in the database before this task is dispatched.
    """

    async def _run():
        SessionLocal = _make_session()
        async with SessionLocal() as db:
            from sqlalchemy import select

            from app.core.security import decrypt_api_key
            from app.models.evaluation import EvalResult, Evaluation, EvaluationStatus
            from app.models.model_config import ModelConfig
            from app.services.litellm_service import LiteLLMService
            from app.services.model_utils import get_litellm_model_id

            # Fresh SELECT — don't rely on identity map
            row = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
            evaluation = row.scalar_one_or_none()
            if not evaluation:
                return {"error": f"Evaluation {evaluation_id} not found"}

            results_row = await db.execute(
                select(EvalResult).where(EvalResult.evaluation_id == evaluation_id)
            )
            results = list(results_row.scalars().all())

            llm = LiteLLMService()

            try:
                evaluation.status = EvaluationStatus.RUNNING
                await db.commit()

                for result in results:
                    config_row = await db.execute(
                        select(ModelConfig).where(ModelConfig.id == result.model_config_id)
                    )
                    model_config = config_row.scalar_one_or_none()

                    if not model_config:
                        result.error = f"Model config '{result.model_config_id}' not found"
                        await db.commit()
                        continue

                    try:
                        api_key = None
                        if model_config.api_key_encrypted:
                            api_key = decrypt_api_key(model_config.api_key_encrypted)

                        model_id = get_litellm_model_id(model_config.provider, model_config.model_id)
                        call = llm.call_model(
                            model_id=model_id,
                            prompt=evaluation.prompt,
                            api_key=api_key,
                            base_url=model_config.base_url,
                        )
                        result.response = call.response
                        result.latency_ms = call.latency_ms
                        result.input_tokens = call.input_tokens
                        result.output_tokens = call.output_tokens
                        result.cost_usd = call.cost_usd
                        result.error = None
                    except Exception as exc:
                        result.error = str(exc)

                    # Commit after each model so SSE can stream incremental progress
                    await db.commit()

                evaluation.status = EvaluationStatus.COMPLETED
                await db.commit()
                return {"status": "completed", "evaluation_id": evaluation_id}

            except Exception as exc:
                try:
                    evaluation.status = EvaluationStatus.FAILED
                    await db.commit()
                except Exception:
                    pass
                raise self.retry(exc=exc, countdown=5) from exc

    return asyncio.run(_run())


# ── Test-suite run task ────────────────────────────────────────────────────────


@celery_app.task(bind=True, name="run_test_suite", max_retries=2)
def run_test_suite_task(self, run_id: str) -> dict:
    """Execute every test case in a suite and persist results one by one.

    The TestRun record must already exist in the database before this task
    is dispatched.
    """

    async def _run():
        SessionLocal = _make_session()
        async with SessionLocal() as db:
            from sqlalchemy import select

            from app.core.security import decrypt_api_key
            from app.models.model_config import ModelConfig
            from app.models.test_suite import TestCase, TestCaseResult, TestRun, TestRunStatus
            from app.services.litellm_service import LiteLLMService
            from app.services.model_utils import get_litellm_model_id, score_response

            run_row = await db.execute(select(TestRun).where(TestRun.id == run_id))
            run = run_row.scalar_one_or_none()
            if not run:
                return {"error": f"TestRun {run_id} not found"}

            config_row = await db.execute(
                select(ModelConfig).where(ModelConfig.id == run.model_config_id)
            )
            model_config = config_row.scalar_one_or_none()
            if not model_config:
                run.status = TestRunStatus.FAILED
                await db.commit()
                return {"error": f"Model config '{run.model_config_id}' not found"}

            cases_row = await db.execute(
                select(TestCase).where(TestCase.suite_id == run.suite_id)
            )
            cases = list(cases_row.scalars().all())

            llm = LiteLLMService()
            api_key = None
            if model_config.api_key_encrypted:
                api_key = decrypt_api_key(model_config.api_key_encrypted)
            model_id = get_litellm_model_id(model_config.provider, model_config.model_id)

            try:
                run.status = TestRunStatus.RUNNING
                await db.commit()

                latencies: list[float] = []
                total_cost = 0.0
                pass_count = 0
                fail_count = 0

                for case in cases:
                    try:
                        call = llm.call_model(
                            model_id=model_id,
                            prompt=case.input,
                            api_key=api_key,
                            base_url=model_config.base_url,
                        )
                        passed = score_response(call.response, case.expected_output, case.expected_tags)
                        case_result = TestCaseResult(
                            run_id=run_id,
                            case_id=case.id,
                            response=call.response,
                            passed=passed,
                            latency_ms=call.latency_ms,
                            cost_usd=call.cost_usd,
                        )
                    except Exception as exc:
                        passed = False
                        case_result = TestCaseResult(
                            run_id=run_id,
                            case_id=case.id,
                            passed=False,
                            error=str(exc),
                        )

                    db.add(case_result)

                    if passed:
                        pass_count += 1
                    else:
                        fail_count += 1
                    if case_result.latency_ms:
                        latencies.append(case_result.latency_ms)
                    if case_result.cost_usd:
                        total_cost += case_result.cost_usd

                    # Update run counters after each case so SSE can show progress
                    run.pass_count = pass_count
                    run.fail_count = fail_count
                    await db.commit()

                run.avg_latency_ms = statistics.mean(latencies) if latencies else None
                run.total_cost_usd = total_cost
                run.status = TestRunStatus.COMPLETED
                await db.commit()
                return {"status": "completed", "run_id": run_id}

            except Exception as exc:
                try:
                    run.status = TestRunStatus.FAILED
                    await db.commit()
                except Exception:
                    pass
                raise self.retry(exc=exc, countdown=5) from exc

    return asyncio.run(_run())
