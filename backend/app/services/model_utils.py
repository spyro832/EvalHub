"""
Shared utilities for model ID resolution and response scoring.
Used by EvalService, TestSuiteService, and benchmarks router.
"""

_PROVIDER_PREFIXES: dict[str, str] = {
    "ollama": "ollama/",
    "huggingface": "huggingface/",
}


def get_litellm_model_id(provider: str, model_id: str) -> str:
    """Resolve the LiteLLM model string for a given provider + model_id.

    Ollama and HuggingFace require a provider prefix (e.g. "ollama/llama3.2").
    All other providers (OpenAI, Anthropic, Google, …) pass the model_id through as-is.
    """
    prefix = _PROVIDER_PREFIXES.get(provider, "")
    if prefix and not model_id.startswith(prefix):
        return f"{prefix}{model_id}"
    return model_id


def score_response(
    response: str,
    expected_output: str | None,
    expected_tags: str | None,
) -> bool:
    """Score an LLM response against expected criteria.

    Rules (in priority order):
    1. If *expected_output* is set → pass iff it appears as a substring (case-insensitive).
    2. Else if *expected_tags* is set → pass iff ALL comma-separated tags appear (case-insensitive).
    3. If neither criterion is set → pass iff the response is non-empty (free-form item).
    """
    response_lower = response.lower()

    if expected_output:
        return expected_output.lower() in response_lower

    if expected_tags:
        tags = [t.strip().lower() for t in expected_tags.split(",") if t.strip()]
        if tags:
            return all(tag in response_lower for tag in tags)

    # No criteria — treat as pass if there's any response
    return bool(response.strip())
