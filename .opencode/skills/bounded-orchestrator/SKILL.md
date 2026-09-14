---
name: bounded-orchestrator
description: Coordinate material OpenCode repository work with bounded roles, one writer per scope, frozen candidates, finite review loops, local task history, and optional candidate-bound evaluation.
---

# Bounded Orchestrator

Use this workflow for multi-file features, cross-component debugging, or high-risk changes. Skip it for trivial localized edits.

1. The owner defines acceptance criteria and a dependency-aware ledger.
2. Explorer or researcher gathers missing evidence without writing.
3. The owner assigns one implementer exclusive ownership of each write scope.
4. The implementer changes only that scope and runs focused checks.
5. Freeze the exact candidate with `.opencode/tools/candidate.py freeze`.
6. The verifier checks that candidate. A failure routes through the owner; the verifier never repairs it.
7. Run a configured shell-free local evaluation when the ledger requires one.
8. The reviewer independently reviews the same candidate. Freeze again after any repair.
9. Finish only when all required ledger work and required evaluation pass.

Every child must deny `subagent`. The owner never writes implementation directly. Review loops are finite: after two failed repair attempts, stop and report the evidence. Do not store prompts, source, transcripts, credentials, or secrets in runtime metadata.

OpenCode V2 does not document a numeric subagent-depth setting. This package enforces one level by allowing the owner to call a fixed specialist list and denying `subagent` for every child.

See [task contract](references/task-contract.md), [review protocol](references/review-protocol.md), and [escalation](references/escalation.md).
