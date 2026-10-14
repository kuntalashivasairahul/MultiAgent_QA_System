# Diagnosis of the seven v1 development refusals

This uses the frozen `9dcd9ef` baseline. [Diagnostic labels](retrieval_labels_v2.json) retain question IDs, exact source phrases, answer-bearing chunk IDs where present, and matches in the actual retrieved context. The assistant authored these labels; they are selected facts, not exhaustive annotations of every equivalent source.

| Question | Document source recall | Labeled facts indexed | Labeled facts retrieved | Required facts |
|---|---:|---:|---:|---:|
| dev-02: Python Worker command | 1.0 | 0 | 0 | 1 |
| dev-04: Java Continue-As-New API | 1.0 | 1 | 0 | 1 |
| dev-10: dashboard polling interval | 0.0 | 1 | 0 | 1 |
| dev-20: Java/Python Continue-As-New APIs | 0.5 | 2 | 0 | 2 |
| dev-21: Go/TypeScript storage permissions | 0.5 | 2 | 1 | 2 |
| dev-22: Java/Python suggested-new-run APIs | 1.0 | 2 | 1 | 2 |
| dev-24: Go/Python ABANDON options | 0.5 | 2 | 1 | 2 |

Every selected refusal lacks at least one labeled fact in its actual context. Three have full document-level source recall while still missing necessary evidence. V2 gates cannot recover these facts.

A confirmed ingestion defect affected dev-02 in this frozen index: the original source contains `python worker.py`, but the syntax splitter emits its fenced code block as a 28-character chunk. The baseline discarded chunks shorter than 50 characters, so this command had no answer-bearing indexed chunk. Increasing retrieval k could not recover an omitted chunk. This defect was discovered after freezing v2 and deliberately preserved in the shared v1/v2 comparison index.

The subsequent fix at `8dc2fae` retains meaningful short code chunks and publishes a 14,414-chunk index, with all old chunks unchanged and the Worker command present. Its original question still misses the command at top five. The same section is already retrieved, motivating bounded section expansion before broader search. See [post-index verification](post_index_verification_v2.json) and [v2 results and next course](V2_STATUS.md). Most multi-SDK misses need coverage of both SDKs, rather than repeated chunks from one. Test lexical/hybrid retrieval only after coverage measurements establish remaining identifier misses. These ingestion/retrieval changes are separate from the frozen gate ablation.
