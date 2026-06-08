from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.test_suite import TestCase, TestSuite
from app.schemas.test_suite import TestRunOut, TestRunRequest, TestSuiteCreate, TestSuiteOut
from app.services.test_suite_service import TestSuiteService

router = APIRouter()


@router.get("", response_model=list[TestSuiteOut])
async def list_test_suites(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TestSuite).order_by(TestSuite.updated_at.desc()))
    return list(result.scalars().all())


@router.post("", response_model=TestSuiteOut, status_code=status.HTTP_201_CREATED)
async def create_test_suite(data: TestSuiteCreate, db: AsyncSession = Depends(get_db)):
    suite = TestSuite(
        name=data.name,
        description=data.description,
        category=data.category,
    )
    db.add(suite)
    await db.flush()

    for case_data in data.cases:
        case = TestCase(suite_id=suite.id, **case_data.model_dump())
        db.add(case)

    await db.commit()
    await db.refresh(suite)
    return suite


@router.get("/{suite_id}", response_model=TestSuiteOut)
async def get_test_suite(suite_id: str, db: AsyncSession = Depends(get_db)):
    suite = await db.get(TestSuite, suite_id)
    if not suite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")
    return suite


@router.post("/{suite_id}/run", response_model=TestRunOut, status_code=status.HTTP_201_CREATED)
async def run_test_suite(
    suite_id: str,
    data: TestRunRequest,
    db: AsyncSession = Depends(get_db),
):
    service = TestSuiteService(db)
    try:
        run = await service.run_suite(suite_id=suite_id, model_config_id=data.model_config_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return run


@router.get("/{suite_id}/runs", response_model=list[TestRunOut])
async def list_runs(suite_id: str, db: AsyncSession = Depends(get_db)):
    service = TestSuiteService(db)
    return await service.list_runs(suite_id)


@router.delete("/{suite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_suite(suite_id: str, db: AsyncSession = Depends(get_db)):
    suite = await db.get(TestSuite, suite_id)
    if not suite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")
    await db.delete(suite)
    await db.commit()

