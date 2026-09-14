#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
clear 2>/dev/null || true
printf '%s\n' "============================================================" " OpenCode Bounded Orchestrator 0.1.0" " Guided setup / macOS and Linux" "============================================================" "" "OpenCode V2 roles inherit the current session model by default." "Use /connect and /models in OpenCode to configure providers." ""
python3 "$HERE/scripts/install.py"
status=$?
printf '\nInstaller exited with status %s.\nPress Return to close.\n' "$status"
read answer || true
exit "$status"
