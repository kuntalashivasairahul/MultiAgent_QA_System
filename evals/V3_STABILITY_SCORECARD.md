# V3 stability and overall project assessment

Target: refine v3 into a stable public-document research prototype with both a v3 engineering score and an overall project score of at least 8.5/10. Scores are coding-assistant assessments, not independent certification, measured answer accuracy or a claim of production readiness. The historical v2.1 score remains 8.63; it is not automatically transferred to v3.

## Fixed rubric and release requirements

Use the existing [six-area rubric](V21_SCORECARD.md), unchanged: architecture/scope 20%, ingestion/retrieval 15%, evaluation validity 25%, testing 15%, reproducibility/runtime 15%, documentation 10%. The weighted mean is computed from retained category ratings. Report the current v3 and the current overall project separately; do not average historical version scores.

Before calling this release stable:

1. Demonstrate named Retrieval, Reasoning and Judge roles, typed state handoff, numeric rubric scoring, conditional branching, at most one quality-triggered retrieval retry and validated FastAPI REST endpoints.
2. Demonstrate genuine Meta Llama inference on the inspected local machine. Distinguish it from Groq-hosted Llama, which the inspected account does not offer. Keep the current Groq backend functional and label actual model names.
3. Reproduce and repair material correctness, protocol, recovery or request-isolation findings. Maintain canonical citations, literal evidence checks, refusals and bounded execution.
4. Complete a broader native development study of the proposed stable profile, retaining operational failures, denominators, retry evidence, usage and latency. Source-review incorrect, unsupported and suspicious outcomes; document model limitations without promoting partial scores. A successful smoke or high test count is insufficient.
5. Pass the current full suite, clean offline source-snapshot checks and changed-code Linux CI, including actual retrieval/index integration. Verify the frozen release inputs match their recorded artifacts.
6. Publish usable startup/recovery commands, current evidence, an explicit résumé claim matrix and separate v3/overall score calculations. Keep private-data service readiness, Windows portability, calibrated confidence and broad accuracy gains outside unproven claims.

Complete 40-question development and fresh confirmation with all eligible metrics remains the existing 9/10 evaluation gate. An 8.5 assessment does not imply that stronger gate passed. Scores may only rise when evidence supports the relevant category; unresolved major supported-scope findings prevent stability regardless of the arithmetic.

## Review baseline: `fabc052`

The implementation supplies the requested graph roles, threshold/retry edge, REST API and actual local Llama path. Initial evidence was 152 local tests, 147 isolated offline tests, four native Judge controls and three native HTTP requests across local/cloud profiles. That established contracts and a few runtime paths, not broad semantic reliability.

Fresh retrieval diagnosis on the current dependency/index fingerprint finds all 11 selected facts, all seven complete diagnostic contexts and all 33 answerable development source groups. These are development-tuned labels, not representative accuracy. [Retained diagnosis](results/section_retrieval/9e1d128004114972533edc2b4fdfffee1127bff776c5f284186010b6ad5ba06e/result.json).

The broader native 3B run has already reproduced false refusals and an unsupported answer. It remains a development diagnostic until complete. No new stable score is awarded while those observations are under review.

| Finding | Status | Required action/evidence |
|---|---|---|
| Small-model Judge rejects directly supported answers | Reproduced on development questions | Review native outputs and choose/verify a more reliable stable model profile |
| Small-model Judge accepts an unsupported answer | Reproduced on development question | Retain exact evidence, repair or change the selected profile, retest adversarial and answerable cases |
| Missing-aspect hint can echo a prompt instruction | Reproduced | Preserve as a model failure; inspect actual retry usefulness rather than counting another search as a gain |
| Retry retention can omit earlier cited chunks | Under review | Check cited-evidence retention under the shared context cap with a regression if a fix is needed |
| Changed-code hosted CI | Passed for `fabc052` | [Run 39133573448](https://github.com/kuntalashivasairahul/MultiAgent_QA_System/actions/runs/39133573448); later code changes require new CI |

Further iterations and final ratings will be appended with their exact evidence. The target score is not yet claimed.

## Iteration 1: measured failures and evidence-retention repair

The [frozen initial 3B study](results/verified/graph_v3/e35862494ee015671f4fd1d51b8085afab3ac9ce13c9806357b5d0cc849710b9/20261018T140101939329Z-0b7ceabe/result.json) attempted all 40 corrected development questions. Three nonliteral-quote failures leave the result **incomplete**, with 37 completed generations/scorings. Automated correctness is 15/37, not a full-dataset accuracy estimate. There are 21 answerable refusals and two source-confirmed unsupported acceptances. The [review](results/v3_initial_3b_review.json) distinguishes seven supported answer reviews, seven expected unknown-fact refusals, two unsupported citation scopes and 21 answerable refusals whose generator/Judge causation was not fully adjudicated. Structural checks validate all 775 retained attempt documents and 36 accepted literal Judge quotes. Literal quotes alone did not prevent the two semantic scope errors. This model profile is rejected for promotion.

The retry implementation now prioritizes previously cited chunks in the retained portion of its fresh/retained mix. The reproduced failing regression passes. Context remains capped at 12 chunks and 8,000 text characters; prioritization does not promise that arbitrarily many cited chunks all fit. The Judge instruction also clarifies that concise answers can be complete, similar commands do not prove the requested operation, and a retry hint must contain search keywords. These are general scope instructions, not a relaxation of citation/quote validation.

Current full suite: **153 tests pass in 17.74 seconds**, including all five integration tests. A clean source snapshot without credentials, `.env`, corpus or index passes **148 offline tests in 8.69 seconds**, with five integration tests explicitly deselected; this reused installed locked dependencies. The [interim verification](results/v3_repair_verification.json) records the repair and input hashes. Native validation after the prompt change uses [15 inspected development controls](v3_judge_controls.json) through the actual Judge/threshold path, via `uv run python evals/calibrate_v3.py`. The [repaired-prompt 3B profile](results/calibration_v3/0e4561c2bb8bf48ecb76148baeb9e082c14b4c785d4b6232d4bb785ddc8b0b73/result.json) scores all 15 but passes only **9/15**, including confirmed false positives and false negatives. Prompt edits alone are insufficient. Failed controls remain retained and cached; the command exits nonzero rather than promoting a partial pass.

A Meta Llama 3.1 8B Instruct Q4_K_M candidate is being downloaded from the [LM Studio Community model repository](https://huggingface.co/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF). It has not yet been loaded, measured or selected. The stable profile and both new scores remain unproven pending model validation and release checks.
