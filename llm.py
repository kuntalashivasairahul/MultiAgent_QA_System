"""Groq chat models, throttled and retried to survive the free tier.

The binding constraint is **tokens per minute, not requests per minute**: Groq's
free tier allows 8,000 TPM per model, and a single v1 call carrying five
retrieved chunks costs roughly 4,500 tokens. `InMemoryRateLimiter` counts
requests and explicitly ignores request size, so no RPS setting can keep a
context-heavy call inside a TPM budget. Two things actually help:

1. **Retries.** The token bucket refills continuously (`x-ratelimit-reset-tokens`
   is well under a second), so a 429 usually clears by waiting briefly. The Groq
   SDK honours `retry-after`.
2. **Separate buckets.** Limits are per model, so running judges on a different
   model from generation gives an eval two independent 8,000 TPM budgets rather
   than one contended budget.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.rate_limiters import InMemoryRateLimiter

load_dotenv()

GEN_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
# Judges make binary calls against a supplied reference, which does not need the
# larger model — and putting them on their own model doubles the token budget.
# Opt in explicitly: defaulting to it would silently downgrade golden-set drafting.
JUDGE_MODEL = os.environ.get("GROQ_JUDGE_MODEL", "openai/gpt-oss-20b")


def get_llm(
    temperature: float = 0.0,
    model: str | None = None,
    reasoning_effort: str | None = None,
) -> BaseChatModel:
    kwargs = {}
    if reasoning_effort:
        # Reasoning tokens count against TPM. Binary verdicts do not need depth.
        kwargs["reasoning_effort"] = reasoning_effort
    return init_chat_model(
        model or GEN_MODEL,
        model_provider="groq",
        temperature=temperature,
        max_retries=int(os.environ.get("GROQ_MAX_RETRIES", "8")),
        rate_limiter=InMemoryRateLimiter(
            requests_per_second=float(os.environ.get("GROQ_RPS", "0.25")),
            check_every_n_seconds=0.1,
            max_bucket_size=2,
        ),
        **kwargs,
    )


def structured(
    schema,
    temperature: float = 0.0,
    model: str | None = None,
    reasoning_effort: str | None = None,
):
    """Structured output via JSON schema rather than tool calling.

    gpt-oss is a reasoning model: given a long passage it often replies in prose
    instead of invoking the tool, and Groq rejects that with `tool_use_failed`.
    The failure is intermittent, which is worse than consistent — it silently
    thins results rather than breaking loudly. `json_schema` is the model's
    native structured-output path and does not depend on tool-call compliance.
    """
    return get_llm(
        temperature, model=model, reasoning_effort=reasoning_effort
    ).with_structured_output(schema, method="json_schema")
