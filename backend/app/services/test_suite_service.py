import statistics

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_api_key
from app.models.model_config import ModelConfig
from app.models.test_suite import TestCase, TestCaseResult, TestRun, TestRunStatus, TestSuite
from app.services.litellm_service import LiteLLMService
from app.services.model_utils import get_litellm_model_id, score_response


class TestSuiteService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.llm = LiteLLMService()

    async def run_suite(self, suite_id: str, model_config_id: str) -> TestRun:
        suite = await self.db.get(TestSuite, suite_id)
        if not suite:
            raise ValueError(f"Test suite '{suite_id}' not found")

        model_config = await self.db.get(ModelConfig, model_config_id)
        if not model_config:
            raise ValueError(f"Model config '{model_config_id}' not found")

        run = TestRun(
            suite_id=suite_id,
            model_config_id=model_config_id,
            status=TestRunStatus.RUNNING,
        )
        self.db.add(run)
        await self.db.flush()

        api_key = None
        if model_config.api_key_encrypted:
            api_key = decrypt_api_key(model_config.api_key_encrypted)

        model_id = get_litellm_model_id(model_config.provider, model_config.model_id)

        latencies: list[int] = []
        total_cost = 0.0
        pass_count = 0
        fail_count = 0

        for case in suite.cases:
            case_result = await self._run_case(
                run_id=run.id,
                case=case,
                model_id=model_id,
                api_key=api_key,
                base_url=model_config.base_url,
            )
            self.db.add(case_result)

            if case_result.passed:
                pass_count += 1
            else:
                fail_count += 1
            if case_result.latency_ms:
                latencies.append(case_result.latency_ms)
            if case_result.cost_usd:
                total_cost += case_result.cost_usd

        run.pass_count = pass_count
        run.fail_count = fail_count
        run.avg_latency_ms = statistics.mean(latencies) if latencies else None
        run.total_cost_usd = total_cost
        run.status = TestRunStatus.COMPLETED

        await self.db.commit()
        await self.db.refresh(run)
        return run

    async def _run_case(
        self,
        run_id: str,
        case: TestCase,
        model_id: str,
        api_key: str | None,
        base_url: str | None,
    ) -> TestCaseResult:
        try:
            result = self.llm.call_model(
                model_id=model_id,
                prompt=case.input,
                api_key=api_key,
                base_url=base_url,
            )
            passed = score_response(result.response, case.expected_output, case.expected_tags)
            return TestCaseResult(
                run_id=run_id,
                case_id=case.id,
                response=result.response,
                passed=passed,
                latency_ms=result.latency_ms,
                cost_usd=result.cost_usd,
            )
        except Exception as exc:
            return TestCaseResult(
                run_id=run_id,
                case_id=case.id,
                passed=False,
                error=str(exc),
            )

    async def list_runs(self, suite_id: str) -> list[TestRun]:
        result = await self.db.execute(
            select(TestRun).where(TestRun.suite_id == suite_id).order_by(TestRun.created_at.desc())
        )
        return list(result.scalars().all())
