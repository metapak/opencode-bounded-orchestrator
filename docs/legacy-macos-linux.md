> Advanced compatibility only / Yalnız ileri düzey uyumluluk. These instructions describe the older provider-specific console, not the unified Ustam app. / Bu yönergeler birleşik Ustam uygulamasını değil eski sağlayıcı konsolunu anlatır.

# Install on macOS or Linux

## Mac: four steps

Have OpenCode V2 2.0.0+ and [Python 3.11 or newer](https://www.python.org/downloads/) installed. Python is not included.

1. **Download:** [Get the current ZIP](https://github.com/metapak/ustam-opencode-orchestrator/archive/refs/heads/main.zip) and open the extracted folder.
2. **Open:** Open `launchers` and double-click **Ustam.app**.
3. **Choose a project:** Pick the folder where you use OpenCode.
4. **Install:** In the browser, keep the suggested team or change it. Click **Review setup**, check the file list, then **Install and save**. Restart OpenCode in that project.

For later changes, reopen the app and **Save changes**; no uninstall is needed. An already-open OpenCode session may need to be reopened before it uses them. If macOS blocks the unsigned app, inspect it first, then Control-click and choose **Open**. Keep the app inside the extracted folder beside the launcher script and setup files. If macOS asks for the setup package, its first dialog explains which folder to choose: the outer folder extracted from the ZIP whose name starts with `ustam-opencode-orchestrator`. The short picker opens in Downloads; the folder contains `launchers` and `scripts`. Choose **Try again** after a wrong selection. The second dialog asks for the separate Git project where you use OpenCode; settings go there before setup continues in the browser. Dialogs use Turkish or English based on your primary system language. If the browser cannot open, an alert shows the full local address to open manually.

## Linux: the same four steps

Have OpenCode V2 2.0.0+ and Python 3.11 or newer installed. There is no double-click launcher or folder picker for Linux in this package.

1. **Download:** Use the same [current ZIP](https://github.com/metapak/ustam-opencode-orchestrator/archive/refs/heads/main.zip) and open the extracted folder.
2. **Open:** Open a terminal in that folder.
3. **Choose a project:** Run `python3 scripts/dashboard.py /absolute/path/to/your-project`. Put your project's path in the command; it opens the same browser page.
4. **Install:** Keep the suggested team or change it. Click **Review setup**, check the file list, then **Install and save**. Restart OpenCode in that project. Later, repeat the command and **Save changes**; no uninstall is needed.

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
