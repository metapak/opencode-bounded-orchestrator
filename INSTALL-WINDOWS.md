# Install on Windows

Requirements: Git, Python 3.10+, and OpenCode V2 2.0.0+.

1. Extract the ZIP completely.
2. Double-click `setup.cmd`.
3. Paste the target Git repository path.
4. Choose a profile and review conflict prompts.
5. Restart OpenCode in the repository.
6. Use `/connect` and `/models` inside OpenCode for account and model setup.

PowerShell alternative:

```powershell
py -3 scripts\install.py --target C:\path\to\repo --action install --profile balanced
```

The installer never asks for or writes API keys. Uninstall removes only unchanged managed files and its `AGENTS.md` block.
