#!/usr/bin/env python3
"""Wrap verified `opencode stats --json` output without reading transcripts."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from typing import Any


class UsageError(RuntimeError):
    pass


def collect(command: str = "opencode") -> dict[str, Any]:
    executable = shutil.which(command) if "/" not in command else command
    if not executable:
        raise UsageError("OpenCode CLI was not found; usage data is unavailable.")
    try:
        result = subprocess.run(
            [executable, "stats", "--json"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UsageError(f"OpenCode stats is unavailable: {exc}") from exc
    if result.returncode:
        detail = result.stderr.strip()[:300]
        raise UsageError(f"opencode stats --json failed ({result.returncode}): {detail}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise UsageError("OpenCode stats returned invalid JSON; usage data is unavailable.") from exc
    if not isinstance(payload, (dict, list)):
        raise UsageError("OpenCode stats JSON has an unsupported shape.")
    return {
        "status": "available",
        "source": "opencode stats --json",
        "reported": payload,
        "limitations": "Values are reported by OpenCode/providers; this tool does not infer missing tokens, quota percentages, billing totals, or costs.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command", default="opencode")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = collect(args.command)
    except UsageError as exc:
        report = {"status": "unavailable", "source": "opencode stats --json", "error": str(exc)}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"OpenCode usage report unavailable: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("OpenCode usage report")
        print(json.dumps(report["reported"], indent=2, sort_keys=True))
        print(report["limitations"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
