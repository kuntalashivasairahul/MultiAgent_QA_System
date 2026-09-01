"""v0 — no retrieval. The contamination baseline.

If this scores well, the corpus is one the model already memorised and the
whole evaluation is measuring parametric knowledge rather than retrieval.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from llm import get_llm
from state import QAState

PROMPT = """You are answering questions about Temporal, the durable execution platform.

Answer from your own knowledge. If you do not know the answer, reply exactly:
I don't know.

Question: {question}"""


def answer(state: QAState) -> QAState:
    reply = get_llm().invoke(PROMPT.format(question=state["question"]))
    return {"generation": reply.content, "documents": []}


_builder = StateGraph(QAState)
_builder.add_node("answer", answer)
_builder.add_edge(START, "answer")
_builder.add_edge("answer", END)

graph = _builder.compile()
