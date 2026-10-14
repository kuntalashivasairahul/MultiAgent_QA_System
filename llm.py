"""Cached Groq models with a shared request limiter per model; TPM errors use SDK retries."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.exceptions import OutputParserException
from langchain_core.rate_limiters import InMemoryRateLimiter

load_dotenv(Path(__file__).resolve().parent / ".env")
os.environ.setdefault("LANGSMITH_TRACING", "false")

GEN_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
JUDGE_MODEL = os.environ.get("GROQ_JUDGE_MODEL", "openai/gpt-oss-20b")
MAX_RETRIES = int(os.environ.get("GROQ_MAX_RETRIES", "8"))
REQUESTS_PER_SECOND = float(os.environ.get("GROQ_RPS", "0.25"))
if MAX_RETRIES < 0 or not 0 < REQUESTS_PER_SECOND < float("inf"):
    raise ValueError("GROQ_MAX_RETRIES must be non-negative and GROQ_RPS must be finite and positive")


@lru_cache(maxsize=4)
def _limiter(model: str) -> InMemoryRateLimiter:
    return InMemoryRateLimiter(
        requests_per_second=REQUESTS_PER_SECOND,
        check_every_n_seconds=0.1, max_bucket_size=1,
    )


@lru_cache(maxsize=8)
def get_llm(
    temperature: float = 0.0, model: str | None = None, reasoning_effort: str | None = None,
) -> BaseChatModel:
    selected = model or GEN_MODEL
    kwargs = {"reasoning_effort": reasoning_effort} if reasoning_effort else {}
    return init_chat_model(
        selected, model_provider="groq", temperature=temperature, timeout=120,
        max_tokens=4096, max_retries=MAX_RETRIES,
        rate_limiter=_limiter(selected), **kwargs,
    )


def structured(schema, temperature: float = 0.0, model: str | None = None, reasoning_effort: str | None = None):
    """JSON schema output avoids intermittent tool-call failures on the chosen models."""
    return get_llm(temperature, model=model, reasoning_effort=reasoning_effort).with_structured_output(
        schema, method="json_schema",
    ).with_retry(retry_if_exception_type=(OutputParserException,), stop_after_attempt=3)
