# Journal

Historical entries below describe the original experiment. The 14 October 2026 audit supersedes claims that low v0 performance proves no memorization, that refusal substring failures count fabrications, or that the original Unjudged counter exposes every missing judgment. See PROJECT_AUDIT.md, architecture.md, and verified result artifacts for current behavior.

Dated record of what was built, what the numbers said, and what was decided next.

## 2026-09-01 — Project start, v1 built

**Decisions made before writing code**

- *Single graph, not a multi-agent swarm.* Multi-agent orchestration pays off only
  for genuinely heterogeneous sources; starting there would buy latency and failure
  surface without evidence it helps.
- *Separate graph files per version.* Locked in so that cross-version comparison is a
  for-loop rather than a git archaeology exercise.
- *Corpus: Temporal docs.* Chosen for low parametric contamination, dense jargon, and
  a standalone docs repo that clones without a codebase attached.
- *Groq + local BGE embeddings.* No OpenAI access. Local embeddings remove quota
  pressure from the loop that runs most often.

**Built:** ingestion (9,765 chunks / 762 files), v0 baseline, v1 linear graph,
eval runner, comparison table, 5 tests.

**Surprise worth recording:** the corpus contains 97 instances of `<String` — Java
and Rust generics inside code fences, not JSX. A naive tag-stripping cleaner would
have quietly corrupted the code samples that answer a large share of developer
questions. Fixed by only cleaning prose segments between ``` fences. This is the kind
of failure that produces bad retrieval with no error message.

**Blocked on:** a Groq API key, and human verification of the golden set.

**Next:** draft 40 golden questions, verify them by hand, run v0 and v1, commit the
baseline table. No v2 code before that.

## 2026-09-01 — Model selection corrected

`llama-3.3-70b-versatile` is not available on this Groq account; the API returns
`model_not_found`. Querying `/v1/models` showed the account's active text models,
of which only the `openai/gpt-oss-*` family declares `structured_outputs` support.

Chose **`openai/gpt-oss-120b`** (131k context, tools + structured outputs). Structured
output matters more than raw size here: the eval judges and every v2 grader node
depend on `with_structured_output`, and a model that only offers `json_mode` would
force hand-rolled JSON parsing and retry logic in each of them.

Verified both plain and structured calls succeed.

**Aside:** the `/v1/models` endpoint returns 403 to Python's `urllib` but 200 to
`curl` — a User-Agent filter, not a permissions problem. Worth knowing before
misreading it as a key scope issue.

## 2026-09-01 — Structured output: json_schema, not tool calling

Golden-set drafting failed intermittently with
`tool_use_failed: Tool choice is required, but model did not call a tool`.

Cause: `with_structured_output()` defaults to function calling. gpt-oss is a
reasoning model, and on longer passages it replies in prose rather than invoking
the tool. Groq then rejects the response.

Tested all three methods against this model:

| method | result |
|---|---|
| `json_schema` | works |
| `json_mode` | rejected — requires the literal word "json" in the messages |
| `function_calling` | works on short input, fails on long — **intermittent** |

Intermittent is the dangerous one. It does not fail loudly; it silently thins
the golden set, and a golden set quietly missing its hardest questions is worse
than one that fails to build at all.

Fixed at the source with `llm.structured()`, which both the drafter and the eval
judges now route through. Every v2 grader node will use it too — those nodes are
entirely structured-output calls, so this would have surfaced as flaky grading.

## 2026-09-01 — Human review caught a drafting bug, not just bad rows

Verified all 40 drafted questions against source. Direct, jargon, ambiguous, and
unanswerable buckets were clean. **Four of eight multihop rows were wrong**, and
every failure sat in the second half of the two-part answer:

| Row | Failure |
|---|---|
| 21 | Arithmetic error — confused the per-TRU rate with the 6-TRU total |
| 23 | Fabricated a resolution the source never gives; the doc stops mid-thought |
| 24 | Reversed the source's meaning about assumed Temporal knowledge |
| 25 | Invented API behaviour supported by neither cited file |

**Root cause was in the drafter, not the model.** Multihop drafting used
`random.sample(chunks, 2)` — two arbitrary chunks out of 9,765, which are
essentially never related. The prompt then demanded "one question that requires
BOTH to answer." With no real connection available, the only way to comply is to
invent one. The prompt was a fabrication instruction.

Fixed with `_related_pair()`: pick a chunk, then take its nearest neighbour from a
*different* file via the vector store. The prompt now also forbids inference and
arithmetic, and allows the model to answer "SKIP" rather than force a link.
Redrafted pairs are things like `go/external-storage` + `typescript/external-storage`
and `cli/namespace` + `cloud/namespaces` — genuinely connected material.

**Why this matters more than the four rows.** An LLM judge would have passed all
four: they are fluent, well-structured, and cite real files. Only reading the
source catches them. Had they entered the golden set, every faithfulness number
for v1, v2, and v3 would have been quietly measured against fabricated ground
truth — and the errors would have looked like model failures rather than
dataset failures. This is the concrete reason the human verification gate exists.

## 2026-09-01 — An automated screen that could not be trusted

Human review flagged row 25 as single-source: the answer sat entirely inside
`namespace.mdx`, so the second citation did no work. That generalises — a
"multihop" question answerable from one document cannot justify v3's iterative
retrieval, and because `recall_at_k` uses set intersection, such a row scores a
hit when only one source is retrieved. It inflates the metric.

Built an LLM screen to check the whole bucket: for each cited document, is the
entire answer supported by that document alone? **It disagreed with the
line-cited human reading in both directions** — calling row 25 genuinely
multihop (it is not) and row 24 single-source (verified as needing both, with
line numbers). Likely cause: documents are truncated to 9,000 characters, so
verdicts partly reflect what survived truncation rather than what the document
says.

Discarded the screen rather than acting on it. Recorded because the failure is
instructive: it is the same mistake as trusting an LLM judge to verify the golden
set, one level up. A check that disagrees with ground truth in both directions is
worse than no check, because its output looks authoritative.

Reading rows by eye then found a second defect the factual review could not
catch: row 26 stapled GCP Private Service Connect to the .NET `Patched` marker
with invented framing. Both halves were true, so it passed factual checking, but
no real user would ask it. Rows 26 and 27 — the last survivors of the broken
pairing — were regenerated with an added rule forbidding stapled sub-questions.

The whole multihop bucket is now generated by one consistent method.

## 2026-09-01 — The rate limit that matters is tokens, not requests

First full v0 run died at question ~22:

```
429: Rate limit reached ... on tokens per minute (TPM):
     Limit 8000, Used 3553, Requested 4456
