# Contributing

Issues and focused pull requests are welcome. Explain the trigger, expected behavior, OpenCode V2 evidence, and tests. Keep provider/model claims conditional and do not add secrets, transcripts, runtime state, generated archives, or unrelated refactors.

Before opening a pull request:

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

By contributing, you agree that your contribution is licensed under Apache-2.0.
