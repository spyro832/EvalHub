from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_api_key
from app.models.evaluation import EvalResult, Evaluation, EvaluationStatus
from app.models.model_config import ModelConfig
from app.schemas.evaluation import EvaluationCreate
from app.services.litellm_service import LiteLLMService


class EvalService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.llm = LiteLLMService()

    async def create_evaluation(self, data: EvaluationCreate) -> Evaluation:
        evaluation = Evaluation(
            name=data.name,
            prompt=data.prompt,
            status=EvaluationStatus.RUNNING,
        )
        self.db.add(evaluation)
        await self.db.flush()

        for model_config_id in data.model_ids:
            result = await self._run_single_model(evaluation.id, model_config_id, data.prompt)
            self.db.add(result)

        evaluation.status = EvaluationStatus.COMPLETED
        await self.db.commit()
        await self.db.refresh(evaluation)
        return evaluation

    async def _run_single_model(
        self, evaluation_id: str, model_config_id: str, prompt: str
    ) -> EvalResult:
        model_config = await self.db.get(ModelConfig, model_config_id)
        if not model_config:
            return EvalResult(
                evaluation_id=evaluation_id,
                model_config_id=model_config_id,
                error=f"Model config '{model_config_id}' not found",
            )

        try:
            api_key = None
            if model_config.api_key_encrypted:
                api_key = decrypt_api_key(model_config.api_key_encrypted)

            # LiteLLM requires provider-prefixed model IDs for some providers
            model_id = model_config.model_id
            if model_config.provider == "ollama" and not model_id.startswith("ollama/"):
                model_id = f"ollama/{model_id}"

            result = self.llm.call_model(
                model_id=model_id,
                prompt=prompt,
                api_key=api_key,
                base_url=model_config.base_url,
            )

            return EvalResult(
                evaluation_id=evaluation_id,
                model_config_id=model_config_id,
                response=result.response,
                latency_ms=result.latency_ms,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                cost_usd=result.cost_usd,
            )
        except Exception as exc:
            return EvalResult(
                evaluation_id=evaluation_id,
                model_config_id=model_config_id,
                error=str(exc),
            )

    async def list_evaluations(self, skip: int = 0, limit: int = 50) -> list[Evaluation]:
        result = await self.db.execute(
            select(Evaluation).order_by(Evaluation.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_evaluation(self, evaluation_id: str) -> Evaluation | None:
        return await self.db.get(Evaluation, evaluation_id)
