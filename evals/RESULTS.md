# Evaluation Results

Identical golden set across every version. Retrieval and generation
scored separately. `Refuses` is measured only on the unanswerable bucket.

| Version | n | Correct | Faithful | Recall@5 | Refuses | Unjudged |
|---|---|---|---|---|---|---|
| graph_v0 | 40 | 0.425 | — | — | 0.625 | 0 |
| graph_v1 | 40 | 0.800 | 0.839 | 0.688 | 0.875 | 0 |

**Reading v0:** it retrieves nothing. High correctness there means the
model already knows this corpus, and the retrieval numbers below it are
not measuring what they appear to.

**Unjudged** counts rows the LLM judge could not score after retries.
Those rows are excluded from the means, so a non-zero value means the
denominator is smaller than n.
