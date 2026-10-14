"""A short fenced command is evidence even when prose noise is filtered."""
import ingest


def test_short_fenced_worker_command_is_indexed(tmp_path, monkeypatch):
    source = tmp_path / "worker.mdx"
    source.write_text(
        "---\ntitle: Worker guide\n---\n# Run the Worker\n"
        "Create a Python Worker that polls the Task Queue and registers the Activities.\n\n"
        "```bash\npython worker.py\n```\n\nnoise\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ingest, "CORPUS", tmp_path)
    chunks = ingest.load_chunks()
    command = [d for d in chunks if "python worker.py" in d.page_content]
    assert len(command) == 1
    assert command[0].metadata["source"] == "worker.mdx"
    assert command[0].metadata["headings"] == "Run the Worker"
    assert "```bash\npython worker.py\n```" in command[0].page_content
    assert not any(d.page_content.strip() == "noise" for d in chunks)
