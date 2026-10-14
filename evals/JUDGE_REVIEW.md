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
