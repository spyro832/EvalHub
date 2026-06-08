from datetime import datetime

from pydantic import BaseModel, Field


class ModelConfigCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider: str = Field(..., min_length=1, max_length=50)
    model_id: str = Field(..., min_length=1, max_length=100)
    api_key: str | None = Field(None)
    base_url: str | None = Field(None, max_length=500)
    is_local: bool = False
    cost_per_input_token: float | None = None
    cost_per_output_token: float | None = None


class ModelConfigOut(BaseModel):
    id: str
    name: str
    provider: str
    model_id: str
    base_url: str | None
    is_active: bool
    is_local: bool
    cost_per_input_token: float | None
    cost_per_output_token: float | None
    created_at: datetime

    model_config = {"from_attributes": True}
