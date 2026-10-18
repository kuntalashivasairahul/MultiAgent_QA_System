"""HTTP contract, safe errors and per-request isolation without provider calls."""
import threading
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from api import create_app
from graph_v2 import REFUSAL


def output(question="answer", *, refused=False):
    return {"generation": REFUSAL if refused else question,
            "citations": [] if refused else [{"id": 1, "source": "fixture.mdx", "chunk_id": "chunk"}],
            "quality": {"passed": not refused, "confidence": 0.0 if refused else 1.0,
                        "reason": "Fixture.", "quotes": [], "retry_query": ""},
            "attempt_count": 2 if refused else 1}


def test_api_success_isolated_state_health_and_openapi():
    seen = []
    def invoke(state):
        seen.append(state.copy())
        return output(state["question"])
    client = TestClient(create_app(SimpleNamespace(invoke=invoke)))
    assert client.get("/health").json()["scope"] == "process_only" and not seen
    assert "/ask" in client.get("/openapi.json").json()["paths"]
    for question in ["first", "second"]:
        response = client.post("/ask", json={"question": question})
        assert response.status_code == 200
        body = response.json()
        assert body["answer"] == question and not body["refused"]
        assert body["citations"][0]["chunk_id"] == "chunk"
        assert body["model_profile"]["max_attempts"] == 2
    assert seen == [{"question": "first"}, {"question": "second"}]


@pytest.mark.parametrize("body", [{}, {"question": ""}, {"question": "   "}, {"question": 42},
                                  {"question": None}, {"question": "x" * 4001},
                                  {"question": "valid", "backend": "evil"}])
def test_invalid_request_is_422_without_inference(body):
    client = TestClient(create_app(SimpleNamespace(invoke=lambda s: pytest.fail("Invalid request reached graph"))))
    assert client.post("/ask", json=body).status_code == 422


def test_refusal_is_successful_response():
    client = TestClient(create_app(SimpleNamespace(invoke=lambda s: output(refused=True))))
    response = client.post("/ask", json={"question": "Unknown private setting?"})
    assert response.status_code == 200 and response.json()["refused"] and response.json()["citations"] == []


@pytest.mark.parametrize("error,status,code", [(FileNotFoundError, 503, "index_unavailable"),
                                               (ValueError, 502, "invalid_pipeline_output"),
                                               (RuntimeError, 503, "backend_unavailable")])
def test_errors_are_safe_and_release_inference_slot(error, status, code):
    calls = []
    def invoke(state):
        if not calls:
            calls.append(True)
            raise error("do-not-leak-secret-or-provider-body")
        return output()
    client = TestClient(create_app(SimpleNamespace(invoke=invoke)))
    response = client.post("/ask", json={"question": "question"})
    assert response.status_code == status and response.json()["detail"]["code"] == code
    assert "do-not-leak" not in response.text
    assert client.post("/ask", json={"question": "question"}).status_code == 200


def test_one_inference_at_a_time_but_health_remains_available():
    entered, release = threading.Event(), threading.Event()
    def invoke(state):
        entered.set()
        assert release.wait(5)
        return output()
    client = TestClient(create_app(SimpleNamespace(invoke=invoke)))
    results = []
    worker = threading.Thread(target=lambda: results.append(client.post("/ask", json={"question": "one"})))
    worker.start()
    try:
        assert entered.wait(5)
        assert client.post("/ask", json={"question": "two"}).status_code == 429
        assert client.get("/health").status_code == 200
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive() and results[0].status_code == 200
