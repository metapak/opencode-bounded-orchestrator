# Local console / Yerel konsol

Run with Python 3.10+ from a target project after installation:

```sh
python3 .opencode/tools/console.py configure
python3 .opencode/tools/console.py dashboard --no-browser --port 8765
```

The same console provides Turkish by default (Tercihler, Kullanım, Çalışmalar) and an English switch (Preferences, Usage, Work). The language choice is kept in local browser storage; switching languages keeps the current view and form values. `configure` and `dashboard` are launcher aliases. The default opens the browser; `--no-browser` prints a local URL with an ephemeral session token. Stop with Ctrl+C. Never share this URL. It binds only to 127.0.0.1. Host, Origin and token checks protect every write and API read. No Node/npm is needed.

From the distribution repository, set an existing project explicitly:

```sh
python3 .opencode/tools/console.py --root /path/to/project --no-browser
```

A fresh target needs the installer for agent prompts and permissions: `python3 scripts/install.py --target /path/to/project --action install --profile balanced`. The console itself edits scalar settings only; it does not install agents or grant permissions. Installed console assets are managed by the existing installer, conflict policy and uninstall manifest.

The everyday view shows a working style, a saved-versus-pending summary, and a plain confirmation before Save. Technical paths, provider/model overrides and the exact field diff are inside collapsed details. Choose project (`.opencode/opencode.json(c)`) or user (`$XDG_CONFIG_HOME/opencode/opencode.json(c)`, default `~/.config/opencode`). Only the selected target is written after **Farkı önizle → Kaydet**. Existing .json is used when no .jsonc exists; ambiguous pairs, symlinks, malformed config and stale previews are rejected. Profiles set finite `steps`; custom keeps existing steps. Role selectors use `provider/model#variant`; root model uses `provider/model` because V2 does not retain a root variant. Provider/model availability is not inferred. Mixed or unknown inherited providers require the explicit checkbox. User settings may be overridden by project settings or the current session.

Runtime scalar preferences live in JSON. New distributed Markdown agents contain prompts and permissions without duplicate model/steps settings. Existing Markdown model overrides or conflicting steps are rejected with a manual-merge instruction. The local effective view reads documented user/ancestor project config locations and Markdown scalar overrides; environment, remote config, provider catalog and session selection are outside this view. Confirm the running session using OpenCode debug config/agent. Parallelism has no verified numeric V2 setting; no fabricated parallelism knob is exposed. Brief/context/retry/report rules are prompt preferences, never enforced token ceilings.

The exact preview lists before/after values of only changed managed fields. JSONC edits preserve unrelated bytes and comments, including credentials. Credentials, arbitrary config, chat bodies and session titles are never returned to the browser or logs. Before creating backups or state, even on an uninstalled target, the console creates the reserved runtime `.gitignore` sentinel (`*` and `!.gitignore`). A changed existing sentinel is preserved and Save is refused until it is restored; no private backup is written. Backups and console state use restrictive files beneath `.opencode/.bounded-orchestrator` for project settings or the user config's `.bounded-orchestrator` directory. Existing installer ownership hashes are updated when changing its owned config, so uninstall respects the save. If the owned file changed outside the installer, explicit backup/replace consent is required. **Son konsol kaydını geri al** restores only the last console-managed fields, preserves unrelated later edits, and refuses changes to saved fields made elsewhere. Removing newly introduced values may leave harmless empty parent objects. Backups are retained; normal installer runtime excludes keep them out of releases.

Usage is observed, never a quota/billing estimate. Current official `stats` has **no JSON output flag**. The collector reads recognized display rows from `opencode stats`, supports `--days` (0=today) and `--project` (empty=current), and marks K/M counts as rounded. Unknown layouts, missing CLI, failures and timeouts are unavailable. Display precision is not recovered. Total input, output, cache read/write, sessions and messages are shown only when present. A total across cache/input/output is intentionally omitted because their accounting semantics differ. Stats does not expose thread records.

For a real scoped session, enter `ses_…` in Çalışmalar / Work; the collector runs `opencode export SESSION --sanitize` and retains only token counters and safe session/model/provider/agent identifiers. The browser can filter these real records by model and displays observed message dates when present in the sanitized export; missing dates are marked unavailable. No transcript content is displayed or logged. Missing counters stay unavailable. A fixture can exercise the UI without a CLI and is visibly labeled **DEMO fixture (not live usage)**:

```sh
python3 .opencode/tools/console.py --root /path/to/test-project --fixture tests/fixtures/opencode-export.json --no-browser
python3 .opencode/tools/usage_report.py --session ses_EXPLICIT --json
```

Do not treat fixture values as your usage. CLI absence was verified in development; no real OpenCode session was available for runtime validation.

Verified official contracts (2026-09-29):

- [V2 config locations and merge rules](https://opencode.ai/v2/docs/config)
- [V2 agents, model variants and steps](https://opencode.ai/v2/docs/agents)
- [Current stats command source](https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/cli/cmd/stats.ts)
- [Current sanitized export command source](https://github.com/anomalyco/opencode/blob/dev/packages/opencode/src/cli/cmd/export.ts)
