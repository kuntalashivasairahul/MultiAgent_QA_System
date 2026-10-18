"""Retrieval, Reasoning and Judge roles with one quality-driven retrieval retry."""
import math
import os
from itertools import zip_longest
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from pydantic import Field

import graph_v1
import graph_v2
import v3_llm
from retrieval import HYBRID_LIMITS, get_hybrid_context
from state import QAState, question_text

USES_RETRIEVAL = True
SUPPORTS_CHECKPOINTS = True
RETRIEVAL_K = HYBRID_LIMITS["max_chunks"]
CONTEXT_LIMITS = dict(HYBRID_LIMITS)
THRESHOLD = float(os.environ.get("QA_QUALITY_THRESHOLD", "0.8"))
MAX_ATTEMPTS = 2


class QualityVerdict(graph_v2.EvidenceCheck):
    confidence: float = Field(ge=0, le=1, strict=True, allow_inf_nan=False,
                              description="Rubric quality score, not a calibrated probability")
    retry_query: str = Field(max_length=256, description="Missing aspect to search; empty if none")


class V3State(QAState, total=False):
    attempt_count: int
    retrieval_query: str
    quality: dict
    history: list[dict]
    new_document_ids: list[str]
    support: dict
    draft: dict | None


def runtime_inputs() -> dict:
    return {**v3_llm.profile(), "quality_threshold": THRESHOLD, "max_attempts": MAX_ATTEMPTS,
            "score_scope": "uncalibrated rubric quality, not probability", "retry_policy": "missing-aspect-new-evidence"}


def initialize(state: V3State) -> dict:
    question = question_text(state).strip()
    if len(question) > 4000:
        raise ValueError("question must be at most 4000 characters")
    return {"question": question, "attempt_count": 0, "retrieval_query": question,
            "history": [], "documents": [], "citations": [], "generation": graph_v2.REFUSAL,
            "quality": {}, "support": {}, "draft": None, "new_document_ids": []}


def retrieve(state: V3State) -> dict:
    previous = state["documents"]
    seen = tuple(d.id for d in previous)
    query = state["question"]
    if state["attempt_count"]:
        aspect = state["quality"]["retry_query"].strip() or "exact definition and supporting API details"
        query += "\nMissing aspect: " + aspect
    fresh = get_hybrid_context(query, exclude_ids=seen)
    cited = {previous[c["id"] - 1].id for c in state.get("citations", [])}
    retained = sorted(previous, key=lambda doc: doc.id not in cited)
    candidates = [d for pair in zip_longest(fresh, retained) for d in pair if d is not None] if previous else fresh
    documents, used, characters = [], set(), 0
    for doc in candidates:
        if doc.id in used or len(documents) == RETRIEVAL_K:
            continue
        if characters + len(doc.page_content) > HYBRID_LIMITS["max_document_text_characters"]:
            continue
        documents.append(doc)
        used.add(doc.id)
        characters += len(doc.page_content)
    return {"documents": documents, "attempt_count": state["attempt_count"] + 1,
            "retrieval_query": query, "citations": [], "generation": graph_v2.REFUSAL,
            "new_document_ids": [d.id for d in documents if d.id not in seen]}


def reason(state: V3State) -> dict:
    if not state["documents"]:
        return {"generation": graph_v2.REFUSAL, "citations": []}
    return graph_v1.generate(state, chain=v3_llm.structured(graph_v1.GroundedAnswer))


def judge(state: V3State) -> dict:
    if state["generation"] == graph_v2.REFUSAL:
        quality = QualityVerdict(passed=False, confidence=0.0, reason="No supported answer was generated.",
                                 quotes=[], retry_query=state["question"][:256]).model_dump()
    else:
        quality = graph_v2.check(
            "Assess answer quality for the ORIGINAL question using ONLY the cited documents. "
            "passed is true only if the answer completely addresses the exact entity/SDK/scope and EVERY claim is supported. "
            "Score confidence as rubric quality: 1.0 fully supported and complete; 0.5 partial coverage; 0.0 unsupported/wrong scope. "
            "This score is not a probability. Public examples cannot establish private configuration. "
            "A concise answer can be complete; do not require details the question did not ask for. "
            "A similar command or term does not prove the requested operation or scope. "
            "retry_query must be search keywords for missing evidence, or empty if none; never copy these instructions. "
            "Quote literal evidence supporting your decision; a high score cannot excuse unsupported claims.",
            state["question"], state["documents"], answer=state["generation"],
            ids=[c["id"] for c in state["citations"]],
            chain=v3_llm.structured(QualityVerdict, judge=True),
        )
    audit = {"attempt": state["attempt_count"], "query": state["retrieval_query"],
             "documents": [{"id": d.id, "text": d.page_content, "metadata": d.metadata} for d in state["documents"]],
             "generation": state["generation"], "citations": state["citations"], "quality": quality,
             "new_document_ids": state["new_document_ids"]}
    return {"quality": quality, "history": [*state["history"], audit]}


def accepted(state: V3State, threshold: float) -> bool:
    return (state["generation"] != graph_v2.REFUSAL and state["quality"]["passed"]
            and state["quality"]["confidence"] >= threshold)


def build_graph(*, checkpointer=None, threshold: float = THRESHOLD):
    if isinstance(threshold, bool) or not math.isfinite(threshold) or not 0 < threshold <= 1:
        raise ValueError("quality threshold must be finite and in (0, 1]")

    def route(state):
        return "finish" if accepted(state, threshold) or state["attempt_count"] >= MAX_ATTEMPTS else "retrieval"

    def finish(state):
        if accepted(state, threshold):
            return {"support": state["quality"], "draft": None}
        return {"support": state["quality"],
                "draft": {"generation": state["generation"], "citations": state["citations"]},
                "generation": graph_v2.REFUSAL, "citations": []}

    builder = StateGraph(V3State)
    for name, node in (("initialize", initialize), ("retrieval", retrieve), ("reasoning", reason),
                       ("judge", judge), ("finish", finish)):
        builder.add_node(name, node)
    builder.add_edge(START, "initialize")
    builder.add_edge("initialize", "retrieval")
    builder.add_edge("retrieval", "reasoning")
    builder.add_edge("reasoning", "judge")
    builder.add_conditional_edges("judge", route, {"retrieval": "retrieval", "finish": "finish"})
    builder.add_edge("finish", END)
    return builder.compile(checkpointer=checkpointer)


graph = build_graph()
