"""v1 — retrieve then generate. Two nodes, no branching.

The control group. It is intentionally simple, but not intentionally bad:
the prompt gets a fair refusal instruction, because v2's improvement must
come from graph structure rather than from sandbagging v1's prompt.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from llm import get_llm
from retrieval import format_docs, get_retriever
from state import QAState

PROMPT = """You are answering questions about Temporal, the durable execution platform.

Use ONLY the context below. If the context does not contain the answer, reply
exactly: I don't know.

Context:
{context}

Question: {question}"""


def retrieve(state: QAState) -> QAState:
    return {"documents": get_retriever().invoke(state["question"])}


def generate(state: QAState) -> QAState:
    reply = get_llm().invoke(
        PROMPT.format(
            context=format_docs(state["documents"]), question=state["question"]
        )
    )
    return {"generation": reply.content}


_builder = StateGraph(QAState)
_builder.add_node("retrieve", retrieve)
_builder.add_node("generate", generate)
_builder.add_edge(START, "retrieve")
_builder.add_edge("retrieve", "generate")
_builder.add_edge("generate", END)

graph = _builder.compile()
