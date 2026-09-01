"""One runnable check for the whole project.

Run: uv run pytest test_graph.py -v
 or: uv run python test_graph.py
"""
from ingest import clean_mdx


def test_clean_mdx_strips_frontmatter_and_imports():
    raw = '---\ntitle: X\n---\nimport A from "b";\n\n# Head\nReal text.'
    out = clean_mdx(raw)
    assert "title: X" not in out
    assert "import A" not in out
    assert "Real text." in out


def test_clean_mdx_strips_jsx_tags_but_keeps_inner_text():
    raw = '<Tabs groupId="x">\n<TabItem value="go">\nGo instructions.\n</TabItem>\n</Tabs>'
    out = clean_mdx(raw)
    assert "<Tabs" not in out and "<TabItem" not in out
    assert "Go instructions." in out


def test_clean_mdx_preserves_generics_inside_code_fences():
    """<String is Java generics, not JSX. Stripping it would corrupt samples."""
    raw = 'Text.\n\n```java\nList<String> x = new ArrayList<>();\n```\n'
    out = clean_mdx(raw)
    assert "List<String>" in out


def test_retriever_finds_jargon_term():
    """Exact-identifier jargon is where dense-only retrieval typically fails."""
    from retrieval import get_retriever
    docs = get_retriever().invoke("continue-as-new")
    assert docs, "retriever returned nothing - is chroma_db/ built?"
    assert any("continue-as-new" in d.metadata["source"] for d in docs)


def test_every_graph_exposes_the_shared_interface():
    """compare.py depends on this contract. If it breaks, the table breaks."""
    import importlib, pathlib
    modules = [p.stem for p in pathlib.Path(".").glob("graph_v*.py")]
    assert modules, "no graph modules found"
    for name in modules:
        graph = importlib.import_module(name).graph
        assert hasattr(graph, "invoke"), f"{name}.graph is not invokable"

if __name__ == "__main__":
    import sys
    mod = sys.modules[__name__]
    tests = [v for k, v in vars(mod).items() if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
