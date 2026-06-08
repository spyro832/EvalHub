import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.evaluation import Evaluation

router = APIRouter()


async def _evaluation_stream(evaluation_id: str, db: AsyncSession):
    """Stream evaluation status updates as Server-Sent Events."""
    max_polls = 60  # 60 seconds max
    for _ in range(max_polls):
        evaluation = await db.get(Evaluation, evaluation_id)
        if not evaluation:
            yield f"data: {json.dumps({'error': 'Evaluation not found'})}\n\n"
            return

        payload = {
            "id": evaluation.id,
            "status": evaluation.status.value,
            "result_count": len(evaluation.results),
        }
        yield f"data: {json.dumps(payload)}\n\n"

        if evaluation.status.value in ("completed", "failed"):
            return

        await asyncio.sleep(1)

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
