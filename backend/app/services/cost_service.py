from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.evaluation import EvalResult
from app.schemas.cost import CostSummary


class CostService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_summary(self) -> CostSummary:
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(EvalResult.cost_usd), 0).label("total_usd"),
                func.count(EvalResult.id).label("total_calls"),
                func.coalesce(func.sum(EvalResult.input_tokens), 0).label("total_input_tokens"),
                func.coalesce(func.sum(EvalResult.output_tokens), 0).label("total_output_tokens"),
            )
        )
        row = result.one()
        return CostSummary(
            total_usd=float(row.total_usd),
            total_calls=row.total_calls,
            total_input_tokens=row.total_input_tokens,
            total_output_tokens=row.total_output_tokens,
        )
