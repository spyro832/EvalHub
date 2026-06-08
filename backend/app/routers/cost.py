from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.cost import CostSummary
from app.services.cost_service import CostService

router = APIRouter()


@router.get("/summary", response_model=CostSummary)
async def get_cost_summary(db: AsyncSession = Depends(get_db)):
    service = CostService(db)
    return await service.get_summary()
