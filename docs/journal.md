# Journal

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
