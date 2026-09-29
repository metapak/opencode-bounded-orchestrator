# Profiles

Profiles change finite OpenCode `steps` budgets only.

- **Balanced:** daily default.
- **Quality:** larger budgets for complex work.
- **Economy:** smaller budgets for routine work.
- **Quota saver:** smallest bundled budgets; it can stop before difficult work is solved.
- **Custom:** Balanced budgets plus optional exact model selectors.

Example custom install:

```bash
python3 scripts/install.py --target . --action install --profile custom --model provider/model --role-model reviewer=provider/model#variant
```

All selected native roles must use one provider unless `--allow-mixed-providers` is explicitly supplied. A role override without `--model` has an unknown inherited default provider and is rejected unless the same explicit gate is supplied. The package does not verify whether a named model or variant exists; use OpenCode `/models`.


Runtime `steps` and model selectors are stored only in JSON config. Markdown role files retain prompts and permissions, avoiding duplicate scalar overrides. Root `--model` does not accept `#variant`; use `--role-model` for provider-supported variants. Model IDs can contain slash segments. `steps` are model-turn budgets, not token ceilings. Browser profiles are available through [the local console](local-console.md); custom keeps existing steps. No numeric parallelism setting is claimed without a verified OpenCode contract.


The browser Setup tab can create 1–10 separately named helper slots, each with a selected specialist duty and model. The count describes available slots, not a guaranteed simultaneous worker count. Existing custom `#variant` selectors are preserved; new variant choices are disabled when OpenCode does not expose a verified list. The conductor is always a coordinator and never a worker.
