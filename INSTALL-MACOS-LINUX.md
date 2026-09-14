# Install on macOS or Linux

Requirements: Git, Python 3.10+, and OpenCode V2 2.0.0+.

On macOS, extract the archive completely and open `setup.command`. If Gatekeeper blocks the unsigned community script, inspect it first, then use **Control-click → Open** or run `python3 scripts/install.py` from Terminal.

On Linux:

```bash
python3 scripts/install.py --target /path/to/repo --action dry-run --profile balanced
python3 scripts/install.py --target /path/to/repo --action install --profile balanced
```

Restart OpenCode in the target repository. Configure accounts with `/connect` and choose a model with `/models`. The installer never asks for or writes API keys.

To uninstall unchanged managed files:

```bash
python3 scripts/install.py --target /path/to/repo --action uninstall
```

Uninstall deliberately keeps the runtime and candidate `.gitignore` sentinels. This keeps any retained backups, ledger runs, evaluations, and candidate metadata out of Git status.
