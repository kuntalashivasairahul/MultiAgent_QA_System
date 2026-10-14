"""Formatting recovery must restore source text without changing factual content."""
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

import graph_v2 as v2


def checked(monkeypatch, source, quote):
    verdict = v2.EvidenceCheck(passed=True, reason="Supported.", quotes=[v2.Quote(id=1, text=quote)])
    monkeypatch.setattr(v2, "structured", lambda *a, **kw: SimpleNamespace(invoke=lambda messages: verdict))
    return v2.check("Check support.", "What is a Sticky Queue?",
                    [Document(page_content=source, metadata={"source": "fixture.mdx"})])


def test_restores_markdown_bold_as_exact_source_quote(monkeypatch):
    source = "This queue, which has an automatically-generated name, is known as a **Sticky Queue**."
    rendered = "This queue, which has an automatically-generated name, is known as a Sticky Queue."
    result = checked(monkeypatch, source, rendered)
    assert result["quotes"][0]["text"] == source


def test_restores_source_line_breaks(monkeypatch):
    source = "The Worker polls the original queue.\nIt also polls its Sticky Queue."
    result = checked(monkeypatch, source, source.replace("\n", " "))
    assert result["quotes"][0]["text"] == source


def test_recovers_link_label_and_line_break_without_changing_inline_code(monkeypatch):
    source = "Use [`temporal workflow delete`](/cli/workflow#delete).\nThis removes a closed Workflow."
    quote = "Use `temporal workflow delete`. This removes a closed Workflow."
    assert checked(monkeypatch, source, quote)["quotes"][0]["text"] == source


def test_restores_bold_and_newline_together(monkeypatch):
    source = "The Worker polls this queue.\nIt is called a **Sticky Queue**."
    quote = "The Worker polls this queue. It is called a Sticky Queue."
    assert checked(monkeypatch, source, quote)["quotes"][0]["text"] == source


def test_literal_code_quotes_are_preserved(monkeypatch):
    source = "```python\na**2**b\n```"
    assert checked(monkeypatch, source, source)["quotes"][0]["text"] == source


@pytest.mark.parametrize("source,quote", [
    ("MaximumAttempts is **3**.", "MaximumAttempts is 5."),
    ("The Go API is **RecordHeartbeat**.", "The Go API is RecordActivityHeartbeat."),
    ("The queue is **Sticky Queue.", "The queue is Sticky Queue."),
    ("```python\na**2**b\n```", "a2b"),
    ("~~~python\na**2**b\n~~~", "a2b"),
    ("Use `a**2**b`.", "Use a2b."),
    ("    a**2**b", "a2b"),
    ("Compute a**2**b.", "Compute a2b."),
    ("Use [`delete`](/correct).", "Use [`delete`](/wrong)."),
    ("Use `a  b`.\nThen stop.", "Use `a b`. Then stop."),
    ("The **limit** is 3.", "The limit is 5."),
])
def test_recovery_rejects_changed_facts_and_code(monkeypatch, source, quote):
    with pytest.raises(ValueError, match="quote"):
        checked(monkeypatch, source, quote)
