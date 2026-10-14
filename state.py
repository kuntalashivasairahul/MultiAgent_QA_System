"""The shared graph input/output contract."""
from __future__ import annotations

from typing import TypedDict
from langchain_core.documents import Document


class QAState(TypedDict, total=False):
    question: str
    documents: list[Document]
    generation: str
    citations: list[dict]


def question_text(state: QAState) -> str:
    question = state.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")
    return question
