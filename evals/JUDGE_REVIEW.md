# Judge review — 14 October 2026

The published correctness values are automated judge labels, not independently verified ground-truth accuracy. Eight positive/negative/adversarial controls passed; spot-checking the actual evaluation still found a confirmed false-negative.

## Confirmed false-negative: dev-08

Question: In the Python Google GenAI hello-world example, what task_queue name is used to execute the Workflow?

Reference: google-genai-hello-world

Actual generated answer: The example uses the task queue named "google-genai-hello-world".

Automated verdict: incorrect.

Judge explanation: The answer misspells the task queue name – it says "google-geni-hello-world" instead of the correct "google-genai-hello-world" as given in the reference.

The actual answer contains the exact reference identifier, google-genai-hello-world. The judge's alleged spelling, google-geni-hello-world, does not occur in the answer. This is a verified judge misreading, not a model spelling error. The faithful verdict also confirms the correct identifier in retrieved code.

Evidence: [raw attempt](results/verified/graph_v1/e13b5e6dd44ede10c5f55f8e798477049e4d60775d5eb064aa94836aa8be31e4/20261014T033524238124Z-1faf06c2/partial.jsonl), [run inputs](results/verified/graph_v1/e13b5e6dd44ede10c5f55f8e798477049e4d60775d5eb064aa94836aa8be31e4/20261014T033524238124Z-1faf06c2/inputs.json).

The original verdict and aggregate are preserved. Correcting this case alone changes the development count from 27/40 to 28/40 (70.0%), but that is a partial adjudication, not a fully human-reviewed score. No remaining verdict is certified by this spot-check. This review was by the coding assistant, not an independent human reviewer.

## What the recorded failures support

Of 13 automated incorrect labels, seven answers were exact refusals. Several refusals occur with source recall=1.0: retrieving the right document does not establish that its answer-bearing chunk was retrieved. Source recall is therefore a document-level diagnostic and must be interpreted with retained chunk text, correctness, and faithfulness.

Other non-refusal failures include incomplete answers (such as a short Java class name instead of the fully qualified mainClass), a wrong abstraction level (Temporal Server services instead of the Server plus Persistence/Visibility stores), and differences between reference answers and generated alternatives. These need case-by-case review before tuning.

The next quality experiment should use a frozen reviewed development set, preserve this judge issue, and confirm on new held-out data. Do not silently patch model outputs, convert missing judgments into guesses, tune repeatedly on holdout, or equate an LLM judge with independent verification.

## V2 confirmation: scope false-positive and disputed API label

For v2-confirm-02, v1 answered the private Nova production configuration question with “The configured heartbeat timeout is 30 seconds.” It cited `guides/worker-execution-affinity.mdx`. The faithfulness judge returned true because the example contains that timeout. The public example does not establish Nova's private configuration, so this is a confirmed scope error in the faithfulness verdict. Exact-refusal correctness is false and remains reliable for detecting this failure. A zero automated unsupported-answer rate cannot be interpreted as zero fabricated private facts.

For v2-confirm-01, v1 answered “In Go you record a heartbeat with the RecordActivityHeartbeat (RecordHeartbeat) API, and in Python you use the heartbeat() API.” The correctness judge rejected the Go API and the missing `activity.` prefix in Python. The reference explicitly accepts `heartbeat()`; that part of the rationale is wrong. The Go source also documents external heartbeats through `temporalClient.RecordActivityHeartbeat`, as well as the in-Activity `activity.RecordHeartbeat`. The question did not restrict which situation it meant. The generated parenthetical conflates names, so this review records a disputed label rather than silently certifying it correct. The original reference and verdict are preserved; this row cannot support a small v1/v2 accuracy advantage.

Evidence: [fresh v1 checkpoint](results/verified/graph_v1/180fba46b3a145e2b5f19ccced278f664e2c4a06b5b792f1605f8fd07c3d87be/20261014T042408031523Z-f93405a4/partial.jsonl), [confirmation protocol](CONFIRMATION_V2.md). The four incorrect holdout labels used by replay were also reviewed: one Activity Execution answer omits the chain of Activity Task Executions, two are canonical refusals on answerable questions, and one invents private Acme retry configuration from a public example. Their original labels remain in replay.

## Replay retention disagreement: correct fact, incomplete cited evidence

For “I shortened Namespace retention, but old closed Workflows did not disappear sooner. Why?”, v1 correctly answered that the change does not alter old cleanup timers and suggested manual deletion. It cited chunk 5, the “Manual cleanup of closed Workflow Executions” section. That chunk supports the deletion remedy but does not state that retention changes preserve existing timers. The explicit causal statement exists elsewhere in `encyclopedia/temporal-service/temporal-server.mdx`, outside the retrieved chunk. The original faithfulness judge nevertheless marked every claim supported.

V2's sufficiency check rejected the available evidence. This is a defensible conservative decision, rather than proof of an erroneous gate. The answerable-refusal metric still counts it as a false refusal because its denominator is questions answerable in the full corpus. Review retrieval coverage and cited claim support alongside correctness before calling a lower refusal rate better.
