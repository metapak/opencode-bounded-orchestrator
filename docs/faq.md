# FAQ and troubleshooting

**Does it choose a provider?** No. Default roles inherit the current OpenCode session model. Use `/connect` and `/models`.

**Does Quota saver guarantee fewer tokens?** No. It sets smaller step budgets. Actual usage depends on the task, model, provider, and OpenCode behavior.

**Why did custom model installation fail?** Use exact `provider/model` or `provider/model#variant`. Mixed providers require the explicit gate.

**Why are existing files kept?** The installer found a conflict it does not own. Run again with replacement only after reviewing; the original is backed up.

**Why is usage unavailable?** `opencode stats --json` was missing, failed, timed out, or returned unsupported JSON.

**Can a child create more agents?** No. Every child denies `subagent`.
