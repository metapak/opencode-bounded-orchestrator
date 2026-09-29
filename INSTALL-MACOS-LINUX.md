# Install on macOS or Linux

## Mac: four steps

Have OpenCode V2 2.0.0+ and [Python 3.11 or newer](https://www.python.org/downloads/) installed. Python is not included.

1. **Download:** [Get the current ZIP](https://github.com/metapak/opencode-bounded-orchestrator/archive/refs/heads/main.zip) and open the extracted folder.
2. **Open:** Open `launchers` and double-click **Bounded Orchestrator.app**.
3. **Choose a project:** Pick the folder where you use OpenCode.
4. **Install:** In the browser, keep the suggested team or change it. Review the choices, then click **Install and save**. Restart OpenCode in that project.

For later changes, reopen the app and **Save changes**; no uninstall is needed. An already-open OpenCode session may need to be reopened before it uses them. If macOS blocks the unsigned app, inspect it first, then Control-click and choose **Open**. Finder double-click behavior was not tested in this development environment.

## Linux: the same four steps

Have OpenCode V2 2.0.0+ and Python 3.11 or newer installed. There is no double-click launcher or folder picker for Linux in this package.

1. **Download:** Use the same [current ZIP](https://github.com/metapak/opencode-bounded-orchestrator/archive/refs/heads/main.zip) and open the extracted folder.
2. **Open:** Open a terminal in that folder.
3. **Choose a project:** Run `python3 scripts/dashboard.py /absolute/path/to/your-project`. Put your project's path in the command; it opens the same browser page.
4. **Install:** Review the suggested team or change it, then click **Install and save**. Restart OpenCode in that project. Later, repeat the command and **Save changes**; no uninstall is needed.

## Optional command-line installer

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
