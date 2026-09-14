#!/usr/bin/env python3
"""Safely install OpenCode Bounded Orchestrator into a repository."""

from __future__ import annotations

import argparse
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
SELECTOR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*(?:#[A-Za-z0-9][A-Za-z0-9._-]*)?$")
PROFILES = {
    "balanced": {"owner":36,"fast-lookup":10,"explorer":22,"researcher":22,"implementer":34,"verifier":20,"failure-analyst":22,"qa-operator":20,"reviewer":22,"advisor":24},
    "quality": {"owner":56,"fast-lookup":16,"explorer":34,"researcher":34,"implementer":52,"verifier":32,"failure-analyst":34,"qa-operator":32,"reviewer":36,"advisor":40},
    "economy": {"owner":24,"fast-lookup":7,"explorer":14,"researcher":14,"implementer":22,"verifier":13,"failure-analyst":14,"qa-operator":13,"reviewer":14,"advisor":16},
    "quota-saver": {"owner":18,"fast-lookup":5,"explorer":10,"researcher":10,"implementer":16,"verifier":9,"failure-analyst":10,"qa-operator":9,"reviewer":10,"advisor":12},
}
MANAGED = [Path(".opencode/opencode.jsonc"), Path(".opencode/bounded-orchestrator.eval.example.json"), Path(".opencode/.candidate/.gitignore"), Path(".opencode/.bounded-orchestrator/.gitignore")]
MANAGED += [Path(f".opencode/agents/{role}.md") for role in ROLES]
MANAGED += [Path(".opencode/tools") / name for name in ("candidate.py","ledger.py","usage_report.py","local_eval.py")]
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
    if not set(data["files"]).issubset(ALLOWED_MANIFEST_FILES): raise InstallError("Install manifest contains an unmanaged path")
    if any(not isinstance(meta,dict) or not re.fullmatch(r"[0-9a-f]{64}",str(meta.get("sha256",""))) for meta in data["files"].values()): raise InstallError("Install manifest contains an invalid checksum")
    return data


def selector(value: str) -> str:
    if not SELECTOR.fullmatch(value): raise InstallError(f"Invalid model selector {value!r}; expected provider/model or provider/model#variant")
    return value


def provider(value: str) -> str: return value.split("/", 1)[0].lower()


def configured_template(profile: str, default_model: str | None, role_models: dict[str,str], allow_mixed: bool) -> bytes:
    if profile != "custom" and (default_model or role_models):
        raise InstallError("Model selectors are available only with the custom profile.")
    text = (ROOT / ".opencode/opencode.jsonc").read_text(encoding="utf-8")
    config = json.loads(text)
    steps = PROFILES["balanced"] if profile == "custom" else PROFILES[profile]
    for role in ROLES: config["agents"][role]["steps"] = steps[role]
    selectors = []
    if default_model:
        default_model = selector(default_model); config["model"] = default_model; selectors.append(default_model)
    for role, model in role_models.items():
        if role not in ROLES: raise InstallError(f"Unknown role in --role-model: {role}")
        model = selector(model); config["agents"][role]["model"] = model; selectors.append(model)
    if role_models and not default_model and not allow_mixed:
        raise InstallError("Role-only model overrides have an unknown inherited default provider; supply --model or explicitly pass --allow-mixed-providers.")
    providers = {provider(item) for item in selectors}
    if len(providers) > 1 and not allow_mixed:
        raise InstallError("Mixed providers require --allow-mixed-providers and explicit user confirmation.")
    return (json.dumps(config, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def configured_agent(role: str, profile: str, role_models: dict[str,str]) -> bytes:
    text=(ROOT/f".opencode/agents/{role}.md").read_text(encoding="utf-8")
    steps=(PROFILES["balanced"] if profile=="custom" else PROFILES[profile])[role]
    text=re.sub(r"^steps:\s*\d+\s*$",f"steps: {steps}",text,count=1,flags=re.MULTILINE)
    selected=role_models.get(role)
    if selected:
        text=re.sub(r"^(steps:\s*\d+\s*)$",rf"\1\nmodel: {selector(selected)}",text,count=1,flags=re.MULTILINE)
    return text.encode("utf-8")


def backup(target: Path, relative: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = target / BACKUPS / stamp / relative
    suffix = 1
    while destination.exists(): destination = destination.with_name(f"{destination.name}.{suffix}"); suffix += 1
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target / relative, destination)
    return destination


def replace_block(existing: str, block: str) -> str:
    if START in existing or END in existing:
        if existing.count(START) != 1 or existing.count(END) != 1 or existing.index(START) > existing.index(END): raise InstallError("AGENTS.md has malformed managed markers")
        before = existing[:existing.index(START)].rstrip(); after = existing[existing.index(END)+len(END):].lstrip("\n")
        return ((before + "\n\n") if before else "") + block.strip() + "\n" + (("\n" + after) if after else "")
    return existing.rstrip() + ("\n\n" if existing.strip() else "") + block.strip() + "\n"


def install(target: Path, profile: str, replace: bool, dry_run: bool, default_model: str | None, role_models: dict[str,str], allow_mixed: bool) -> list[str]:
    if not target.is_dir(): raise InstallError("Target must be an existing directory")
    manifest = load_manifest(target); actions=[]; files=dict(manifest["files"])
    config_data = configured_template(profile, default_model, role_models, allow_mixed)
    agents = target / "AGENTS.md"
    if agents.is_symlink() or (agents.exists() and not agents.is_file()):
        raise InstallError("Refusing unsafe AGENTS.md path")
    block=(ROOT/"templates/AGENTS.block.md").read_text(encoding="utf-8")
    existing=agents.read_text(encoding="utf-8") if agents.exists() else ""; updated=replace_block(existing, block)
    for relative in MANAGED:
        ensure_safe_parent(target, relative)
        source = ROOT / relative; destination = target / relative
        if relative == Path(".opencode/opencode.jsonc"): data=config_data
        elif relative.parent == Path(".opencode/agents"): data=configured_agent(relative.stem,profile,role_models)
        else: data=source.read_bytes()
        wanted = hashlib.sha256(data).hexdigest()
        if destination.is_symlink() or (destination.exists() and not destination.is_file()): raise InstallError(f"Refusing unsafe path: {relative}")
        if destination.exists() and digest(destination) != wanted:
            old_owned = files.get(relative.as_posix(), {}).get("sha256") == digest(destination)
            if not old_owned and not replace:
                actions.append(f"KEEP {relative} (conflict)"); continue
            if not dry_run: saved=backup(target, relative)
            actions.append(f"BACKUP {relative}" + ("" if dry_run else f" -> {saved.relative_to(target)}"))
        if not destination.exists() or digest(destination) != wanted:
            if not dry_run: atomic_bytes(destination, data)
            actions.append(f"INSTALL {relative}")
        else: actions.append(f"UNCHANGED {relative}")
        files[relative.as_posix()]={"sha256":wanted}
    if updated != existing:
        if agents.exists() and not dry_run: backup(target, Path("AGENTS.md"))
        if not dry_run: atomic_bytes(agents, updated.encode())
        actions.append("UPDATE AGENTS.md managed block")
    if not dry_run:
        payload={"schema":1,"version":(ROOT/"VERSION").read_text().strip(),"profile":profile,"files":files,"agents_block":True}
        atomic_bytes(target/MANIFEST,(json.dumps(payload,indent=2,sort_keys=True)+"\n").encode())
    return actions


def uninstall(target: Path, dry_run: bool) -> list[str]:
    manifest=load_manifest(target); actions=[]
    for name, meta in manifest["files"].items():
        relative=Path(name); path=target/relative
        ensure_safe_parent(target, relative)
        if relative in IGNORE_SENTINELS:
            if path.is_file() and not path.is_symlink(): actions.append(f"KEEP {relative} (runtime ignore sentinel)")
            elif path.exists(): raise InstallError(f"Refusing unsafe ignore sentinel: {relative}")
            else:
                if not dry_run: atomic_bytes(path,(ROOT/relative).read_bytes())
                actions.append(f"INSTALL {relative} (runtime ignore sentinel)")
            continue
        if path.is_file() and not path.is_symlink() and digest(path)==meta.get("sha256"):
            if not dry_run: path.unlink()
            actions.append(f"REMOVE {relative}")
        elif path.exists(): actions.append(f"KEEP {relative} (modified)")
    agents=target/"AGENTS.md"
    if agents.is_symlink() or (agents.exists() and not agents.is_file()): raise InstallError("Refusing unsafe AGENTS.md path")
    if agents.is_file():
        text=agents.read_text(encoding="utf-8")
        if START in text and END in text:
            cleaned=(text[:text.index(START)].rstrip()+"\n"+text[text.index(END)+len(END):].lstrip("\n")).lstrip("\n")
            if not dry_run: atomic_bytes(agents,cleaned.encode())
            actions.append("REMOVE AGENTS.md managed block")
    if not dry_run and (target/MANIFEST).exists(): (target/MANIFEST).unlink()
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
