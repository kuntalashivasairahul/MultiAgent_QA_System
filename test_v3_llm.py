"""Provider protocol and endpoint boundaries; no paid calls."""
import os
import subprocess
import sys

import pytest
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda

import graph_v1
import v3_llm


def test_groq_llama_uses_json_object_mode_with_explicit_schema(monkeypatch):
    observed = {}
    class Model:
        def with_structured_output(self, schema, *, method):
            observed["method"] = method
            def invoke(messages, **kwargs):
                observed["messages"] = messages
                observed["kwargs"] = kwargs
                return schema(answer="Supported.", citations=[1])
            return RunnableLambda(invoke)
    monkeypatch.setattr(v3_llm, "BACKEND", "groq")
    monkeypatch.setattr(v3_llm.llm, "get_llm", lambda **kwargs: Model())
    reply = v3_llm.structured(graph_v1.GroundedAnswer).invoke([HumanMessage("Question")])
    assert reply.citations == [1] and observed["method"] == "json_mode"
    assert '"citations"' in observed["messages"][0].content and "ONLY JSON" in observed["messages"][0].content
    assert observed["kwargs"]["max_tokens"] == v3_llm.MAX_TOKENS


def test_local_uses_schema_constrained_output(monkeypatch):
    observed = {}
    class Model:
        def with_structured_output(self, schema, **kwargs):
            observed.update(kwargs)
            return RunnableLambda(lambda messages: schema(answer="Supported.", citations=[1]))
    monkeypatch.setattr(v3_llm, "BACKEND", "lmstudio")
    monkeypatch.setattr(v3_llm, "client", lambda model: Model())
    assert v3_llm.structured(graph_v1.GroundedAnswer).invoke([]).answer == "Supported."
    assert observed == {"method": "json_schema", "strict": True}


@pytest.mark.parametrize("url", ["https://example.com/v1", "http://localhost:1234/other",
                                "http://secret@localhost:1234/v1", "http://localhost:1234/v1?token=secret"])
def test_local_profile_cannot_send_documents_to_remote_or_credential_url(url):
    env = {**os.environ, "QA_BACKEND": "lmstudio", "LMSTUDIO_BASE_URL": url, "LANGSMITH_TRACING": "false"}
    result = subprocess.run([sys.executable, "-c", "import v3_llm"], env=env, capture_output=True, text=True)
    assert result.returncode != 0 and "loopback /v1 endpoint" in result.stderr


def test_v3_profile_and_helper_are_in_evaluation_fingerprint(monkeypatch, tmp_path):
    import graph_v3
    import evals.run_eval as evaluation
    monkeypatch.setattr(evaluation, "read_manifest", lambda: {"fingerprint": "fixture"})
    monkeypatch.setattr(v3_llm, "MODEL_SHA256", "a" * 64)
    dataset = tmp_path / "fixture.jsonl"
    dataset.write_text('{}\n')
    before = evaluation.run_inputs(graph_v3, [], dataset)
    monkeypatch.setattr(v3_llm, "MODEL", "different-llama-model")
    after = evaluation.run_inputs(graph_v3, [], dataset)
    assert before["graph_runtime"]["generation_model"] != after["graph_runtime"]["generation_model"]
    assert "v3_llm.py" in before["code"]
    assert before["generation_model"] == before["graph_runtime"]["generation_model"]
    assert before["max_tokens"] == v3_llm.MAX_TOKENS


@pytest.mark.parametrize("digest", [None, "bad", "a" * 63])
def test_local_evaluation_rejects_missing_or_invalid_weights_identity(monkeypatch, tmp_path, digest):
    import graph_v3
    import evals.run_eval as evaluation
    monkeypatch.setattr(v3_llm, "BACKEND", "lmstudio")
    monkeypatch.setattr(v3_llm, "MODEL_SHA256", digest)
    dataset = tmp_path / "fixture.jsonl"
    dataset.write_text('{}\n')
    with pytest.raises(ValueError, match="LMSTUDIO_MODEL_SHA256"):
        evaluation.run_inputs(graph_v3, [], dataset)
