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
