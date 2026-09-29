# Install on Windows

Requirements: Python 3.11+ for the browser launcher and OpenCode V2 2.0.0+; Git is optional for local project folders.

1. Extract the ZIP completely.
2. Double-click `launchers/Launch Bounded Orchestrator.vbs`.
3. Choose an existing local project folder.
4. In the browser, choose helper roles and models, review the changes, then install. `setup.cmd` remains a guided terminal option.
5. Restart OpenCode in the repository.
6. Use `/connect` and `/models` inside OpenCode for account and model setup.

PowerShell alternative:

```powershell
py -3 scripts\install.py --target C:\path\to\repo --action install --profile balanced
```

The installer never asks for or writes API keys. Uninstall removes only unchanged managed files and its `AGENTS.md` block. It keeps two `.gitignore` sentinels so retained runtime metadata and backups remain ignored.
