import asyncio

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="run_evaluation")
def run_evaluation(self, evaluation_id: str) -> dict:
    """
    Background task to run an evaluation asynchronously.
    Used for large test suites that would otherwise time out the HTTP request.
    """
    from app.core.database import AsyncSessionLocal
    from app.models.evaluation import Evaluation, EvaluationStatus
    from app.services.eval_service import EvalService

    async def _run():
        async with AsyncSessionLocal() as db:
            evaluation = await db.get(Evaluation, evaluation_id)
            if not evaluation:
                return {"error": f"Evaluation {evaluation_id} not found"}

            service = EvalService(db)
            try:
                evaluation.status = EvaluationStatus.RUNNING
                await db.commit()

                # Re-run all model calls for this evaluation
                for result in evaluation.results:
                    updated = await service._run_single_model(
                        evaluation_id, result.model_config_id, evaluation.prompt
                    )
                    result.response = updated.response
                    result.latency_ms = updated.latency_ms
                    result.input_tokens = updated.input_tokens
                    result.output_tokens = updated.output_tokens
                    result.cost_usd = updated.cost_usd
                    result.error = updated.error

                evaluation.status = EvaluationStatus.COMPLETED
                await db.commit()
                return {"status": "completed", "evaluation_id": evaluation_id}
            except Exception as exc:
                evaluation.status = EvaluationStatus.FAILED
                await db.commit()
                raise self.retry(exc=exc, countdown=5, max_retries=2) from exc

    return asyncio.run(_run())
