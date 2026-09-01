"""State shared by every graph version.

`retries` is unused before v2. It is declared now so that adding the
corrective loop does not require migrating persisted state.
"""
from __future__ import annotations

from typing import TypedDict

from langchain_core.documents import Document


class QAState(TypedDict, total=False):
    question: str
    documents: list[Document]
    generation: str
    retries: int
