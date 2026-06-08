import time
from dataclasses import dataclass

import litellm
from litellm import completion


@dataclass
class ModelCallResult:
    response: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost_usd: float
    model_id: str


class LiteLLMService:
    """Unified interface for calling AI models via LiteLLM."""

    def call_model(
        self,
        model_id: str,
        prompt: str,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> ModelCallResult:
        start = time.monotonic()

        kwargs: dict = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
        }
        if api_key:
            kwargs["api_key"] = api_key
        if base_url:
            kwargs["base_url"] = base_url

        response = completion(**kwargs)
        latency_ms = int((time.monotonic() - start) * 1000)

        content = response.choices[0].message.content or ""
        usage = response.usage
        cost = litellm.completion_cost(completion_response=response)

        return ModelCallResult(
            response=content,
            latency_ms=latency_ms,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
            cost_usd=float(cost) if cost else 0.0,
            model_id=model_id,
        )
