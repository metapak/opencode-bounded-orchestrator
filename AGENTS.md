# Repository guidance

This repository contains the distributable OpenCode V2 configuration and its safe installer. Keep provider/model availability claims conditional and never add credentials or runtime state.

<!-- opencode-bounded-orchestrator:start -->
## OpenCode Bounded Orchestrator

For material repository work, use the `bounded-orchestrator` skill. The primary `owner` plans and delegates. Only `implementer` writes within an explicit scope. Verification and review use a frozen candidate, review loops are finite, and unfinished work is recorded in the local schema-2 ledger. Project-specific local evaluation is optional and must be explicitly configured.
<!-- opencode-bounded-orchestrator:end -->
