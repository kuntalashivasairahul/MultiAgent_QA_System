import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
from langchain_core.documents import Document

from evals import calibrate, draft_golden


def test_drafting_rejects_skip_duplicates_and_preserves_incomplete_output(tmp_path, monkeypatch):
    a = Document(page_content="A" * 500, metadata={"source": "a.mdx"})
    b = Document(page_content="B" * 500, metadata={"source": "b.mdx"})
    monkeypatch.setattr(draft_golden, "load_chunks", lambda: [a, b])
    monkeypatch.setattr(draft_golden, "get_vectorstore", Mock())
    monkeypatch.setattr(draft_golden, "structured", Mock())
    monkeypatch.setattr(draft_golden, "_related_pair", lambda *args: (a, b))
    monkeypatch.setattr(draft_golden, "TARGET", {"direct": 1, "multihop": 1})
    output = tmp_path / "golden.draft.jsonl"
    monkeypatch.setattr(draft_golden, "OUT", output)
    qa = draft_golden.QA
    monkeypatch.setattr(draft_golden, "_draft", Mock(side_effect=[
        qa(question="SKIP", answer="None"), qa(question="Specific direct?", answer="A"),
        qa(question="specific direct?", answer="A"), qa(question="Specific multihop?", answer="A and B"),
    ]))
    draft_golden.main()
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(rows) == 2 + len(draft_golden.UNANSWERABLE)
    assert len({r["question"].casefold() for r in rows}) == len(rows)
    previous = output.read_bytes()
    monkeypatch.setattr(draft_golden, "_draft", lambda *args: qa(question="SKIP", answer="None"))
    with pytest.raises(SystemExit, match="Incomplete"):
        draft_golden.main()
    assert output.read_bytes() == previous
    assert (tmp_path / "golden.incomplete.jsonl").exists()


def test_calibration_does_not_pass_an_always_false_judge(tmp_path, monkeypatch):
    def structured(schema, **kwargs):
        chain = Mock()
        key = "correct" if schema is calibrate.Correctness else "grounded"
        chain.invoke.return_value = schema(**{key: False}, reason="Always false")
        return chain
    monkeypatch.setattr(calibrate, "structured", structured)
    monkeypatch.setattr(calibrate, "ROOT", tmp_path)
    result = calibrate.main()
    assert not result["passed"] and len(result["cases"]) == 8
    assert json.loads((tmp_path / "calibration.json").read_text())["passed"] is False


def test_corpus_fetch_pins_updates_and_preserves_local_edits(tmp_path):
    git = shutil.which("git")
    project, remote, wrappers = (tmp_path / name for name in ("project", "remote", "bin"))
    for path in (project, remote, wrappers):
        path.mkdir()
    def run_git(*args):
        return subprocess.check_output([git, "-C", str(remote), *args], text=True).strip()
    run_git("init", "-q")
    (remote / "docs").mkdir()
    source = remote / "docs/sample.md"
    source.write_text("First snapshot")
    run_git("add", ".")
    run_git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "First")
    first = run_git("rev-parse", "HEAD")
    shutil.copy(Path(__file__).parent / "fetch_corpus.sh", project / "fetch_corpus.sh")
    pin = project / "CORPUS_REVISION"
    pin.write_text(first + "\n")
    wrapper = wrappers / "git"
    wrapper.write_text(f"#!{sys.executable}\nimport os,sys\nargs=[{str(remote)!r} if a=='https://github.com/temporalio/documentation.git' else a for a in sys.argv[1:]]\nos.execv({git!r},[{git!r},*args])\n")
    wrapper.chmod(0o755)
    env = {**os.environ, "PATH": str(wrappers) + os.pathsep + os.environ["PATH"]}
    def fetch():
        return subprocess.run(["bash", str(project / "fetch_corpus.sh")], env=env, capture_output=True, text=True)
    assert fetch().returncode == 0
    assert (project / "corpus/docs/sample.md").read_text() == "First snapshot"
    source.write_text("Second snapshot")
    run_git("add", ".")
    run_git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "Second")
    pin.write_text(run_git("rev-parse", "HEAD") + "\n")
    assert fetch().returncode == 0
    assert (project / "corpus/docs/sample.md").read_text() == "Second snapshot"
    assert any((p / "corpus/docs/sample.md").read_text() == "First snapshot" for p in project.glob(".corpus-backup-*"))
    local = project / "corpus/docs/sample.md"
    local.write_text("Local edits")
    assert fetch().returncode != 0
    assert local.read_text() == "Local edits"


def test_atomic_json_keeps_previous_artifact_on_failed_publication(tmp_path, monkeypatch):
    import artifacts
    target = tmp_path / "result.json"
    artifacts.write_json(target, {"version": "old"})
    monkeypatch.setattr(artifacts.os, "replace", Mock(side_effect=OSError("failed publication")))
    with pytest.raises(OSError, match="failed publication"):
        artifacts.write_json(target, {"version": "new"})
    assert json.loads(target.read_text()) == {"version": "old"}
    assert list(tmp_path.iterdir()) == [target]


def test_structured_output_retries_schema_instead_of_instance(monkeypatch):
    import llm
    from langchain_core.exceptions import OutputParserException
    from langchain_core.runnables import RunnableLambda
    calls = []
    def invoke(messages):
        calls.append(messages)
        if len(calls) == 1:
            raise OutputParserException("Provider returned the schema instead of an answer instance")
        return {"answer": "Known fact", "citations": [1]}
    model = Mock()
    model.with_structured_output.return_value = RunnableLambda(invoke)
    monkeypatch.setattr(llm, "get_llm", lambda *args, **kwargs: model)
    result = llm.structured(Mock()).invoke("question")
    assert result == {"answer": "Known fact", "citations": [1]}
    assert len(calls) == 2
