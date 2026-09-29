# Install on Windows

## Graphical setup

1. [Download the current main ZIP](https://github.com/metapak/opencode-bounded-orchestrator/archive/refs/heads/main.zip) and extract the whole folder. This current repository snapshot contains the launcher; an older v0.1.0 release ZIP may not.
2. Install [Python 3.11 or newer](https://www.python.org/downloads/) if needed. Python is not bundled. OpenCode V2 2.0.0+ is needed to use the installed agents.
3. Double-click `launchers/Launch Bounded Orchestrator.vbs` and choose your existing project folder in the Windows picker (your Git project when working in a repository). The folder path is read-only in the browser; reopen the launcher to choose another project.
4. In the local browser page, choose available helper slots, their duties and models, and a working style. Review the proposed changes, select **Install and save**, then restart OpenCode in the project.

The page binds only to `127.0.0.1`. The selected helper count is capacity, not a simultaneous-worker limit or automatic launch count. Models and variants depend on provider access; a new variant choice stays unavailable without a verified list. The installer never asks for API keys. Actual Windows double-click behavior was not exercised in this development environment.

## Optional command-line path

The guided `setup.cmd` and direct installer remain optional terminal alternatives. Python 3.10+ supports the terminal installer:

```powershell
py -3 scripts\install.py --target C:\path\to\project --action dry-run --profile balanced
py -3 scripts\install.py --target C:\path\to\project --action install --profile balanced
```

Uninstall removes only unchanged managed files and its own `AGENTS.md` block. It leaves private runtime `.gitignore` sentinels. Roster reduction backs up removed owned helper files. **Preferences → Undo last change** reverses only the last console-managed preference save, not installation or roster reduction. Configure accounts and available models inside OpenCode with `/connect` and `/models`.
