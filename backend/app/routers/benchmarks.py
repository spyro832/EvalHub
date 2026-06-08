import json
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decrypt_api_key
from app.models.benchmark import Benchmark, BenchmarkItem
from app.models.model_config import ModelConfig
from app.schemas.benchmark import (
    BenchmarkCreate,
    BenchmarkImport,
    BenchmarkOut,
    BenchmarkRunRequest,
    BenchmarkRunResult,
)
from app.services.eval_service import _get_litellm_model_id
from app.services.litellm_service import LiteLLMService

router = APIRouter()
_llm = LiteLLMService()


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[BenchmarkOut])
async def list_benchmarks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Benchmark).order_by(Benchmark.updated_at.desc()))
    benchmarks = list(result.scalars().all())
    return [BenchmarkOut.from_orm_with_count(b) for b in benchmarks]


@router.post("", response_model=BenchmarkOut, status_code=status.HTTP_201_CREATED)
async def create_benchmark(data: BenchmarkCreate, db: AsyncSession = Depends(get_db)):
    benchmark = Benchmark(
        name=data.name,
        description=data.description,
        category=data.category,
        source_url=data.source_url,
        author=data.author,
    )
    db.add(benchmark)
    await db.flush()

    for item_data in data.items:
        db.add(BenchmarkItem(benchmark_id=benchmark.id, **item_data.model_dump()))

    await db.commit()
    await db.refresh(benchmark)
    return BenchmarkOut.from_orm_with_count(benchmark)


@router.get("/{benchmark_id}", response_model=BenchmarkOut)
async def get_benchmark(benchmark_id: str, db: AsyncSession = Depends(get_db)):
    benchmark = await db.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark not found")
    return BenchmarkOut.from_orm_with_count(benchmark)


@router.delete("/{benchmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_benchmark(benchmark_id: str, db: AsyncSession = Depends(get_db)):
    benchmark = await db.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark not found")
    await db.delete(benchmark)
    await db.commit()


# ── Import / Export ────────────────────────────────────────────────────────────

@router.post("/import", response_model=BenchmarkOut, status_code=status.HTTP_201_CREATED)
async def import_benchmark(data: BenchmarkImport, db: AsyncSession = Depends(get_db)):
    """Import a benchmark from JSON body (same format as export)."""
    benchmark = Benchmark(
        name=data.name,
        description=data.description,
        category=data.category,
        source_url=data.source_url,
        author=data.author,
    )
    db.add(benchmark)
    await db.flush()

    for item_data in data.items:
        db.add(BenchmarkItem(benchmark_id=benchmark.id, **item_data.model_dump()))

    await db.commit()
    await db.refresh(benchmark)
    return BenchmarkOut.from_orm_with_count(benchmark)


@router.get("/{benchmark_id}/export")
async def export_benchmark(benchmark_id: str, db: AsyncSession = Depends(get_db)):
    """Export a benchmark as a downloadable JSON file."""
    benchmark = await db.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark not found")

    payload = {
        "name": benchmark.name,
        "description": benchmark.description,
        "category": benchmark.category,
        "source_url": benchmark.source_url,
        "author": benchmark.author,
        "items": [
            {
                "input": item.input,
                "expected_output": item.expected_output,
                "expected_tags": item.expected_tags,
                "meta": item.meta,
            }
            for item in benchmark.items
        ],
    }

    filename = benchmark.name.lower().replace(" ", "_") + ".json"
    content = json.dumps(payload, indent=2, ensure_ascii=False)
    return StreamingResponse(
        StringIO(content),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Run ────────────────────────────────────────────────────────────────────────

@router.post("/{benchmark_id}/run", response_model=BenchmarkRunResult)
async def run_benchmark(
    benchmark_id: str,
    data: BenchmarkRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run a benchmark against a model config, returning pass/fail per item."""
    benchmark = await db.get(Benchmark, benchmark_id)
    if not benchmark:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Benchmark not found")

    model_config = await db.get(ModelConfig, data.model_config_id)
    if not model_config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model config not found")

    api_key = None
    if model_config.api_key_encrypted:
        api_key = decrypt_api_key(model_config.api_key_encrypted)

    model_id = _get_litellm_model_id(model_config.provider, model_config.model_id)

    items = list(benchmark.items)
    if data.item_limit:
        items = items[: data.item_limit]

    results = []
    total_latency = 0.0
    total_cost = 0.0
    pass_count = 0

    for item in items:
        call = None
        try:
            call = _llm.call_model(
                model_id=model_id,
                prompt=item.input,
                api_key=api_key,
                base_url=model_config.base_url,
            )
            response = call.response or ""
            passed = _score(item, response)
        except Exception as exc:
            response = f"ERROR: {exc}"
            passed = False

        if passed:
            pass_count += 1
        if call:
            total_latency += call.latency_ms or 0
            total_cost += call.cost_usd or 0

        results.append(
            {
                "item_id": item.id,
                "input": item.input,
                "response": response,
                "passed": passed,
                "latency_ms": call.latency_ms if call else None,
                "cost_usd": call.cost_usd if call else None,
            }
        )

    total = len(results)
    fail_count = total - pass_count
    avg_latency = (total_latency / total) if total else None

    return BenchmarkRunResult(
        benchmark_id=benchmark_id,
        model_config_id=data.model_config_id,
        total_items=total,
        pass_count=pass_count,
        fail_count=fail_count,
        pass_rate=round(pass_count / total, 4) if total else 0.0,
        avg_latency_ms=avg_latency,
        total_cost_usd=round(total_cost, 6),
        results=results,
    )


def _score(item: BenchmarkItem, response: str) -> bool:
    """Return True if the response satisfies the item's expected criteria."""
    response_lower = response.lower()
    if item.expected_output:
        if item.expected_output.lower() in response_lower:
            return True
    if item.expected_tags:
        tags = [t.strip() for t in item.expected_tags.split(",") if t.strip()]
        if tags and all(t.lower() in response_lower for t in tags):
            return True
    # If neither criterion set, treat as pass (free-form item)
    if not item.expected_output and not item.expected_tags:
        return True
    return False
