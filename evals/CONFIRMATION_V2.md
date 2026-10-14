# V2 confirmation protocol

The graph/evaluator implementation was frozen at `cd815e7` before authoring these four questions. Questions were not used for prompt or retrieval tuning. The coding assistant authored and source-checked the references; no independent human or blind external validation is claimed. They cover two answerable cases (serialization order and cross-SDK heartbeat APIs) and two private facts unavailable in the public corpus. They are a narrow confirmation check, not a representative accuracy benchmark.

References in the pinned corpus:

- `encyclopedia/data-conversion/payload-codec.mdx`: the paragraph beginning “When serializing to Payloads” and the operational chain establish converter then codec.
- `develop/go/activities/timeouts.mdx`: “To Heartbeat … use the RecordHeartbeat API” and its code example.
- `develop/python/activities/timeouts.mdx`: “To Heartbeat … use the heartbeat() API” and its code example.
- Private Nova and Orion repositories are not part of this corpus. Public example timeout values or key-management guidance cannot establish their actual configuration.

Run v1 and default v2 against exactly this dataset. Preserve gate failures and missing judgments. Record provider-reported usage and latency. Treat the already inspected ten-question holdout as a regression set; apply component ablations to its retained v1 drafts in a separate replay artifact. Do not combine replay and fresh scores or tune v2 on confirmation outcomes.
