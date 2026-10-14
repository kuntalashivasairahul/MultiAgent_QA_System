# Verified evaluation results

Frozen repaired baseline at `9dcd9ef`. These ten questions have since been inspected and are now regression examples, not a fresh blind holdout. The original table and raw artifacts below are preserved.

Dataset: holdout.jsonl. Only current-input full evaluations appear here; missing metrics are visible below.

| Version | n | Correct | Answerable correct | Faithful | Source recall@k | All sources@k | Exact refusal | Status |
|---|---|---|---|---|---|---|---|---|
| graph_v0 | 10 | 1.000 | 1.000 | — | — | — | 1.000 | complete |
| graph_v1 | 10 | 0.600 | 0.625 | 1.000 | 0.812 | 0.750 | 0.500 | complete |

## graph_v0

Run: [20261014T034425656951Z-b368fd30](results/verified/graph_v0/38a9e478e0a5bffcc64c3697b3b8d9931d5f86ac094ad7b4b7ffc7166b5b83b8/20261014T034425656951Z-b368fd30/result.json). Fingerprint: 38a9e478e0a5bffcc64c3697b3b8d9931d5f86ac094ad7b4b7ffc7166b5b83b8. Retrieval k: None.

| Metric | Eligible | Scored | Missing |
|---|---:|---:|---:|
| correctness | 10 | 10 | 0 |
| answerable_correctness | 8 | 8 | 0 |
| faithfulness | 0 | 0 | 0 |
| recall_at_k | 0 | 0 | 0 |
| all_sources_rate | 0 | 0 | 0 |
| any_source_rate | 0 | 0 | 0 |
| refusal_rate | 2 | 2 | 0 |

## graph_v1

Run: [20261014T034508791321Z-201b04a2](results/verified/graph_v1/c5a804ea77a0046438529e467b2b339d9cdb00902481995a02cd57e2e1bd33e8/20261014T034508791321Z-201b04a2/result.json). Fingerprint: c5a804ea77a0046438529e467b2b339d9cdb00902481995a02cd57e2e1bd33e8. Retrieval k: 5.

| Metric | Eligible | Scored | Missing |
|---|---:|---:|---:|
| correctness | 10 | 10 | 0 |
| answerable_correctness | 8 | 8 | 0 |
| faithfulness | 8 | 8 | 0 |
| recall_at_k | 8 | 8 | 0 |
| all_sources_rate | 8 | 8 | 0 |
| any_source_rate | 8 | 8 | 0 |
| refusal_rate | 2 | 2 | 0 |

Source recall counts evidence groups, accepting reviewed alternative paths. All-sources success requires every group. Exact refusal is a contract check, not a direct hallucination measure. Model-only performance cannot establish training-data provenance. Development and holdout scores must be interpreted separately; small samples have substantial uncertainty.

## Quality limit

This ten-question confirmation set is small and shares familiar topics with development. It shows no retrieval advantage here. One private-configuration question received an unsupported claim that MaximumAttempts is 3; the prototype has no access to that private repository. Preserve this failure as evidence for the next grounding/refusal experiment. The 100% answerable faithfulness value does not cover the unanswerable bucket and must not be presented as universal hallucination prevention.
