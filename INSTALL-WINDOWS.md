# Install on Windows

Requirements: Python 3.11+ for the browser launcher, Python 3.10+ for the terminal installer, and OpenCode V2 2.0.0+ to use installed agents. Python is not bundled; Git is optional for local project folders.

1. Extract the ZIP completely.
2. Double-click `launchers/Launch Bounded Orchestrator.vbs`.
3. Choose an existing local project folder.
4. In the browser, choose 1–10 available helper slots, a duty and model for each, review the changes, then install. The selected path is read-only; reopen the launcher for another project. Slots are capacity, not an automatic launch count or runtime concurrency setting. `setup.cmd` remains a guided terminal option.
5. Restart OpenCode in the repository.
6. Use `/connect` and `/models` inside OpenCode for account and model setup.

PowerShell alternative:

```powershell
py -3 scripts\install.py --target C:\path\to\repo --action install --profile balanced
```

Model and variant access depend on your provider. New variant choices remain disabled if OpenCode supplies no verified list; an existing custom choice is preserved. The installer never asks for or writes API keys. Uninstall removes only unchanged managed files and its `AGENTS.md` block. It keeps two `.gitignore` sentinels so retained runtime metadata and backups remain ignored. Reducing a roster privately backs up removed owned helper files. **Preferences → Undo last change** reverses only the last console-managed preference save, not a roster change. Native Windows double-click behavior was not exercised in this development environment.