```

`InMemoryRateLimiter` throttles **requests per second**, and its own
documentation notes it does not account for request size. The free-tier ceiling
is 8,000 **tokens** per minute. A v1 call carrying five retrieved chunks costs
roughly 4,500 tokens, so fewer than two calls per minute fit — no RPS value
could have prevented this. Throttling the wrong dimension gave a false sense of
safety.

Read the actual limits from the API rather than guessing:

| | requests/day | tokens/min |
|---|---|---|
| `gpt-oss-120b` | 1000 | 8000 |
| `gpt-oss-20b` | 1000 | 8000 |

**Buckets are per model.** Three fixes followed:

1. `max_retries=8`. The token bucket refills in well under a second
   (`x-ratelimit-reset-tokens: 547ms`), so a 429 usually clears by waiting.
2. Judges moved to `gpt-oss-20b` at `reasoning_effort="low"` — a second
   independent 8,000 TPM budget, and binary verdicts against a supplied
   reference do not need the larger model. Generation stays on 120b, and
   `structured()` still defaults to the generation model so golden-set drafting
   is not silently downgraded.
3. Per-question checkpointing to `results/<graph>.partial.jsonl`. A run takes
   tens of minutes; losing all of it to one 429 near the end is not acceptable.
   Reruns resume.

**Second bug, quieter and worse.** The crashed run reported *exit code 0*. The
command was piped through `grep`, so the pipeline returned grep's status and the
Python traceback was masked. A failed eval looked like a completed one. Fixed by
running under `set -o pipefail`.

## 2026-09-01 — Judges that fail intermittently

Second v0 attempt died at question 8 with a different error:

```
400 output_parse_failed
failed_generation: 'We need to output JSON with property correct boolean.
                    ... They don't match. So correct=false.'
