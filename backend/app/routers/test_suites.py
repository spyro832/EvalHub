import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.test_suite import TestCase, TestCaseResult, TestRun, TestRunStatus, TestSuite
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
    """Create a TestRun record and dispatch execution to a Celery worker.

    Returns immediately with status=pending. Stream progress via
    GET /{suite_id}/runs/{run_id}/stream.
    """
    from app.tasks.eval_tasks import run_test_suite_task

    suite = await db.get(TestSuite, suite_id)
    if not suite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")

    run = TestRun(
        suite_id=suite_id,
        model_config_id=data.model_config_id,
        status=TestRunStatus.PENDING,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    run_test_suite_task.delay(run.id)
    return run


@router.get("/{suite_id}/runs", response_model=list[TestRunOut])
async def list_runs(suite_id: str, db: AsyncSession = Depends(get_db)):
    service = TestSuiteService(db)
    return await service.list_runs(suite_id)


@router.get("/{suite_id}/runs/{run_id}/stream")
async def stream_run(
    suite_id: str,
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Stream test-suite run progress as Server-Sent Events (1 event/second)."""

    async def _stream():
        _MAX_POLLS = 300  # 5-minute ceiling
        for _ in range(_MAX_POLLS):
            run_row = await db.execute(select(TestRun).where(TestRun.id == run_id))
            run = run_row.scalar_one_or_none()
            if not run:
                yield f"data: {json.dumps({'error': 'TestRun not found'})}\n\n"
                return

            completed_row = await db.execute(
                select(func.count(TestCaseResult.id)).where(TestCaseResult.run_id == run_id)
            )
            completed_count = completed_row.scalar_one()

            payload = {
                "run_id": run.id,
                "status": run.status.value,
                "pass_count": run.pass_count,
                "fail_count": run.fail_count,
                "completed": completed_count,
            }
            yield f"data: {json.dumps(payload)}\n\n"

            if run.status.value in ("completed", "failed"):
                return

            await asyncio.sleep(1)
            db.expire_all()

        yield f"data: {json.dumps({'error': 'timeout'})}\n\n"

    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/{suite_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_test_suite(suite_id: str, db: AsyncSession = Depends(get_db)):
    suite = await db.get(TestSuite, suite_id)
    if not suite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test suite not found")
    await db.delete(suite)
    await db.commit()
