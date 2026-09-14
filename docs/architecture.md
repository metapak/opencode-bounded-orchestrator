# Architecture

The `owner` is the V2 primary and default agent. It can call only nine named children. Each child denies `subagent`, creating one practical delegation level without an undocumented depth setting. The owner denies edit and assigns implementation to the only edit-enabled role, `implementer`.

Read-only specialists deny shell. `verifier` and `qa-operator` allow only narrow read-only Git patterns and ask for other shell commands. Candidate fingerprints bind verification and review to exact Git state. The schema-2 ledger keeps bounded metadata for retries and resumability.

Default configuration contains no `model`, so roles inherit the current session model. Custom installation may write exact V2 `provider/model[#variant]` selectors. Mixed native providers require an explicit gate.
