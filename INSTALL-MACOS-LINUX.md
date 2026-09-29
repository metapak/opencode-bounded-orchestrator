# Install on macOS or Linux

Requirements: Python 3.11+ for the browser launcher, Python 3.10+ for the terminal installer, and OpenCode V2 2.0.0+ to use the installed agents. Git is useful for repository work but an existing non-Git project folder can be selected.

On macOS, extract the archive completely and open `launchers/Bounded Orchestrator.app` to choose a project and install in the browser. Python is not bundled. The chosen project path is read-only in the page; reopen the app to choose another folder. Select 1–10 available helper slots, review the changes, and install. The count does not set runtime concurrency or automatically launch helpers. The older `setup.command` guided terminal installer is also available. If Gatekeeper blocks the unsigned community script, inspect it first, then use **Control-click → Open** or run `python3 scripts/install.py` from Terminal. Native Finder double-click behavior was not exercised in this development environment.

On Linux:

```bash
python3 scripts/dashboard.py /path/to/repo
python3 scripts/install.py --target /path/to/repo --action dry-run --profile balanced
python3 scripts/install.py --target /path/to/repo --action install --profile balanced
```

The first command opens the same local browser setup; the other commands are terminal alternatives. A model or variant offered in the UI is usable only if your OpenCode provider supports it. New variant choices stay unavailable without a verified provider list; saved custom choices are preserved.

Restart OpenCode in the target repository. Configure accounts with `/connect` and choose a model with `/models`. The installer never asks for or writes API keys.

To uninstall unchanged managed files:

```bash
python3 scripts/install.py --target /path/to/repo --action uninstall
```

Uninstall deliberately keeps the runtime and candidate `.gitignore` sentinels. This keeps any retained backups, ledger runs, evaluations, and candidate metadata out of Git status. Roster reduction backs up removed owned helper files privately. **Preferences → Undo last change** restores only the last console-managed preference change; it does not reverse team installation or roster reduction.
