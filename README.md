# Temporal QA / RAG Evaluation

A versioned LangGraph experiment over a pinned snapshot of public Temporal documentation. v0 is a model-only baseline; v1 retrieves five chunks and generates an answer with validated citation IDs; v2 adds evidence sufficiency and cited-claim support checks. Multiple agents, corrective loops, hybrid search, private-data access control, and memory are not implemented.

Model-only performance measures answering without supplied documents. It cannot establish whether training data contained Temporal documentation.

## Setup

Python 3.12 is selected by .python-version. Corpus fetching requires Bash; use WSL or Git Bash on Windows.

~~~sh
uv sync
./fetch_corpus.sh
uv run python ingest.py
test -f .env || cp .env.example .env
~~~

Set GROQ_API_KEY in .env. CORPUS_REVISION pins the Git snapshot. Fetching refuses local edits and preserves old checkouts before replacement. Embeddings use a pinned BGE-small revision on CPU; the initial model download needs network access. Generation, drafting, and judging call Groq.

Indexing publishes a new fingerprinted collection after every chunk is present. Repeating the same build does not duplicate documents. Old collections remain recoverable. Corpus, pipeline, or dependency changes require a rebuild; a missing/mismatched index fails clearly.

LangSmith tracing defaults to false in .env.example. Existing local .env preferences are preserved. Opting in can send prompts, retrieved documents, and answers to LangSmith. This implementation supports public data only. Private sources require identity filtering before generation/tracing and dedicated access-control tests.

## Use and verification

~~~sh
uv run pytest -q
uv run python evals/calibrate.py
uv run python evals/calibrate_v2.py
uv run python evals/run_eval.py graph_v2
uv run python evals/run_eval.py graph_v2 --variant sufficiency
uv run python evals/run_eval.py graph_v2 --variant support
uv run python evals/run_eval.py graph_v1
uv run python evals/run_eval.py graph_v1 5
uv run python evals/run_eval.py graph_v1 --fresh
uv run python evals/compare.py
uv run python evals/compare.py --run
uv run python evals/compare.py --dataset evals/holdout.jsonl
~~~

The five-question run is exploratory and cannot overwrite a full result. Default evaluation resumes only matching inputs. --fresh and compare.py --run create new attempts while preserving prior artifacts. Restart Python after changing .env model/rate settings because clients are cached.

~~~python
from graph_v2 import graph
result = graph.invoke({"question": "What is a Local Activity in Temporal?"})
print(result["generation"])
print(result["citations"])
~~~

Graph output includes generation, documents, and citations. Citation IDs bind to actual retrieved chunks; structural validity alone does not prove claim support. Faithfulness evaluates the cited context when citations are present. Missing context produces the exact refusal: I don't know.

V2 checks that retrieved evidence answers the exact question, including entity, SDK, and scope, before generation. It then checks every claim against only the cited chunks. Failing either semantic check produces the canonical refusal; a rejected answer remains in `draft` for inspection. Grader outages, malformed verdicts, and non-verbatim evidence quotes raise errors. Output also includes `sufficiency` and `support` verdicts with reasons and checked quotes. These model-based checks can still be wrong.

The default v2 variant runs both checks; single-check variants are evaluation ablations and have distinct fingerprints. Evaluation retains gate audits, provider-reported generation/gate token usage, wall-clock generation time, false refusals, supported correct answers, and unsupported answers across **all** buckets. Empty usage metadata means unreported usage, not zero billing. Evaluation-judge tokens are outside generation usage.

## Evidence

- [V2 status and next course](evals/V2_STATUS.md): frozen implementation, calibration, comparison limits, and prioritized retrieval follow-up.
- [Frozen development baseline](evals/RESULTS_VERIFIED.md): 40 revised questions at `9dcd9ef`, per-metric coverage, raw evidence links.
- [Earlier confirmation, now a regression set](evals/RESULTS_HOLDOUT.md): 10 questions originally excluded from development runs, since inspected. Shared topics and authorship mean this is not an independent blind benchmark.
- [Reference review](evals/REVIEW.md): SDK/sample-specific questions and required/alternative evidence groups. Source-audited by the coding assistant; independent human review is not claimed.
- [Judge calibration](evals/calibration.json): positive, negative, and adversarial controls; a small calibration does not prove universal reliability.
- [Actual judge review](evals/JUDGE_REVIEW.md): a confirmed correctness false-negative, scope errors in faithfulness judgments, and a disputed API label despite passing controls. Reported metrics are automated labels, not independently certified accuracy.
- [V2 retrieval diagnosis](evals/RETRIEVAL_DIAGNOSIS_V2.md): seven refusals labeled at the chunk level, including a short code block omitted during indexing.
- [Live generation controls](evals/generation_controls.json): source/question injection and an unknown private fact; these checks mitigate risk without proving immunity to every attack.
- [Historical results](evals/RESULTS.md) and [original references](evals/history/golden_v1.jsonl): preserved, uncorrected baselines.

New artifacts live under evals/results/verified/graph/fingerprint/attempt/. They retain run inputs, answers, retrieved chunks, citations, judge prompts/verdicts/errors, and metric denominators. Code, references, corpus/index, dependency lock, actual model settings, and sample size contribute to the fingerprint. Generation is checkpointed before judging, so missing verdicts can retry without repeating successful generation. A torn final append recovers; other corruption fails explicitly.

Source recall counts every required evidence group, accepting reviewed alternatives within a group. All-sources success requires every group. Empty retrieval is a miss for retrieval-enabled graphs and N/A for v0. Exact refusal checks the whole answer; it is not a measured hallucination rate. Each metric reports eligible, scored, and missing counts.

The headline faithfulness metric covers answerable questions and counts refusals as grounded because they make no factual claim. Unsupported-answer rate also covers unanswerable questions, but still depends on a fallible judge. False-refusal rate uses questions answerable in the full corpus, so it can count a defensible refusal when retrieval omitted the necessary evidence. Interpret these together with correctness, answer-bearing chunk coverage, and retained gate reasons.

## Further work

The repaired v0/v1 baseline is frozen at commit `9dcd9ef`. Its results describe that snapshot; adding v2 changes current evaluation fingerprints. Existing holdout questions are now regression examples. Gate replay on frozen drafts measures rejection behavior without regenerating answers; it is not a fresh end-to-end accuracy comparison. Use newly authored questions after freezing code for confirmation, and report their small sample and shared authorship.

Choose retrieval changes from retained failures: lexical retrieval for demonstrated identifier misses, or rewriting for demonstrated phrasing misses. Bundled retrieval, rewriting, grading, and reflection cannot support component-specific claims without ablations. One development question changes the overall score by 2.5 percentage points; one unanswerable question changes that bucket by 12.5 points.

- [Architecture](docs/architecture.md)
- [Audit and repair status](docs/PROJECT_AUDIT.md)
- [Historical journal](docs/journal.md)
- [Original design](docs/superpowers/specs/2026-09-01-multiagent-qa-design.md)
