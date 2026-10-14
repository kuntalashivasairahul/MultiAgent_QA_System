# V2.1: bounded section context

Starting point: `2cd663b` and the existing 14,414-chunk index. This version changes retrieval context only. V2's semantic prompts, models, canonical refusal, citation validation, and gate routing are retained.

Implementation scope:

- Keep five dense anchors in their original order, then append nearest chunks from each anchor's section in anchor-rank order. Deduplicate stable chunk IDs; never replace anchors with expansion chunks.
- Cap the result at ten chunks and 8,000 document-text characters. Skip additions that do not fit. Fail clearly if anchors themselves exceed the budget; do not truncate code or silently drop evidence.
- Build section membership from the existing canonical chunker, preserving contiguous source/heading runs and source order. Cache by verified collection identity. A changed/missing index must continue to fail explicitly.
- Reuse v2's graph builder with an injected retrieval node. Expose `graph_v2_1` through the existing evaluator and retain its context limits in run inputs.
- Test budgets, source/heading boundaries, repeated heading runs, ordering, deduplication, cache identity, citation IDs, and negative gate/error behavior. Preserve the user's existing `.serena/project.yml` change.

Verification scope:

1. Freeze the implementation before new confirmation questions or native comparison.
2. Compare dense-five and section-expanded context on all 40 development questions; report source-group coverage, context size, runtime, and all seven diagnostic questions' exact fact coverage. These labels are selective coding-assistant annotations, not exhaustive independent ground truth.
3. Exercise the wired graph locally and, if provider quota permits, on a small fresh paired native confirmation. Preserve outputs, scope errors, missing work and actual reported usage. No claim of broad accuracy improvement follows from a small or incomplete study.
4. Report whether missing evidence was recovered and what still needs another retrieval method. Do not tune on the existing four-question confirmation or ten-question regression set. Do not bundle hybrid search, query rewriting, agents, or memory into this change.

This is a bounded retrieval experiment. It cannot recover a section with no dense anchor, and early anchors may consume the expansion budget. All original anchors remain available, but extra context can distract the model. Current work must not be represented as an independently reviewed or production-ready release.
