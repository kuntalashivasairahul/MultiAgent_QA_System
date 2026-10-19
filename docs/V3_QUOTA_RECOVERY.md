# V3 provider recovery, 19 October 2026

The Groq daily token bucket prevented completion of the previous native study. Waiting and replaying that same bucket did not create enough capacity. V3 now supports an explicit Gemini backend for Reasoning, the graph Judge, and the separately selected evaluation grader, using the already installed OpenAI-compatible client. Local Meta Llama and Groq remain available. This does not change the three workflow roles or the one-retrieval-retry limit.

## What was reused from Harrison

Harrison's `backend/llm/router.py` separates provider outages from semantic decisions; its `KeyManager` cools a key for the affected model instead of discarding the whole provider. The QA implementation uses the smaller part needed here: a fixed Gemini endpoint, a bounded pool of configured keys, shared per-model pacing, and per-model/key cooldowns. It does not import Harrison's medical code or corpus.

- Configure `GEMINI_API_KEY`, optionally followed by `GEMINI_API_KEY_1` through `GEMINI_API_KEY_8`. Duplicate and empty values are removed. Keys are never included in profiles or evaluation artifacts.
- Each model call tries at most the configured slots. A 429, connection failure, timeout or provider 5xx cools that slot and allows another configured slot for the **same model**. Numeric `Retry-After` is honored; absent/invalid values use 60 seconds. Cooldowns and pacing are process-local.
- Authentication/configuration failures, malformed output and negative semantic verdicts do not trigger key failover. Existing schema/literal-quote correction remains bounded separately. Pool exhaustion remains an operational error, never a supported answer or an `I don't know.` result.
- `GEMINI_RPS=0.1` shares one request limiter across that process's clients for the same model. It is request pacing, not a token/day quota guarantee. Keys belonging to the same provider project can share capacity; adding keys does not multiply that shared quota.
- Graph checkpoints retain successful retrieval, generation and cited-support nodes. External grader errors retain missing metrics and can resume without regenerating completed answers.

The inspected machine reused the owner's already configured Harrison Gemini credentials in the ignored local `.env`. No key values were printed or committed. Reproduction elsewhere requires that operator's own credentials. Mistral was also probed and returned 429; it was not added as an unvalidated runtime backend.

## Explicit alternative profile

Start LM Studio and load the recorded Llama weights as described in [the local guide](V3_LOCAL_UPGRADE.md). Then:

```sh
LANGSMITH_TRACING=false QA_BACKEND=lmstudio QA_MODEL=llama-3.1-8b-instruct \
  QA_JUDGE_BACKEND=gemini QA_JUDGE_MODEL=gemini-3.5-flash \
  uv run uvicorn api:app --host 127.0.0.1 --port 8000
```

The Gemini graph Judge receives the question, draft and bounded public evidence. When evaluation is requested, its external grader also receives the reference answer. Keep tracing off unless that additional data flow is intended. The selected Llama remains **local**, not Groq-hosted. Gemini 2.5 Flash uses `reasoning_effort=none`; other Gemini selections use `low`. Model, endpoint, protocol, thinking setting, rate, slot count and failover policy are fingerprinted. Provider/model changes select a new evaluation fingerprint rather than mixing results from different profiles.

```sh
export LANGSMITH_TRACING=false
export QA_BACKEND=lmstudio QA_MODEL=llama-3.1-8b-instruct
export QA_JUDGE_BACKEND=gemini QA_JUDGE_MODEL=gemini-3.5-flash
export QA_EVAL_BACKEND=gemini QA_EVAL_MODEL=gemini-2.5-flash
export LMSTUDIO_MODEL_SHA256=f2be3e1a239c12c9f3f01a962b11fb2807f8032fdb63b0a5502ea42ddef55e44

uv run python evals/calibrate_v3.py
uv run python evals/run_eval.py graph_v3 12 --dataset evals/v3_stability_regression.jsonl
```

Repeat the same command and environment to resume missing work. Do not use `--fresh` for recovery. Stop competing operators before starting another run. Switching the backend explicitly back to `groq` preserves the existing Groq path; key failover never silently changes models/providers inside a frozen study.

## Validation and scoring

Current evidence, source adjudications and the separate V3/overall weighted assessments belong in [the stability scorecard](../evals/V3_STABILITY_SCORECARD.md). Synthetic controls establish specific safety/protocol behavior, not general accuracy. The fixed 12-question study is inspected development regression coverage, not fresh confirmation. The original six-area scoring rubric and the stronger 40-question/fresh-confirmation gate remain unchanged.

The provider compatibility and thinking settings were checked against [Google's official OpenAI compatibility documentation](https://ai.google.dev/gemini-api/docs/openai). Credentials and capacity were checked through actual model calls; a listed model alone was not treated as usable capacity.
