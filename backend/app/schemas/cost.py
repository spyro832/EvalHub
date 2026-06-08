from pydantic import BaseModel


class CostSummary(BaseModel):
    total_usd: float
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int


class DailyCostItem(BaseModel):
    date: str
    total_usd: float
    total_calls: int
