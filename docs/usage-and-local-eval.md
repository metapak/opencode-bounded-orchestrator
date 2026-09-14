# Usage report and local evaluation

`usage_report.py` executes the verified CLI command `opencode stats --json` and returns that JSON under `reported`. It does not inspect session transcripts, infer missing tokens, estimate costs, or claim a quota percentage. Missing CLI, command failure, timeout, or invalid JSON produces a clear `unavailable` result and nonzero exit.

`local_eval.py` accepts an explicit JSON manifest containing `label`, `argv`, and a bounded timeout. It uses `shell=False`, stores hashes and optional sanitized tail only, and fingerprints the Git candidate before and after the command. A changed candidate becomes `candidate_changed`. Ledger readiness rejects missing, failed, or stale required evaluation.
