from datetime import datetime

from pydantic import BaseModel, Field


class PromptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=100_000)
    description: str | None = None
    tags: str | None = None


class PromptOut(BaseModel):
    id: str
    name: str
    content: str
    description: str | None
    version: int
    parent_id: str | None
    tags: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
