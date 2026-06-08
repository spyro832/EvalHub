from datetime import datetime

from pydantic import BaseModel, Field


class BenchmarkItemCreate(BaseModel):
    input: str = Field(..., min_length=1, max_length=100_000)
    expected_output: str | None = None
    expected_tags: str | None = None
    meta: dict | None = None


class BenchmarkCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    source_url: str | None = Field(None, max_length=500)
    author: str | None = Field(None, max_length=200)
    items: list[BenchmarkItemCreate] = []


class BenchmarkItemOut(BaseModel):
    id: str
    input: str
    expected_output: str | None
    expected_tags: str | None
    meta: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


class BenchmarkOut(BaseModel):
    id: str
    name: str
    description: str | None
    category: str | None
    source_url: str | None
    author: str | None
    item_count: int = 0
    items: list[BenchmarkItemOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_count(cls, obj):
        data = cls.model_validate(obj)
        data.item_count = len(obj.items)
        return data


# Used for JSON import: same shape as BenchmarkCreate but items are required
class BenchmarkImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    source_url: str | None = None
    author: str | None = None
    items: list[BenchmarkItemCreate] = Field(..., min_length=1)


class BenchmarkRunRequest(BaseModel):
    model_config_id: str
    item_limit: int | None = Field(None, ge=1, le=500)


class BenchmarkRunResult(BaseModel):
    benchmark_id: str
    model_config_id: str
    total_items: int
    pass_count: int
    fail_count: int
    pass_rate: float
    avg_latency_ms: float | None
    total_cost_usd: float
    results: list[dict]
