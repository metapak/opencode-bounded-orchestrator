# Install on macOS or Linux

## macOS: graphical setup

1. [Download the current main ZIP](https://github.com/metapak/opencode-bounded-orchestrator/archive/refs/heads/main.zip) and extract the whole folder. This current repository snapshot contains the app launcher; an older v0.1.0 release ZIP may not.
2. Install [Python 3.11 or newer](https://www.python.org/downloads/) if it is not already present. Python is not bundled. You also need OpenCode V2 2.0.0+ to use the installed agents.
3. Double-click `launchers/Bounded Orchestrator.app`. In the macOS folder picker, choose your existing project folder (your Git project when working in a repository). The project path is read-only in the browser; reopen the app to choose another project.
4. In the local browser page, choose the available helper slots, their duties and models, and a working style. Review the proposed changes, then select **Install and save**. Restart OpenCode in that project.

The browser binds only to `127.0.0.1`. The chosen number of helpers is available capacity, not a simultaneous-worker limit or automatic launch count. Model and variant availability depends on your OpenCode provider; a new variant choice remains unavailable without a verified list. The installer never asks for API keys. If Gatekeeper blocks this unsigned community launcher, inspect it first, then use **Control-click → Open**. Actual Finder double-click behavior was not exercised in this development environment.

## Optional Linux and command-line path

Linux has no bundled double-click launcher. From the extracted current main ZIP, use Python 3.10+ to open the same browser setup:

```bash
python3 scripts/dashboard.py /path/to/project
```

The guided `setup.command` and direct installer remain optional macOS/Linux terminal alternatives. To preview and install from the terminal:

```bash
python3 scripts/install.py --target /path/to/project --action dry-run --profile balanced
python3 scripts/install.py --target /path/to/project --action install --profile balanced
```

To uninstall unchanged managed files:

```bash
python3 scripts/install.py --target /path/to/project --action uninstall
```

Uninstall preserves user-modified and unrelated files and leaves private runtime `.gitignore` sentinels. Roster reduction separately backs up removed owned helper files. **Preferences → Undo last change** reverses only the last console-managed preference save, not installation or roster reduction. Configure accounts and available models inside OpenCode with `/connect` and `/models`.
