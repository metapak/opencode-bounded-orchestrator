# Schema-2 task ledger

The local ledger records short task IDs, labels, dependencies, owner role, state, attempts, timestamps, and route-back metadata. States include `interrupted`, `waiting_user`, and `needs_repair`. It deliberately rejects prompt, transcript, source, log, and secret storage. Runtime JSON is ignored by Git and uses restrictive permissions where supported.

Run `python3 .opencode/tools/ledger.py --help` for commands. Required incomplete tasks, exhausted repairs, or a stale required evaluation block review readiness.
