#!/usr/bin/env python3
"""Live-load the repository with OpenCode 2.0.3 and verify bounded agents."""

from __future__ import annotations

import argparse, json, os, subprocess, sys
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[1]
ROLES={"owner","fast-lookup","explorer","researcher","implementer","verifier","failure-analyst","qa-operator","reviewer","advisor"}


class SmokeError(RuntimeError): pass


def parse_json(text: str, label: str) -> Any:
    try: return json.loads(text)
    except json.JSONDecodeError as exc: raise SmokeError(f"{label} did not return JSON: {exc}") from exc


def project_config(payload: Any) -> dict:
    if isinstance(payload,dict) and isinstance(payload.get("agents"),dict): return payload
    if isinstance(payload,list):
        matches=[item.get("info") for item in payload if isinstance(item,dict) and item.get("type")=="document" and str(item.get("path","")).endswith("/.opencode/opencode.jsonc") and isinstance(item.get("info"),dict)]
        if len(matches)==1: return matches[0]
    raise SmokeError("debug config did not expose exactly one project opencode.jsonc document")


def effective(rules: list[dict], action: str, resource: str) -> str | None:
    result=None
    for rule in rules:
        if rule.get("action") not in {"*",action}: continue
        target=rule.get("resource")
        if target=="*" or target==resource or (isinstance(target,str) and target.endswith("*") and resource.startswith(target[:-1])): result=rule.get("effect")
    return result


def verify(config_payload: Any, agents_payload: Any) -> dict:
    config=project_config(config_payload)
    if config.get("default_agent")!="owner" or set(config.get("agents",{}))!=ROLES: raise SmokeError("debug config lost the exact ten-role set or default owner")
    if not isinstance(agents_payload,list): raise SmokeError("debug agents must return a JSON list")
    indexed={item.get("id"):item for item in agents_payload if isinstance(item,dict) and item.get("id") in ROLES}
    if set(indexed)!=ROLES: raise SmokeError(f"debug agents is missing bounded roles: {sorted(ROLES-set(indexed))}")
    for role,item in indexed.items():
        rules=item.get("permissions",[])
        if effective(rules,"edit","src/file.py") != ("allow" if role=="implementer" else "deny"): raise SmokeError(f"{role} has incorrect effective edit permission")
        if role!="owner" and effective(rules,"subagent","implementer")!="deny": raise SmokeError(f"{role} can delegate")
    owner=indexed["owner"]["permissions"]
    for role in ROLES-{"owner"}:
        if effective(owner,"subagent",role)!="allow": raise SmokeError(f"owner cannot delegate to {role}")
    if effective(owner,"subagent","unlisted")!="deny": raise SmokeError("owner can delegate to an unlisted agent")
    for role in ("fast-lookup","explorer","researcher","failure-analyst","reviewer","advisor"):
        if effective(indexed[role]["permissions"],"shell","anything")!="deny": raise SmokeError(f"{role} can use shell")
    for role in ("verifier","qa-operator"):
        rules=indexed[role]["permissions"]
        if effective(rules,"shell","rm file")!="ask" or effective(rules,"shell","git status --short")!="allow": raise SmokeError(f"{role} shell ordering is incorrect")
    return {"status":"pass","default_agent":"owner","configured_roles":sorted(ROLES),"loaded_roles":sorted(indexed)}


def run(prefix: list[str]) -> dict:
    outputs=[]
    for command in (("debug","config"),("debug","agents")):
        result=subprocess.run([*prefix,*command],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False,timeout=120)
        if result.returncode: raise SmokeError(f"opencode {' '.join(command)} failed ({result.returncode}): {result.stderr.strip()[:500]}")
        outputs.append(parse_json(result.stdout," ".join(command)))
    return verify(*outputs)


def command_prefix(command: str, npm_package: str|None, platform_name: str=os.name) -> list[str]:
    if not npm_package: return [command]
    npm_command="npm.cmd" if platform_name=="nt" else "npm"
    return [npm_command,"exec","--yes",f"--package={npm_package}","--","opencode"]


def main(argv: list[str]|None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--command",default="opencode"); parser.add_argument("--npm-package"); args=parser.parse_args(argv)
    prefix=command_prefix(args.command,args.npm_package)
    try: report=run(prefix)
    except (SmokeError,OSError,subprocess.TimeoutExpired) as exc: print(f"OPENCODE SMOKE FAILED: {exc}",file=sys.stderr); return 1
    print(json.dumps(report,indent=2,sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
