# FAQ and troubleshooting

**Does it choose a provider?** No. Default roles inherit the current OpenCode session model. Use `/connect` and `/models`.

**Does Quota saver guarantee fewer tokens?** No. It sets smaller step budgets. Actual usage depends on the task, model, provider, and OpenCode behavior.

**Why did custom model installation fail?** Use exact `provider/model` or `provider/model#variant`. Mixed providers require the explicit gate.

**Why are existing files kept?** The installer found a conflict it does not own. Run again with replacement only after reviewing; the original is backed up.

**Why is usage unavailable?** The OpenCode CLI is missing, a supported `opencode stats`/sanitized export command failed or timed out, or its output could not be recognized. `stats --json` is not a supported option. No unavailable counter is filled with an invented zero.

**Why can I choose ten helpers but see fewer musicians?** Setup defines available named slots. Usage shows only linked sessions observed in the latest exported window. Neither number is a numeric runtime concurrency limit.

**Why can I not choose a new variant/effort?** The browser has no verified choices from this OpenCode provider. An existing saved custom variant is preserved; the package does not invent an effort setting.

**Can a child create more agents?** The installed OpenCode child permissions deny `subagent`. The primary owner is deny-by-default and may delegate only to the selected helper allowlist.
