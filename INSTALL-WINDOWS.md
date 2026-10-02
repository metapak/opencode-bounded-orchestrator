# Install on Windows

## Windows: four steps

Have OpenCode V2 2.0.0+ and [Python 3.11 or newer](https://www.python.org/downloads/) installed. Python is not included.

1. **Download:** [Get the current ZIP](https://github.com/metapak/ustam-opencode-orchestrator/archive/refs/heads/main.zip) and open the extracted folder.
2. **Open:** Open `launchers` and double-click **Launch Ustam.vbs**.
3. **Choose a project:** Pick the folder where you use OpenCode.
4. **Install:** In the browser, keep the suggested team or change it. Review the choices, then click **Install and save**. Restart OpenCode in that project.

For later changes, reopen the launcher and **Save changes**; no uninstall is needed. An already-open OpenCode session may need to be reopened before it uses them. Double-click behavior was not tested on Windows in this development environment.

## Optional command-line path

The guided `setup.cmd` and direct installer remain optional terminal alternatives. Python 3.10+ supports the terminal installer:

```powershell
py -3 scripts\install.py --target C:\path\to\project --action dry-run --profile balanced
py -3 scripts\install.py --target C:\path\to\project --action install --profile balanced
```

Uninstall removes only unchanged managed files and its own `AGENTS.md` block. It leaves private runtime `.gitignore` sentinels. Roster reduction backs up removed owned helper files. **Preferences → Undo last change** reverses only the last console-managed preference save, not installation or roster reduction. Configure accounts and available models inside OpenCode with `/connect` and `/models`.
