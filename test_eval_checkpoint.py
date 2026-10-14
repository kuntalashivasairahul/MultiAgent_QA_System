"""Durable paid-node resumption, attempt ownership, and cumulative observations."""
from contextlib import contextmanager
import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest
from groq import RateLimitError
from langchain_core.documents import Document
from langgraph.graph import START, END, StateGraph

from evals import run_eval as ev
from graph_v2 import V2State
from test_evals import evaluation


def checkpoint_graph(module, *, fail_support=True):
    calls = {name: 0 for name in ("retrieve", "sufficient", "generate", "support")}
    document = Document(id="a", page_content="Evidence A", metadata={"source": "a.mdx", "chunk_id": "a"})
    def retrieve(state):
        calls["retrieve"] += 1
        return {"documents": [document]}
    def sufficient(state):
        calls["sufficient"] += 1
        return {"sufficiency": {"passed": True, "reason": "Evidence exists.", "quotes": []}}
    def generate(state):
        calls["generate"] += 1
        return {"generation": "Supported answer", "citations": [{"id": 1, "source": "a.mdx", "chunk_id": "a"}]}
    def support(state):
        calls["support"] += 1
        if fail_support and calls["support"] == 1:
            raise RuntimeError("Provider outage after paid generation")
        return {"support": {"passed": True, "reason": "Supported.", "quotes": []}}
    def build_graph(*, checkpointer):
        graph = StateGraph(V2State)
        for name, fn in (("retrieve", retrieve), ("sufficient", sufficient), ("generate", generate), ("support", support)):
            graph.add_node(name, fn)
        for a, b in ((START, "retrieve"), ("retrieve", "sufficient"), ("sufficient", "generate"), ("generate", "support"), ("support", END)):
            graph.add_edge(a, b)
        return graph.compile(checkpointer=checkpointer)
    module.SUPPORTS_CHECKPOINTS = True
    module.build_graph = build_graph
    return calls


def test_resume_reopens_disk_checkpoint_without_repeating_paid_nodes(evaluation, monkeypatch):
    module, dataset, _, _ = evaluation
    calls = checkpoint_graph(module)
    reports = iter([{"test-model": {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}},
                    {"test-model": {"input_tokens": 30, "output_tokens": 4, "total_tokens": 34}}])
    @contextmanager
    def usage():
        yield SimpleNamespace(usage_metadata=next(reports))
    monkeypatch.setattr(ev, "get_usage_metadata_callback", usage)
    first = ev.run_eval(module.__name__, dataset=dataset)
    assert first["status"] == "incomplete" and first["generation_errors"] == 1
    second = ev.run_eval(module.__name__, dataset=dataset)
    assert second["status"] == "complete" and first["run_id"] == second["run_id"]
    assert calls == {"retrieve": 1, "sufficient": 1, "generate": 1, "support": 2}
    record = next(iter(ev._load_partial(Path(second["artifact_dir"]) / "partial.jsonl").values()))
    assert record["generation_usage"]["test-model"] == {"input_tokens": 130, "output_tokens": 24, "total_tokens": 154}
    assert record["checks"]["sufficiency"]["passed"] and record["checks"]["support"]["passed"]
    assert record["documents"][0]["id"] == "a"


def test_completed_graph_recovers_if_answer_append_fails(evaluation, monkeypatch):
    module, dataset, _, _ = evaluation
    calls = checkpoint_graph(module, fail_support=False)
    append = ev._append
    def fail_answer_write(path, record):
        if "answer" in record:
            raise OSError("Simulated failed append after graph completion")
        append(path, record)
    monkeypatch.setattr(ev, "_append", fail_answer_write)
    with pytest.raises(OSError):
        ev.run_eval(module.__name__, dataset=dataset)
    monkeypatch.setattr(ev, "_append", append)
    result = ev.run_eval(module.__name__, dataset=dataset)
    assert result["status"] == "complete"
    assert calls == {name: 1 for name in calls}


def test_attempt_lock_rejects_competing_writer_and_releases_on_close(tmp_path):
    path = tmp_path / "owner.sqlite"
    owner = sqlite3.connect(path, timeout=0)
    owner.execute("BEGIN IMMEDIATE")
    try:
        with pytest.raises(RuntimeError, match="already running"):
            with ev._evaluation_lock(path):
                pass
    finally:
        owner.close()
    with ev._evaluation_lock(path):
        pass


def test_rate_limit_retry_metadata_survives_without_raw_error_body(evaluation):
    module, dataset, _, _ = evaluation
    response = httpx.Response(429, headers={"retry-after": "2"}, request=httpx.Request("POST", "https://api.groq.com"))
    module.graph.invoke = Mock(side_effect=RateLimitError("TEST_PRIVATE_MESSAGE", response=response, body={}))
    result = ev.run_eval(module.__name__, dataset=dataset)
    row = next(iter(ev._load_partial(Path(result["artifact_dir"]) / "partial.jsonl").values()))
    assert row["generation_error_details"] == {"status_code": 429, "retry_after": "2"}
    assert "TEST_PRIVATE_MESSAGE" not in json.dumps(row)
