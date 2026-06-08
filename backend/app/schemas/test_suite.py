from datetime import datetime

from pydantic import BaseModel, Field

from app.models.test_suite import TestRunStatus


class TestCaseCreate(BaseModel):
    input: str = Field(..., min_length=1, max_length=100_000)
    expected_output: str | None = None
    expected_tags: str | None = None


class TestSuiteCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    cases: list[TestCaseCreate] = []


class TestCaseOut(BaseModel):
    id: str
    input: str
    expected_output: str | None
    expected_tags: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TestSuiteOut(BaseModel):
    id: str
    name: str
    description: str | None
    category: str | None
    cases: list[TestCaseOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestRunRequest(BaseModel):
    model_config_id: str


class TestRunOut(BaseModel):
    id: str
    suite_id: str
    model_config_id: str
    status: TestRunStatus
    pass_count: int
    fail_count: int
    avg_latency_ms: float | None
    total_cost_usd: float
    created_at: datetime

    model_config = {"from_attributes": True}
