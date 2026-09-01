"""Groq chat model, throttled to stay inside the free tier."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.rate_limiters import InMemoryRateLimiter

load_dotenv()


def get_llm(temperature: float = 0.0) -> BaseChatModel:
    """A rate-limited Groq model.

    The limiter matters more than a fallback chain here: an eval run fires
    hundreds of calls in a burst, and throttling ahead of the limit avoids
    the 429s that a fallback could only react to after the fact.
    """
    return init_chat_model(
        os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
        model_provider="groq",
        temperature=temperature,
        rate_limiter=InMemoryRateLimiter(
            requests_per_second=float(os.environ.get("GROQ_RPS", "0.4")),
            check_every_n_seconds=0.1,
            max_bucket_size=5,
        ),
    )


def structured(schema, temperature: float = 0.0):
    """Structured output via JSON schema rather than tool calling.

    gpt-oss is a reasoning model: given a long passage it often replies in prose
    instead of invoking the tool, and Groq rejects that with `tool_use_failed`.
    The failure is intermittent, which is worse than consistent — it silently
    thins results rather than breaking loudly. `json_schema` is the model's
    native structured-output path and does not depend on tool-call compliance.
    """
    return get_llm(temperature).with_structured_output(schema, method="json_schema")
