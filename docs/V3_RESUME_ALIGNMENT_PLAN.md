# V3 plan: implement the missing résumé claims

Status: **core v3 workflow and API implemented in the development branch**. Stable v2.1 remains at the accepted 8.63/10 engineering assessment. The owner subsequently requested actual implementation and an LM Studio machine assessment. See [delivered behavior, native evidence and remaining work](V3_LOCAL_UPGRADE.md). This design is retained below; full matched accuracy evaluation is still pending, and the checked Groq account currently has no generative Llama model.

Goal: make the supplied claims about a Retrieval/Reasoning/Judge pipeline, quality-threshold retrieval retries and FastAPI endpoints demonstrably true. Reuse current retrieval, citations, evidence validation and evaluation infrastructure. No new multi-agent framework, parallel-agent infrastructure, database service, UI or private-data ingestion is needed for these claims.

## 1. Define the three roles and the quality contract

Implement a separately versioned `graph_v3.py`, preserving v2.1 as a comparison baseline. Retrieval returns canonical evidence; Reasoning generates a cited answer; Judge assesses that answer against its cited evidence. Here “agent” means a role-specific workflow participant, not a claim of independent autonomous workers or parallel execution. Document the state exchanged between roles.

Reuse existing strict question, citation-ID, literal-quote and semantic-support checks. Add the minimum v3 state: retrieval query, attempt count, structured quality verdict and per-attempt audit history. A quality verdict needs a bounded score, reason, checked evidence and the missing aspect motivating a retry. Call it a rubric quality score, not a calibrated probability of correctness.

Choose the rubric and threshold using development controls before fresh confirmation. Record the chosen threshold in the evaluation fingerprint. A high score cannot override invalid citations, unsupported claims or an operational error. Preserve exact refusal behavior and retain rejected drafts/verdicts.

Acceptance: schema tests reject invalid scores/fields/IDs, unsupported passing verdicts and malformed quotes; controlled high/low-score examples exercise the documented quality rubric. Public examples must not establish private configuration.

## 2. Add a bounded retrieval retry

Wire Judge → Retrieval when the answer is below the configured threshold and retry budget remains. Start with at most **one retrieval retry**, hence at most two retrieval/generation attempts. Terminal failure returns the canonical refusal and retained audit. Provider outages remain errors.

The retry must change evidence acquisition: use the original question plus a bounded missing-aspect query to search again, selecting fresh/diverse canonical evidence under the existing 12-chunk/8,000-text-character cap. Do not simply rerun the identical retrieval and describe it as a retrieval improvement. Treat the Judge's query suggestion as untrusted data; retain the original question and exact scope. If no useful evidence is found, stop safely after the bound.

Keep each answer's citations bound to that attempt's documents. Retain both contexts, queries, verdicts and reported usage so the second attempt cannot hide the first. Use existing synchronous checkpoint support to avoid repeating completed paid nodes after a later outage.

Touchpoints: new v3 graph/state, shared retrieval helpers only where required, [evals/run_eval.py](../evals/run_eval.py) for v3 score/attempt audits and fingerprints, relevant graph/retrieval/checkpoint tests, architecture and usage documentation. Preserve historical artifacts when new fingerprints are selected.

Acceptance: low score leads to an actual second retrieval with changed context on a controlled missing-fact fixture; sufficient second evidence can produce a supported answer; high score skips retry; persistent low quality terminates after one retry; forged evidence fails; recovery retains completed nodes and cumulative usage. Test negative/private questions as well as successful retries.

## 3. Expose the same graph through FastAPI

Add FastAPI and Uvicorn as explicit locked dependencies and a small application module. Use Pydantic request/response models and the same shared graph rather than duplicating inference logic.

- `POST /ask`: validated question in; answer, citations, refusal status, quality verdict and attempt count out. A refusal is a valid result, not a server failure.
- `GET /health`: basic process health with clearly documented meaning. Do not call Groq on health checks or claim corpus/provider readiness without checking it.
- Return safe operational error codes for missing index/provider failures, without credentials, raw provider bodies or private paths. Document request validation, response examples and local startup.

Use isolated per-request state. Do not reuse the evaluation question-hash thread as a public conversation/session identifier. Run blocking inference appropriately for FastAPI's execution model. Continue to support public documentation only; authentication, multi-tenant isolation and production deployment require separate work before such claims can be made.

Touchpoints: application module, `pyproject.toml`/`uv.lock`, API tests using FastAPI TestClient, existing shared input validation, README and architecture. Avoid unnecessary endpoints or deployment infrastructure.

Acceptance: tests cover successful responses and citation structure, canonical refusals, empty/oversized/malformed requests, provider/index errors and request isolation. API tests should run without paid calls. Once quota is available and explicitly scheduled, perform a small real local HTTP-to-graph smoke test and retain its evidence.

## 4. Measure and update the résumé after shipping

Freeze the v3 graph, model profile, score rubric and threshold. Compare v2.1 and v3 on the same corrected development references, including known false refusals, multihop misses and unknown private facts. Measure supported correctness, false refusals, unsupported answers, extra tokens/time and whether the second retrieval actually adds needed evidence. More retries alone are not an improvement.

Author fresh confirmation questions after the freeze, run them completely and source-review failures/suspected judge errors. Existing inspected questions are regression cases. Keep missing denominators, reference errata, shared-authorship limits and automated versus source-reviewed labels explicit. Do not choose the threshold from confirmation outcomes.

Only then use wording such as:

> Built a LangGraph Retrieval–Reasoning–Judge workflow with a bounded, quality-threshold retrieval retry and exposed it through validated FastAPI REST endpoints.

That wording requires passing retry behavior tests, API contract tests and actual local HTTP evidence. Quantitative improvement claims additionally require the completed matched evaluation; use the measured numbers and scope. Use current model names, or “Groq-hosted LLMs”; do not switch models merely to preserve an outdated technology label. Confirm the actual project dates separately.

## Delivery order

1. Push the tested stable v2.1 snapshot with the [résumé audit](RESUME_AUDIT.md), current limitations and this plan.
2. Implement and test the v3 role/score contract and bounded retry together.
3. Add the thin FastAPI interface and its contract/isolation tests.
4. Complete measured validation, then update the résumé to match shipped behavior.

The stable v2.1 push completed item 1. The initial v3 implementation completed items 2 and 3 with 152 passing tests, local native controls and real HTTP smoke evidence. Refinement now has 176 passing tests, independent role backends, separate cited-support/context checks within the Judge role and additional evidence/protocol repairs. Native validation of the latest repair is incomplete, so the candidate is not promoted. Item 4's complete matched quality comparison and fresh confirmation remain future work; no numerical accuracy improvement is claimed. The [upgrade roadmap](V3_UPGRADE_ROADMAP.md) gives the next acceptance criteria and learning sequence.
