# Upgrade plan after the résumé implementation

The three roles, numeric score, conditional retrieval retry, FastAPI endpoints and genuine local Meta Llama inference are implemented. Stability is a separate gate. The inspected M4 Mac mini has 16 GiB unified memory; Llama 3.1 8B Q4_K_M fits at an 8K context with one prediction. Its observed model load report is 4.58 GiB, not total system memory. Keep the pinned BGE embedding index and avoid further model downloads until the current profile is understood.

## Milestones and acceptance criteria

| Order | Work | Evidence required before completion |
|---|---|---|
| 1: finish v3 stability | Repair wrong-operation acceptance, preserve literal citations and strict refusals; freeze local Llama/Groq Judge profile | Native positive and negative scope controls, all fixed 12 regression questions completed and source-reviewed, full tests, isolated offline checks, changed-code Linux CI, real HTTP answer/refusal evidence |
| 2: measure quality | Run the corrected 40-question development set and compare with a fixed v2.1 baseline; then write fresh confirmation questions after freezing code | Complete eligible denominators; source review of unsupported answers, false refusals and evaluator disagreements; reported latency and usage; no accuracy percentage from partial runs |
| 3: prove retry value | Use retained first/second-attempt evidence to diagnose whether the missing fact was acquired and used | A controlled paired comparison with retry enabled/disabled, same references and model settings; report both gains and extra latency/tokens |
| 4: make the demonstration portable | Reproduce setup and API requests on the actual Windows presentation machine | Frozen dependency installation, corpus/index integrity, real HTTP smoke and restart/recovery; document CPU/GPU/model differences |
| 5: expand only for a concrete user | Add document ingestion, UI or hosted access when a use case requires it | Access filtering before model/tracing for private data; authentication and concurrency/load validation before hosted multi-user claims |

The fixed scoring rubric is in the [stability scorecard](../evals/V3_STABILITY_SCORECARD.md). Both v3 and overall scores must be justified separately. An 8.5 engineering score is not 85% answer accuracy. Full development and fresh confirmation remain the stronger 9/10 gate. A reproduced major support failure blocks promotion regardless of weighted arithmetic.

## Model choice on this machine

Use local Llama 3.1 8B for Reasoning while investigating the hybrid profile. The tested local 3B/8B self-Judges and two 4B Qwen experiments were insufficient; valid JSON and hardware fit did not establish reliable judgment. Do not silently fall back to them when Groq quota is exhausted. Preserve completed graph nodes, inspect the recorded cooldown and resume identical inputs.

The checked Groq account has no generative Llama offering. The truthful stack is **LangGraph, FastAPI, Groq, LM Studio, Meta Llama, Python**. Local Llama is not Groq-hosted Llama. The tested hybrid sends public questions and cited evidence to Groq. [LM Studio's structured-output documentation](https://lmstudio.ai/docs/developer/openai-compat/structured-output) confirms schema support and cautions that smaller models may struggle; schema compliance is a format guarantee, not factual support.

## Learning sequence alongside the work

1. Trace one request aloud: request validation, retrieval, cited generation, Judge score, branch, retry bound and response. Explain why a provider error differs from a valid refusal.
2. Learn retrieval basics through this implementation: chunks, embeddings, lexical search, reciprocal-rank fusion, source recall and context caps. Inspect one missed fact in the pinned source.
3. Learn LangGraph state and conditional edges by drawing the graph, then predict the node sequence for a first-pass answer, successful retry and exhausted retry. Run the corresponding tests.
4. Learn FastAPI/Pydantic through `/docs`: try valid input, extra fields, wrong types, an oversized question and concurrent inference. Explain process health versus backend readiness.
5. Learn evaluation: compute eligible/scored/missing counts, distinguish structural citations from semantic support, and source-review an automated grader disagreement.

The readiness check is practical: give a 60-second project explanation, answer two follow-ups, then change or diagnose one small case without copying an answer. Do not add numerical résumé claims until their measured scope is complete. Use actual project dates; the supplied 2025 date remains unverified.
