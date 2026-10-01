[English](README.md) · [Türkçe](README.tr.md)

![A warm burgundy orchestra stage with a conductor and distinct helper musicians](docs/assets/cover-en.svg)

# OpenCode Bounded Orchestrator

[![CI](https://github.com/metapak/opencode-bounded-orchestrator/actions/workflows/ci.yml/badge.svg)](https://github.com/metapak/opencode-bounded-orchestrator/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

A local, bilingual setup and usage console for a bounded **OpenCode V2** team. You describe the outcome; a primary conductor plans and delegates scoped work to helpers. The conductor does not research, edit, build, test, or review source itself.

> Unofficial community project; not affiliated with or endorsed by OpenCode or its maintainers.

## Install in four steps

Have OpenCode V2 2.0.0+ and [Python 3.11 or newer](https://www.python.org/downloads/) installed first. Python is **not included** in this download.

1. **Download:** [Get the current ZIP](https://github.com/metapak/opencode-bounded-orchestrator/archive/refs/heads/main.zip) and open the extracted folder.
2. **Open:** On Mac, open `launchers` and double-click **Bounded Orchestrator.app**. On Windows, double-click **Launch Bounded Orchestrator.vbs** in the same folder. On Linux, use the short command below.
3. **Choose a project:** On Mac or Windows, pick the folder where you use OpenCode. On Linux, the command includes that folder instead.
4. **Install:** In the browser, keep the suggested team or change it. Review the choices, then click **Install and save**. Restart OpenCode in that project.

Keep the Mac app inside the extracted folder. If macOS asks for the setup package, its first dialog explains which folder to choose: the outer folder extracted from the ZIP whose name starts with `opencode-bounded-orchestrator`. The short picker opens in Downloads; the folder contains `launchers` and `scripts`. Choose **Try again** after a wrong selection. The second dialog asks for the separate Git project where you use OpenCode; settings go there before setup continues in the browser. Dialogs use Turkish or English based on your primary system language. If the browser cannot open, the launcher shows the full local address to open manually.

<details>
<summary>Linux: open the same setup page</summary>

Linux has no double-click launcher or folder picker in this package. Open a terminal in the extracted folder, then run this with your project's path:

```bash
python3 scripts/dashboard.py /absolute/path/to/your-project
```

</details>

To change the team later, open the launcher again (or repeat the Linux command) and **Save** the new choices. It updates the project settings without uninstalling. An already-open OpenCode session may need to be reopened before it uses the changes. If setup does not open, see the [Mac/Linux](INSTALL-MACOS-LINUX.md) or [Windows](INSTALL-WINDOWS.md) guide.

## Watch the 8-second preview

<p><img src="docs/assets/bounded-orchestrator-intro-8s.gif" alt="Animated sample Codex orchestra with conductor and four helpers" width="480"></p>

Silent, with Turkish titles. This shared-family preview uses sample Codex UI, not an OpenCode recording or live data. [Download the original MP4](https://raw.githubusercontent.com/metapak/opencode-bounded-orchestrator/main/docs/assets/bounded-orchestrator-intro-8s.mp4).

![Illustrative demo of the OpenCode Usage orchestra with a conductor and three helpers](docs/assets/console-en.png)

*Sample-data Usage screen. The shown sessions, helpers, models, and token counts are examples, not your account or live usage.*

## How the team works

The installed primary `owner` has a deny-by-default tool policy with only its bounded-orchestrator skill, user questions, and the selected helper subagents allowed. Its instructions limit it to conversation, planning, delegation, and concise worker reports. Helper agents deny further subagent delegation; only an `implementer`-based helper writes implementation in an assigned scope. The default team uses one suitable helper; parallel work needs independent scopes and a reason. These are OpenCode configuration and instructions, not a claim that this package controls every external runtime behavior.

The browser shows a *planned* team in Setup and *observed* sessions in Usage. They are different: four characters in a sample orchestra do not mean a four-agent limit or four currently running agents. Usage can show a conductor and linked child-session helpers when OpenCode's sanitized exports provide stable session relationships. Each observed character has its own duty illustration and visible model/variant information; missing values are marked unavailable, and model or role alone never becomes an agent identity. Select the conductor to play the baton and notes; it loops until you click elsewhere. Enter and Space also activate the button. There is no automatic animation or separate Animate control.

Usage charts use exact counters from up to 12 recent sanitized session exports, with unknown and partial coverage shown explicitly. `opencode stats` is display data and may be rounded; it is not silently merged into exact charts. A working style breakdown is an estimate only when a session can be matched conservatively to local settings history. No cost, quota, savings, subscription balance, or live-agent activity is inferred. DEMO fixtures are labeled as examples, not account usage. See [usage and local evaluation](docs/usage-and-local-eval.md).

## Preferences and safe changes

Working styles set finite OpenCode `steps` budgets, not token ceilings. Economy and Quota saver allow fewer steps and can stop earlier; Quality allows more steps. They do not promise token savings or alter reasoning effort automatically. The model picker uses the selected project's `opencode models` list when available; offline examples are visibly unverified. **Refresh model list** asks OpenCode to refresh only when clicked. No credentials or chat bodies are shown in the console.

Setup changes are previewed, then written to the chosen project with an ownership manifest and private backups. Reducing a roster removes only previously owned, unchanged helper files; removed files are backed up. **Preferences → Undo last change** reverses only the last console-managed preference save while preserving unrelated settings. It does not undo a roster install or reduction. Modified or conflicting managed files require a safe resolution rather than silent overwrite. Private runtime state stays ignored by Git; uninstall preserves unrelated and changed files. See [profiles](docs/profiles.md), [architecture](docs/architecture.md), [task ledger](docs/task-ledger.md), and [FAQ](docs/faq.md).

## Development and limits

Installer and repository tests run in GitHub Actions on Ubuntu, macOS, and Windows. This development environment did not have the OpenCode CLI or a real provider session, and native Finder/Windows double-click behavior was not exercised here. Browser flows were checked with sanitized fixtures; model access, variants, and live export shapes still depend on your installation. The documented OpenCode V2 config and permission contracts underpin the generated files, but the package cannot guarantee model availability or a numeric worker concurrency cap.

See the [roadmap](docs/roadmap.md), [contribution guide](CONTRIBUTING.md), [security policy](SECURITY.md), [changelog](CHANGELOG.md), and [release notes](docs/release-v0.1.0.md). Apache-2.0 licensed; attribution is in [NOTICE](NOTICE) and [provenance](docs/provenance.md).
