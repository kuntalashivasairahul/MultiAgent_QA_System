"""Provider protocol and endpoint boundaries; no paid calls."""
import json
import os
import subprocess
import sys

import pytest
from langchain_core.messages import HumanMessage, SystemMessage
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
    reply = v3_llm.structured(graph_v1.GroundedAnswer).invoke([
        SystemMessage("Use only cited public evidence; never invent private values."), HumanMessage("Question")])
    assert reply.citations == [1] and observed["method"] == "json_mode"
    assert '"citations"' in observed["messages"][0].content and "ONLY JSON" in observed["messages"][0].content
    assert observed["kwargs"]["max_tokens"] == v3_llm.MAX_TOKENS
    assert "never invent private values" in "\n".join(message.content for message in observed["messages"]
                                                     if isinstance(message, SystemMessage))


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
@pytest.mark.parametrize("local_role", ["generation", "judge"])
def test_local_profile_cannot_send_documents_to_remote_or_credential_url(url, local_role):
    env = {**os.environ, "QA_BACKEND": "lmstudio" if local_role == "generation" else "groq",
           "QA_JUDGE_BACKEND": "lmstudio" if local_role == "judge" else "groq",
           "LMSTUDIO_BASE_URL": url, "LANGSMITH_TRACING": "false"}
    result = subprocess.run([sys.executable, "-c", "import v3_llm"], env=env, capture_output=True, text=True)
    assert result.returncode != 0 and "loopback /v1 endpoint" in result.stderr


@pytest.mark.parametrize("generation_backend", ["groq", "lmstudio"])
@pytest.mark.parametrize("judge_backend", ["groq", "lmstudio"])
def test_local_reasoner_and_independent_judge_routing_are_reported(monkeypatch, generation_backend, judge_backend):
    import graph_v3
    observed = []
    class Model:
        def __init__(self, backend):
            self.backend = backend
        def with_structured_output(self, schema, *, method, **kwargs):
            observed.append((self.backend, method))
            if schema is graph_v1.GroundedAnswer:
                value = schema(answer="Supported.", citations=[1])
            else:
                value = schema(passed=False, reason="Missing fact.", quotes=[], confidence=0.0, retry_query="fact")
            return RunnableLambda(lambda messages, **kwargs: value)
    monkeypatch.setattr(v3_llm, "BACKEND", "lmstudio")
    monkeypatch.setattr(v3_llm, "BACKEND", generation_backend)
    monkeypatch.setattr(v3_llm, "JUDGE_BACKEND", judge_backend)
    monkeypatch.setattr(v3_llm, "client", lambda model: Model("lmstudio"))
    monkeypatch.setattr(v3_llm.llm, "get_llm", lambda **kwargs: Model("groq"))
    v3_llm.structured(graph_v1.GroundedAnswer).invoke([])
    v3_llm.structured(graph_v3.QualityVerdict, judge=True).invoke([])
    assert observed == [(generation_backend, "json_mode" if generation_backend == "groq" else "json_schema"),
                        (judge_backend, "json_mode" if judge_backend == "groq" else "json_schema")]
    assert v3_llm.profile()["judge_backend"] == judge_backend


@pytest.mark.parametrize("settings", [
    {"QA_JUDGE_BACKEND": "invalid"},
    {"QA_JUDGE_BACKEND": "lmstudio", "QA_JUDGE_MODEL": ""},
    {"QA_BACKEND": "invalid", "QA_JUDGE_BACKEND": "lmstudio"},
])
def test_judge_backend_configuration_rejects_invalid_provider_or_empty_model(settings):
    env = {**os.environ, "QA_BACKEND": "lmstudio", "QA_MODEL": "local-model",
           "QA_JUDGE_MODEL": "local-model", "LANGSMITH_TRACING": "false", **settings}
    result = subprocess.run([sys.executable, "-c", "import v3_llm"], env=env, capture_output=True, text=True)
    assert result.returncode != 0 and "ValueError" in result.stderr


@pytest.mark.parametrize("identity", [None, "invalid", "A" * 64])
def test_different_local_judge_weights_are_required_and_fingerprinted(monkeypatch, tmp_path, identity):
    import graph_v3
    import evals.run_eval as evaluation
    monkeypatch.setattr(evaluation, "read_manifest", lambda: {"fingerprint": "fixture"})
    monkeypatch.setattr(v3_llm, "BACKEND", "lmstudio")
    monkeypatch.setattr(v3_llm, "JUDGE_BACKEND", "lmstudio")
    monkeypatch.setattr(v3_llm, "JUDGE_MODEL", "different-local-judge")
    monkeypatch.setattr(v3_llm, "MODEL_SHA256", "a" * 64)
    monkeypatch.setattr(v3_llm, "JUDGE_MODEL_SHA256", identity)
    dataset = tmp_path / "fixture.jsonl"
    dataset.write_text("{}\n")
    with pytest.raises(ValueError, match="LMSTUDIO_JUDGE_MODEL_SHA256"):
        evaluation.run_inputs(graph_v3, [], dataset)
    monkeypatch.setattr(v3_llm, "JUDGE_MODEL_SHA256", "b" * 64)
    before = evaluation.run_inputs(graph_v3, [], dataset)
    monkeypatch.setattr(v3_llm, "JUDGE_MODEL_SHA256", "c" * 64)
    after = evaluation.run_inputs(graph_v3, [], dataset)
    assert before["graph_runtime"]["model_weights_sha256"] == after["graph_runtime"]["model_weights_sha256"]
    assert before["graph_runtime"]["judge_weights_sha256"] != after["graph_runtime"]["judge_weights_sha256"]


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
    assert before["evaluation_judge"]["model"] == evaluation.JUDGE_MODEL
    monkeypatch.setattr(v3_llm.llm, "REQUESTS_PER_SECOND", 0.125)
    changed = evaluation.run_inputs(graph_v3, [], dataset)
    assert changed["evaluation_judge"]["requests_per_second"] == 0.125
    assert changed["evaluation_judge"] != before["evaluation_judge"]


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
