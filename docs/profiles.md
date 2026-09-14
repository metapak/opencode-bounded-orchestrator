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
