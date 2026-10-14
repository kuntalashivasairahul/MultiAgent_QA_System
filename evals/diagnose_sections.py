"""Compare bounded section context to dense-five retrieval; no model generation or judging."""
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import graph_v2_1 as v21
from artifacts import write_json
from evals.run_eval import GOLDEN, load_golden, run_inputs, source_recall
from ingest import get_vectorstore, load_chunks
from retrieval import SECTION_SEED_K, _section_chunks, expand_sections, format_docs, get_retriever


def main() -> None:
    rows = load_golden(dataset=GOLDEN)
    labels_path = Path(__file__).with_name("retrieval_labels_v2.json")
    labels = {r["question"]: r for r in json.loads(labels_path.read_text())["records"]}
    inputs = {**run_inputs(v21, rows, GOLDEN),
              "diagnostic_labels_sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest()}
    fingerprint = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    directory = Path(__file__).parent / "results/section_retrieval" / fingerprint
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "inputs.json", inputs)
    store = get_vectorstore()
    retriever = get_retriever(SECTION_SEED_K)
    sections = _section_chunks(store._collection.name)
    canonical = {d.id: d for d in load_chunks()}
    assert len(canonical) == inputs["index"]["chunks"]
    results = []
    for row in rows:
        started = time.perf_counter()
        anchors = retriever.invoke(row["question"])
        dense_seconds = time.perf_counter() - started
        started = time.perf_counter()
        expanded = v21.retrieve({"question": row["question"]})["documents"]
        expansion_seconds = time.perf_counter() - started
        assert len(expanded) <= v21.CONTEXT_LIMITS["max_chunks"]
        assert sum(len(d.page_content) for d in expanded) <= v21.CONTEXT_LIMITS["max_document_text_characters"]
        controls = {"dense_twelve": get_retriever(12).invoke(row["question"]),
                    "legacy_section_ten": expand_sections(anchors, sections)}
        assert len({d.id for d in expanded}) == len(expanded)
        for doc in expanded:
            assert doc.page_content == canonical[doc.id].page_content
            assert doc.metadata == canonical[doc.id].metadata
        record = {"id": row.get("id"), "question": row["question"], "bucket": row["bucket"],
                  "dense_chunk_ids": [d.id for d in anchors],
                  "documents": [{"id": d.id, "text": d.page_content, "metadata": d.metadata} for d in expanded],
                  "dense_seconds": dense_seconds, "expansion_seconds": expansion_seconds,
                  "dense_characters": sum(len(d.page_content) for d in anchors),
                  "expanded_characters": sum(len(d.page_content) for d in expanded),
                  "serialized_context_characters": len(format_docs(expanded)),
                  "controls": {name: {"ids": [d.id for d in docs],
                                      "characters": sum(len(d.page_content) for d in docs)}
                               for name, docs in controls.items()}}
        if row["bucket"] != "unanswerable":
            record["dense_source_recall"] = source_recall(row, [{"metadata": d.metadata} for d in anchors])
            record["expanded_source_recall"] = source_recall(row, record["documents"])
            for name, docs in controls.items():
                record["controls"][name]["source_recall"] = source_recall(row, [{"metadata": d.metadata} for d in docs])
        if row["question"] in labels:
            record["labeled_facts"] = []
            for fact in labels[row["question"]]["facts"]:
                matches = lambda docs: [d.id for d in docs if d.metadata["source"] == fact["source"] and fact["quote"] in d.page_content]
                dense_hits, expanded_hits = matches(anchors), matches(expanded)
                for name, docs in controls.items():
                    record["controls"][name].setdefault("fact_hits", []).append(bool(matches(docs)))
                record["labeled_facts"].append({"source": fact["source"], "quote": fact["quote"],
                                               "indexed_ids": matches(canonical.values()),
                                               "dense_hits": dense_hits, "expanded_hits": expanded_hits})
        results.append(record)
    final_inputs = {**run_inputs(v21, rows, GOLDEN),
                    "diagnostic_labels_sha256": hashlib.sha256(labels_path.read_bytes()).hexdigest()}
    assert final_inputs == inputs, "Inputs changed during diagnosis"
    answerable = [r for r in results if "dense_source_recall" in r]
    facts = [f for r in results for f in r.get("labeled_facts", [])]
    diagnostic_rows = [r for r in results if "labeled_facts" in r]
    assert len(results) == 40 and len(diagnostic_rows) == 7
    summary = {"questions": len(results), "answerable_questions": len(answerable),
               "diagnostic_questions": len(diagnostic_rows), "labeled_facts": len(facts),
               "indexed_labeled_facts": sum(bool(f["indexed_ids"]) for f in facts),
               "dense_fact_hits": sum(bool(f["dense_hits"]) for f in facts),
               "expanded_fact_hits": sum(bool(f["expanded_hits"]) for f in facts),
               "dense_complete_diagnostic_contexts": sum(all(f["dense_hits"] for f in r["labeled_facts"]) for r in diagnostic_rows),
               "expanded_complete_diagnostic_contexts": sum(all(f["expanded_hits"] for f in r["labeled_facts"]) for r in diagnostic_rows),
               "dense_mean_source_recall": sum(r["dense_source_recall"] for r in answerable) / len(answerable),
               "expanded_mean_source_recall": sum(r["expanded_source_recall"] for r in answerable) / len(answerable),
               "dense_all_sources": sum(r["dense_source_recall"] == 1 for r in answerable),
               "expanded_all_sources": sum(r["expanded_source_recall"] == 1 for r in answerable),
               "dense_mean_characters": sum(r["dense_characters"] for r in results) / len(results),
               "expanded_mean_characters": sum(r["expanded_characters"] for r in results) / len(results),
               "expanded_max_characters": max(r["expanded_characters"] for r in results),
               "expanded_mean_chunks": sum(len(r["documents"]) for r in results) / len(results),
               "dense_mean_warm_seconds": sum(r["dense_seconds"] for r in results) / len(results),
               "mean_expansion_seconds": sum(r["expansion_seconds"] for r in results) / len(results)}
    summary["mean_serialized_context_characters"] = sum(r["serialized_context_characters"] for r in results) / len(results)
    summary["controls"] = {name: {
        "facts": sum(sum(r["controls"][name].get("fact_hits", [])) for r in results),
        "complete_diagnostic_contexts": sum(all(r["controls"][name]["fact_hits"]) for r in diagnostic_rows),
        "all_sources": sum(r["controls"][name]["source_recall"] == 1 for r in answerable),
        "mean_characters": sum(r["controls"][name]["characters"] for r in results) / len(results)}
        for name in controls}
    write_json(directory / "result.json", {"scope": "Current v21 hybrid retrieval (expanded fields) compared with dense-five, dense-twelve and legacy-section-ten controls, development only; no generation or native judges. Selected coding-assistant fact labels are not independent ground truth. Timings exclude store initialization; first hybrid query includes lexical cache construction. Text budget excludes serialized metadata overhead, reported separately.",
                                          "fingerprint": fingerprint, "summary": summary, "rows": results})
    print(json.dumps({"artifact_dir": str(directory), **summary}, indent=2))


if __name__ == "__main__":
    main()
