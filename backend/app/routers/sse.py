"""
Server-Sent Events (SSE) endpoints for real-time progress streaming.

Both evaluation and test-suite-run streams poll the database every second
and push status/progress updates to the client.  The SSE connection stays
open until the operation finishes (completed/failed) or the 5-minute
timeout is reached.
"""

import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.evaluation import EvalResult, Evaluation
from app.models.test_suite import TestCaseResult, TestRun

router = APIRouter()

_POLL_INTERVAL = 1  # seconds between DB polls
_MAX_POLLS = 300    # 5-minute ceiling (300 × 1 s)


# ── Evaluation stream ──────────────────────────────────────────────────────────


async def _evaluation_stream(evaluation_id: str, db: AsyncSession):
    """Yield SSE events for an evaluation until it completes or times out."""
    for _ in range(_MAX_POLLS):
        # Fresh SELECT each iteration — never use the identity-map cache
        row = await db.execute(select(Evaluation).where(Evaluation.id == evaluation_id))
        evaluation = row.scalar_one_or_none()

        if not evaluation:
            yield f"data: {json.dumps({'error': 'Evaluation not found'})}\n\n"
            return

        # Count how many results already have a response (or an error)
        completed_row = await db.execute(
            select(func.count()).where(
                EvalResult.evaluation_id == evaluation_id,
                (EvalResult.response.isnot(None)) | (EvalResult.error.isnot(None)),
            )
        )
        completed_count = completed_row.scalar_one()
        total = len(evaluation.results)  # loaded via selectin

        payload = {
            "id": evaluation.id,
            "status": evaluation.status.value,
            "completed": completed_count,
            "total": total,
        }
        yield f"data: {json.dumps(payload)}\n\n"

        if evaluation.status.value in ("completed", "failed"):
            return

        await asyncio.sleep(_POLL_INTERVAL)
        # Expire session so next iteration re-fetches from DB
        db.expire_all()

    yield f"data: {json.dumps({'error': 'timeout'})}\n\n"


@router.get("/{evaluation_id}/stream")
async def stream_evaluation(
    evaluation_id: str,
    db: AsyncSession = Depends(get_db),
):
    return StreamingResponse(
        _evaluation_stream(evaluation_id, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Test-suite run stream ──────────────────────────────────────────────────────


async def _run_stream(run_id: str, db: AsyncSession):
    """Yield SSE events for a test-suite run until it completes or times out."""
    # Fetch suite's case count once upfront
    run_row = await db.execute(select(TestRun).where(TestRun.id == run_id))
    run = run_row.scalar_one_or_none()
    if not run:
        yield f"data: {json.dumps({'error': 'TestRun not found'})}\n\n"
        return

    total_cases_row = await db.execute(
        select(func.count(TestCaseResult.id)).where(TestCaseResult.run_id == run_id)
    )

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

        await asyncio.sleep(_POLL_INTERVAL)
        db.expire_all()

    yield f"data: {json.dumps({'error': 'timeout'})}\n\n"
