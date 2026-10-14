# V2.1 initial native confirmation

Implementation frozen at `6594c2a` before authoring these three questions. The same coding assistant authored and source-checked the references. Source material was inspected during project work; this is not an independent, blind, or representative benchmark. Questions were not used to alter the frozen retrieval limits or gate prompts.

Two answerable cases check code configuration in the Celery migration guide and Python handler completion. A third asks for private Lyra configuration unavailable in the public corpus. Exact reference evidence:

- `guides/celery-to-standalone-activity.mdx`, Step 5, `worker.py`: `activities=[send_welcome_email]` and `ThreadPoolExecutor(max_workers=5)`.
- `develop/python/workflows/message-passing.mdx`, “Ensure your handlers finish before the Workflow completes”: `await workflow.wait_condition(workflow.all_handlers_finished)`.
- Public examples cannot establish the private repository's actual thread-pool setting.

Compare default `graph_v2` with `graph_v2_1`, using the same 14,414-chunk index, generation model, judge/gate model, prompts and temperature. For this bounded initial study, set `GROQ_MAX_RETRIES=0` in both processes and disable tracing. This avoids long SDK quota retries; actual settings are retained in each run's inputs. Parsing retries and evaluator judge attempts retain their existing behavior. Preserve provider errors and missing judgments; an incomplete attempt is not a quality result. RPS remains the configured common value.

The separate one-question `section_development_probe.jsonl` reuses the known Worker-command regression. It tests whether recovered context reaches a native answer, but must never be combined with the fresh confirmation score. Existing v2 confirmation and ten-question regression data remain unchanged.

Record per-question context, gates, answers, citations, correctness/faithfulness labels, refusal tradeoffs, token metadata and wall time. These small fallible model-judged results do not establish general superiority or independent human validation. A new question changes the three-question confirmation score by 33 percentage points.