```

At `reasoning_effort="low"` the 20b judge skipped the structured-emission
discipline and returned its reasoning where the JSON object belonged. Removed
the low setting.

Tested four model/effort combinations against three fixed cases first: **all four
passed**, which is the important part — the failure is intermittent, not
deterministic, so no configuration choice can fix it. The run has to tolerate it.
(Worth noting: `gpt-oss-120b` at low effort got one case *wrong*, judging a clear
mismatch as correct. A small sample, but not an argument for the larger model as
judge.)

Added `_judge()`: retry four times, and on total failure return `None` so the
caller leaves that metric unset. **It deliberately does not substitute a
default.** A guessed verdict is fabricated data, which is precisely the failure
this harness exists to detect — quietly defaulting to `False` would have
depressed correctness scores with no visible cause. Unscored rows are excluded
from the means and counted in a new `unjudged` column, so a shrunken denominator
cannot pass unnoticed.

Checkpointing proved itself here: the crash at question 8 cost nothing, and the
rerun resumed from 8.

## 2026-09-01 — v1 baseline. Phase gate met.

| Version | Correct | Faithful | Recall@5 | Refuses | Unjudged |
|---|---|---|---|---|---|
| v0 (no retrieval) | 0.425 | — | — | 0.625 | 0 |
| v1 (retrieve→generate) | 0.800 | 0.839 | 0.688 | 0.875 | 0 |

Answerable-only correctness: **0.375 → 0.781**. Fabrication on unanswerable
questions: **3/8 → 1/8**. Retrieval is doing real work.

**The corpus choice is vindicated, with one exception.** v0 scoring 0.375 means
the model does not already know this material, so v1's gain measures retrieval
rather than memorisation. But the jargon bucket scored 0.750 at v0 — gpt-oss
already knows Temporal's conceptual vocabulary (Parent Close Policy, Local
Activity, Nexus Registry).

Per bucket at v1:

| bucket | correct | recall@5 |
|---|---|---|
| direct | 0.667 | 0.667 |
| jargon | **1.000** | **0.250** |
| multihop | 0.875 | 1.000 |
| ambiguous | 0.500 | 1.000 |

**The jargon row is the interesting failure.** Perfect answers on a quarter of
the retrieval recall. Two candidate explanations, and they imply opposite fixes:

1. The model answers from parametric memory (v0 already 0.750), so retrieval
   quality does not affect the score.
2. `recall_at_k` does exact source-path matching. Glossary terms are documented
   in both `glossary.md` and under `encyclopedia/`, so retrieving an equally
   valid alternative file counts as a miss. The metric would be undercounting.

If (2), the recall number is wrong rather than the retriever. Single-path ground
truth is too strict for a corpus that documents the same concept in several
places. **This must be resolved before v2**, because v2's hybrid BM25 retrieval
is justified precisely by fixing jargon retrieval — and right now the jargon
bucket has 0.25 of correctness headroom and a recall metric that may be
measuring nothing. Fixing the metric, and rewriting jargon questions to target
specific identifiers (flag names, config keys, CLI arguments) rather than
definable concepts, is the first v2 task.

**Gate met:** v1 built, evaluated, numbers committed. v2 may begin.
