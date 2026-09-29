#!/usr/bin/env python3
"""Safely install OpenCode Bounded Orchestrator into a repository."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(".opencode/.bounded-orchestrator/install.json")
BACKUPS = Path(".opencode/.bounded-orchestrator/backups")
START = "<!-- opencode-bounded-orchestrator:start -->"
END = "<!-- opencode-bounded-orchestrator:end -->"
ROLES = ("owner", "fast-lookup", "explorer", "researcher", "implementer", "verifier", "failure-analyst", "qa-operator", "reviewer", "advisor")
TEAM_ROLES = ROLES[1:]
SLOT = re.compile(r"\.opencode/agents/helper-(?:0[1-9]|10)\.md\Z")
DUTY = re.compile(r"[A-Za-z0-9À-ž _.,:;!?()/-]{0,80}\Z")
SELECTOR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._/-]*(?:#[A-Za-z0-9][A-Za-z0-9._-]*)?$")
PROFILES = {
    "balanced": {"owner":36,"fast-lookup":10,"explorer":22,"researcher":22,"implementer":34,"verifier":20,"failure-analyst":22,"qa-operator":20,"reviewer":22,"advisor":24},
    "quality": {"owner":56,"fast-lookup":16,"explorer":34,"researcher":34,"implementer":52,"verifier":32,"failure-analyst":34,"qa-operator":32,"reviewer":36,"advisor":40},
    "economy": {"owner":24,"fast-lookup":7,"explorer":14,"researcher":14,"implementer":22,"verifier":13,"failure-analyst":14,"qa-operator":13,"reviewer":14,"advisor":16},
    "quota-saver": {"owner":18,"fast-lookup":5,"explorer":10,"researcher":10,"implementer":16,"verifier":9,"failure-analyst":10,"qa-operator":9,"reviewer":10,"advisor":12},
}
MANAGED = [Path(".opencode/opencode.jsonc"), Path(".opencode/bounded-orchestrator.eval.example.json"), Path(".opencode/.candidate/.gitignore"), Path(".opencode/.bounded-orchestrator/.gitignore")]
MANAGED += [Path(f".opencode/agents/{role}.md") for role in ROLES]
MANAGED += [Path(".opencode/tools") / name for name in ("candidate.py","ledger.py","usage_report.py","local_eval.py","console.py","team_editor.py","console.html","console.css","console.js","orchestra-actors.svg")]
MANAGED += [Path(".opencode/skills/bounded-orchestrator/SKILL.md"), Path(".opencode/skills/bounded-orchestrator/references/task-contract.md"), Path(".opencode/skills/bounded-orchestrator/references/review-protocol.md"), Path(".opencode/skills/bounded-orchestrator/references/escalation.md")]
ALLOWED_MANIFEST_FILES={path.as_posix() for path in MANAGED}
IGNORE_SENTINELS={Path(".opencode/.candidate/.gitignore"),Path(".opencode/.bounded-orchestrator/.gitignore")}


class InstallError(RuntimeError): pass


def ensure_safe_parent(target: Path, relative: Path) -> None:
    current = target
    for part in relative.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise InstallError(f"Refusing symlinked parent path: {current.relative_to(target)}")
        if current.exists() and not current.is_dir():
            raise InstallError(f"Refusing non-directory parent path: {current.relative_to(target)}")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()


def atomic_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists(): tmp.unlink()


def load_manifest(target: Path) -> dict[str, Any]:
    ensure_safe_parent(target, MANIFEST)
    path = target / MANIFEST
    if not path.exists(): return {"schema":1,"files":{},"agents_block":False}
    try: data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise InstallError(f"Cannot read manifest: {exc}") from exc
    if data.get("schema") != 1 or not isinstance(data.get("files"), dict): raise InstallError("Unsupported install manifest")
    if any(name not in ALLOWED_MANIFEST_FILES and not SLOT.fullmatch(name) for name in data["files"]): raise InstallError("Install manifest contains an unmanaged path")
    validate_team(data.get("team",[]))
    if any(not isinstance(meta,dict) or not re.fullmatch(r"[0-9a-f]{64}",str(meta.get("sha256",""))) for meta in data["files"].values()): raise InstallError("Install manifest contains an invalid checksum")
    return data


def selector(value: str) -> str:
    if not SELECTOR.fullmatch(value): raise InstallError(f"Invalid model selector {value!r}; expected provider/model or provider/model#variant")
    return value


def provider(value: str) -> str: return value.split("/", 1)[0].lower()


def validate_team(team: object) -> list[dict[str,str]]:
    if not isinstance(team,list) or len(team)>10: raise InstallError("Choose up to ten helper slots.")
    clean=[]
    for item in team:
        if not isinstance(item,dict) or set(item)-{"role","model","duty"}: raise InstallError("Invalid helper slot.")
        role=item.get("role"); model=item.get("model",""); duty=item.get("duty","")
        if role not in TEAM_ROLES or not isinstance(model,str) or (model and not SELECTOR.fullmatch(model)) or not isinstance(duty,str) or not DUTY.fullmatch(duty): raise InstallError("Invalid helper role, model, or duty.")
        clean.append({"role":role,"model":model,"duty":duty.strip()})
    return clean


def slot_name(index: int) -> str: return f"helper-{index:02d}"


def configured_slot(index: int, item: dict[str,str]) -> bytes:
    role=item["role"]
    base=(ROOT/f".opencode/agents/{role}.md").read_text(encoding="utf-8")
    if item["duty"]:
        base+=f"\nAssigned duty for this helper slot: {item['duty']}\n"
    return base.replace("description: ",f"description: Helper {index:02d} · ",1).encode("utf-8")


def configured_template(profile: str, default_model: str | None, role_models: dict[str,str], allow_mixed: bool, team: list[dict[str,str]] | None = None) -> bytes:
    team=validate_team(team or [])
    if profile != "custom" and (default_model or role_models) and not team:
        raise InstallError("Model selectors are available only with the custom profile unless a team is selected.")
    text = (ROOT / ".opencode/opencode.jsonc").read_text(encoding="utf-8")
    config = json.loads(text)
    steps = PROFILES["balanced"] if profile == "custom" else PROFILES[profile]
    for role in ROLES: config["agents"][role]["steps"] = steps[role]
    selectors = []
    if default_model:
        default_model = selector(default_model)
        if "#" in default_model: raise InstallError("Root model does not retain a #variant in OpenCode V2; use a role selector for variants.")
        config["model"] = default_model; selectors.append(default_model)
    for role, model in role_models.items():
        if role not in ROLES: raise InstallError(f"Unknown role in --role-model: {role}")
        model = selector(model); config["agents"][role]["model"] = model; selectors.append(model)
    if team:
        owner=config["agents"]["owner"]
        owner["permissions"]=[owner["permissions"][0],owner["permissions"][1],*[{"action":"subagent","resource":slot_name(index),"effect":"allow"} for index in range(1,len(team)+1)],*owner["permissions"][-2:]]
        for index,item in enumerate(team,1):
            slot=slot_name(index); role=item["role"]
            agent=copy.deepcopy(config["agents"][role]); agent["steps"]=steps[role]
            agent["description"]=f"Helper {index:02d}: {item['duty'] or role}"
            if item["model"]: agent["model"]=item["model"]; selectors.append(item["model"])
            config["agents"][slot]=agent
    if (role_models or any(item["model"] for item in team)) and not default_model and not allow_mixed:
        raise InstallError("Role-only model overrides have an unknown inherited default provider; supply --model or explicitly pass --allow-mixed-providers.")
    providers = {provider(item) for item in selectors}
    if len(providers) > 1 and not allow_mixed:
        raise InstallError("Mixed providers require --allow-mixed-providers and explicit user confirmation.")
    return (json.dumps(config, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def configured_agent(role: str, profile: str, role_models: dict[str,str], team: list[dict[str,str]] | None = None) -> bytes:
    # Runtime scalar settings live in JSON; Markdown holds role prompts/permissions.
    text=(ROOT/f".opencode/agents/{role}.md").read_text(encoding="utf-8")
    if role=="owner" and team:
        start=text.index("permissions:"); end=text.index("---",start)
        rules='permissions:\n  - { action: "*", resource: "*", effect: deny }\n  - { action: subagent, resource: "*", effect: deny }\n'
        rules+=''.join(f'  - {{ action: subagent, resource: {slot_name(index)}, effect: allow }}\n' for index in range(1,len(team)+1))
        rules+='  - { action: skill, resource: bounded-orchestrator, effect: allow }\n  - { action: question, resource: "*", effect: allow }\n'
        text=text[:start]+rules+text[end:]
    return text.encode("utf-8")


def assert_private_backups(target: Path) -> None:
    root=target/BACKUPS
    ensure_safe_parent(target,BACKUPS/"preflight"/"check")
    if root.is_symlink() or (root.exists() and not root.is_dir()): raise InstallError("Unsafe backup directory")
    if root.exists() and any(path.is_symlink() for path in root.rglob("*")):
        raise InstallError("Symlink inside private backups refused")


def backup(target: Path, relative: Path) -> Path:
    assert_private_backups(target)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = target / BACKUPS / stamp / relative
    suffix = 1
    while destination.exists() or destination.is_symlink():
        if destination.is_symlink(): raise InstallError("Symlinked backup destination refused")
        destination = destination.with_name(f"{destination.name}.{suffix}"); suffix += 1
    ensure_safe_parent(target,destination.relative_to(target))
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    shutil.copy2(target / relative, destination)
    try: os.chmod(destination,0o600)
    except OSError: pass
    return destination


def replace_block(existing: str, block: str) -> str:
    if START in existing or END in existing:
        if existing.count(START) != 1 or existing.count(END) != 1 or existing.index(START) > existing.index(END): raise InstallError("AGENTS.md has malformed managed markers")
        before = existing[:existing.index(START)].rstrip(); after = existing[existing.index(END)+len(END):].lstrip("\n")
        return ((before + "\n\n") if before else "") + block.strip() + "\n" + (("\n" + after) if after else "")
    return existing.rstrip() + ("\n\n" if existing.strip() else "") + block.strip() + "\n"


def install(target: Path, profile: str, replace: bool, dry_run: bool, default_model: str | None, role_models: dict[str,str], allow_mixed: bool, team: list[dict[str,str]] | None = None) -> list[str]:
    if not target.is_dir() or target.is_symlink(): raise InstallError("Target must be an existing real directory")
    manifest = load_manifest(target); actions=[]; files=dict(manifest["files"])
    team=validate_team(manifest.get("team",[]) if team is None else team)
    config_data = configured_template(profile, default_model, role_models, allow_mixed, team)
    agents = target / "AGENTS.md"
    if agents.is_symlink() or (agents.exists() and not agents.is_file()): raise InstallError("Refusing unsafe AGENTS.md path")
    block=(ROOT/"templates/AGENTS.block.md").read_text(encoding="utf-8")
    existing=agents.read_text(encoding="utf-8") if agents.exists() else ""; updated=replace_block(existing, block)
    sentinel_relative=Path('.opencode/.bounded-orchestrator/.gitignore');sentinel=target/sentinel_relative
    ensure_safe_parent(target,sentinel_relative)
    if sentinel.exists() and (sentinel.is_symlink() or not sentinel.is_file() or sentinel.read_text(encoding='utf-8')!='*\n!.gitignore\n'):
        raise InstallError('Private runtime ignore sentinel changed; refusing backup or install.')
    assert_private_backups(target)
    dynamic=[Path(f".opencode/agents/{slot_name(index)}.md") for index in range(1,len(team)+1)]
    removals=[]; writes=[]
    # Plan and preflight every dynamic and managed path before touching any file.
    for name in list(files):
        if SLOT.fullmatch(name) and Path(name) not in dynamic:
            relative=Path(name);ensure_safe_parent(target,relative);destination=target/relative
            if destination.is_symlink() or (destination.exists() and (not destination.is_file() or digest(destination)!=files[name]['sha256'])):
                raise InstallError(f"Modified old helper slot must be resolved before replacement: {name}")
            removals.append((relative,destination));files.pop(name);actions.append(f"REMOVE {relative}")
    for relative in [*MANAGED,*dynamic]:
        ensure_safe_parent(target,relative)
        destination=target/relative
        if relative==Path('.opencode/opencode.jsonc'): data=config_data
        elif relative in dynamic: data=configured_slot(int(relative.stem[-2:]),team[int(relative.stem[-2:])-1])
        elif relative.parent==Path('.opencode/agents'): data=configured_agent(relative.stem,profile,role_models,team)
        else: data=(ROOT/relative).read_bytes()
        wanted=hashlib.sha256(data).hexdigest()
        if destination.is_symlink() or (destination.exists() and not destination.is_file()): raise InstallError(f"Refusing unsafe path: {relative}")
        current=digest(destination) if destination.exists() else None
        if current is not None and current!=wanted:
            old_owned=files.get(relative.as_posix(),{}).get('sha256')==current
            if not old_owned and not replace:
                actions.append(f"KEEP {relative} (conflict)");continue
            actions.append(f"BACKUP {relative}")
        if current!=wanted:
            writes.append((relative,data,current is not None));actions.append(f"INSTALL {relative}")
        else: actions.append(f"UNCHANGED {relative}")
        files[relative.as_posix()]={'sha256':wanted}
    if updated!=existing: actions.append('UPDATE AGENTS.md managed block')
    if dry_run: return actions
    if not sentinel.exists():
        sentinel.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        atomic_bytes(sentinel,b'*\n!.gitignore\n')
        try: os.chmod(sentinel.parent,0o700)
        except OSError: pass
    for relative,destination in removals:
        if destination.exists():backup(target,relative);destination.unlink()
    for relative,data,needs_backup in writes:
        if needs_backup:backup(target,relative)
        atomic_bytes(target/relative,data)
    if updated!=existing:
        if agents.exists():backup(target,Path('AGENTS.md'))
        atomic_bytes(agents,updated.encode())
    payload={'schema':1,'version':(ROOT/'VERSION').read_text().strip(),'profile':profile,'files':files,'agents_block':True,'team':team}
    atomic_bytes(target/MANIFEST,(json.dumps(payload,indent=2,sort_keys=True)+'\n').encode())
    return actions


def uninstall(target: Path, dry_run: bool) -> list[str]:
    manifest=load_manifest(target);actions=[];planned=[]
    assert_private_backups(target)
    agents=target/'AGENTS.md'
    if agents.is_symlink() or (agents.exists() and not agents.is_file()): raise InstallError('Refusing unsafe AGENTS.md path')
    for name,meta in manifest['files'].items():
        relative=Path(name);path=target/relative;ensure_safe_parent(target,relative)
        if path.is_symlink() or (path.exists() and not path.is_file()): raise InstallError(f'Refusing unsafe path: {relative}')
        if relative in IGNORE_SENTINELS:
            planned.append(('sentinel',relative,path));actions.append(f'KEEP {relative} (runtime ignore sentinel)');continue
        if path.is_file() and digest(path)==meta.get('sha256'):
            planned.append(('remove',relative,path));actions.append(f'REMOVE {relative}')
        elif path.exists():actions.append(f'KEEP {relative} (modified)')
    cleaned=None
    if agents.is_file():
        text=agents.read_text(encoding='utf-8')
        if START in text and END in text:
            cleaned=(text[:text.index(START)].rstrip()+'\n'+text[text.index(END)+len(END):].lstrip('\n')).lstrip('\n')
            actions.append('REMOVE AGENTS.md managed block')
    if dry_run:return actions
    for kind,relative,path in planned:
        if kind=='remove':path.unlink()
        elif not path.exists():atomic_bytes(path,(ROOT/relative).read_bytes())
    if cleaned is not None:atomic_bytes(agents,cleaned.encode())
    if (target/MANIFEST).exists():(target/MANIFEST).unlink()
    return actions


def parse_roles(values: list[str]) -> dict[str,str]:
    result={}
    for item in values:
        if "=" not in item: raise InstallError("--role-model requires role=provider/model[#variant]")
        role, model=item.split("=",1)
        if role in result: raise InstallError(f"Duplicate role model: {role}")
        result[role]=model
    return result


def guided(args: argparse.Namespace) -> None:
    if args.target is None: args.target=Path(input("Drag the target repository folder here / Hedef klasörü sürükleyin:\n> ").strip().strip("'\""))
    if args.action is None:
        choice=input("\n[ ACTION / İŞLEM ]\n1) Safe install/update\n2) Dry run only\n3) Uninstall\nSelect [1]: ").strip() or "1"
        args.action={"1":"install","2":"dry-run","3":"uninstall"}.get(choice,"install")
    if args.action in {"install","dry-run"} and args.profile is None:
        choice=input("\n[ PROFILE / PROFİL ]\n1) Balanced / Dengeli\n2) Quality / Yüksek kalite\n3) Economy / Ekonomik\n4) Quota saver / Kota tasarrufu\n5) Custom / Özel\nSelect [1]: ").strip() or "1"
        args.profile={"1":"balanced","2":"quality","3":"economy","4":"quota-saver","5":"custom"}.get(choice,"balanced")
    if args.profile=="custom" and args.model is None:
        value=input("Default model selector (provider/model[#variant], blank=inherited): ").strip()
        args.model=value or None
        values=input("Optional role selectors, comma-separated role=provider/model[#variant] (blank=none): ").strip()
        if values: args.role_model.extend(item.strip() for item in values.split(",") if item.strip())
        selected=[args.model] if args.model else []
        selected.extend(item.split("=",1)[1] for item in args.role_model if "=" in item)
        if args.role_model and not args.model:
            print("Role overrides may differ from the provider inherited by the current OpenCode session.")
            args.allow_mixed_providers=(input("Allow role override with unknown inherited provider? Type MIX to confirm: ").strip()=="MIX")
        elif len({provider(item) for item in selected}) > 1:
            args.allow_mixed_providers=(input("Mix providers across native roles? Type MIX to confirm: ").strip()=="MIX")
    if args.action=="install" and not args.replace:
        args.replace=(input("Back up and replace conflicting managed files? [y/N]: ").strip().lower()=="y")


def main(argv: list[str] | None=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target",type=Path); parser.add_argument("--action",choices=("install","dry-run","uninstall"))
    parser.add_argument("--profile",choices=(*PROFILES,"custom")); parser.add_argument("--replace",action="store_true")
    parser.add_argument("--model"); parser.add_argument("--role-model",action="append",default=[]); parser.add_argument("--allow-mixed-providers",action="store_true")
    args=parser.parse_args(argv)
    try:
        if args.target is None or args.action is None or (args.action in {"install","dry-run"} and args.profile is None): guided(args)
        target=args.target.expanduser().resolve(); profile=args.profile or "balanced"; dry=args.action=="dry-run"
        if args.action=="uninstall": actions=uninstall(target,dry)
        else: actions=install(target,profile,args.replace,dry,args.model,parse_roles(args.role_model),args.allow_mixed_providers)
    except (InstallError,OSError,EOFError) as exc: print(f"INSTALL ERROR: {exc}",file=sys.stderr); return 2
    print("\n".join(actions)); print(f"\nTarget: {target}\nProfile: {profile}" + ("\nDRY RUN: no files changed" if dry else "")); return 0


if __name__=="__main__": raise SystemExit(main())
