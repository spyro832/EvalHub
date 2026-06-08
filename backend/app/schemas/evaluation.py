from datetime import datetime

from pydantic import BaseModel, Field

from app.models.evaluation import EvaluationStatus


class EvaluationCreate(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=100_000)
    model_ids: list[str] = Field(..., min_length=1)
    name: str | None = Field(None, max_length=200)


class EvalResultOut(BaseModel):
    id: str
    model_config_id: str
    response: str | None
    latency_ms: int | None
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float | None
    error: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationOut(BaseModel):
    id: str
    name: str | None
    prompt: str
    status: EvaluationStatus
    results: list[EvalResultOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EvaluationListItem(BaseModel):
    id: str
    name: str | None
    prompt: str
    status: EvaluationStatus
    created_at: datetime

    model_config = {"from_attributes": True}
