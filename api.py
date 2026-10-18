"""Local public-corpus QA API. Start with: uv run uvicorn api:app --host 127.0.0.1."""
import logging
import threading
import time
from typing import Annotated

from fastapi import FastAPI, HTTPException
from langchain_core.callbacks import get_usage_metadata_callback
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

import graph_v3
import v3_llm
from graph_v2 import REFUSAL


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1, max_length=4000)]


class Citation(BaseModel):
    id: int = Field(ge=1)
    source: str
    chunk_id: str


class AnswerQuality(graph_v3.QualityVerdict):
    validation_failures: list[dict] = Field(default_factory=list)


class AskResponse(BaseModel):
    answer: str
    refused: bool
    citations: list[Citation]
    quality: AnswerQuality
    attempt_count: int = Field(ge=1, le=2)
    model_profile: dict
    seconds: float
    usage: dict


def create_app(pipeline=None) -> FastAPI:
    app = FastAPI(title="Temporal QA v3", version="3.0", description="Local public-document prototype; no authentication or tenant isolation.")
    pipeline = pipeline if pipeline is not None else graph_v3.graph
    busy = threading.Lock()

    @app.get("/health")
    def health():
        return {"status": "ok", "scope": "process_only", "version": "3.0", "model_profile": v3_llm.profile()}

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest):
        if not busy.acquire(blocking=False):
            raise HTTPException(status_code=429, detail={"code": "busy", "message": "One inference request at a time."})
        try:
            started = time.perf_counter()
            with get_usage_metadata_callback() as usage:
                output = pipeline.invoke({"question": request.question})
            return AskResponse(answer=output["generation"], refused=output["generation"] == REFUSAL,
                               citations=output["citations"], quality=output["quality"],
                               attempt_count=output["attempt_count"], model_profile=graph_v3.runtime_inputs(),
                               seconds=time.perf_counter() - started, usage=usage.usage_metadata)
        except FileNotFoundError:
            raise HTTPException(status_code=503, detail={"code": "index_unavailable"}) from None
        except ValueError:
            raise HTTPException(status_code=502, detail={"code": "invalid_pipeline_output"}) from None
        except Exception as exc:
            logging.getLogger(__name__).error("QA request failed: %s", type(exc).__name__)
            raise HTTPException(status_code=503, detail={"code": "backend_unavailable"}) from None
        finally:
            busy.release()

    return app


app = create_app()
