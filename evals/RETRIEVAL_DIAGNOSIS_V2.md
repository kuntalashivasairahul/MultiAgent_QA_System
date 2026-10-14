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

A newly confirmed ingestion defect affects dev-02: the original source contains `python worker.py`, but the syntax splitter emits its fenced code block as a 28-character chunk. `load_chunks()` discards chunks shorter than 50 characters, so this command has no answer-bearing indexed chunk. Increasing retrieval k cannot recover an omitted chunk. This defect was discovered after freezing v2 and remains in the shared v1/v2 index for the controlled comparison; it is not fixed in this release.

The next small experiment should retain meaningful short code chunks and rebuild a separate index, with a regression check for the Worker command. Then measure answer-bearing chunk coverage with a larger candidate pool and bounded context. Most multi-SDK misses need coverage of both SDKs, rather than repeated chunks from one. Test lexical/hybrid retrieval only after those measurements establish remaining identifier misses. Keep these changes separate from the gate ablation.
