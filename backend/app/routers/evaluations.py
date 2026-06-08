from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.evaluation import EvaluationCreate, EvaluationListItem, EvaluationOut
from app.services.eval_service import EvalService

router = APIRouter()


@router.post("", response_model=EvaluationOut, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    data: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
):
    service = EvalService(db)
    return await service.create_evaluation(data)


@router.get("", response_model=list[EvaluationListItem])
async def list_evaluations(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    service = EvalService(db)
    return await service.list_evaluations(skip=skip, limit=limit)


@router.get("/{evaluation_id}", response_model=EvaluationOut)
async def get_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
):
    service = EvalService(db)
    evaluation = await service.get_evaluation(evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")
    return evaluation
