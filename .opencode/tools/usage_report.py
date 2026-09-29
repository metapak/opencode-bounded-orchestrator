#!/usr/bin/env python3
"""Observed OpenCode stats and explicitly scoped sanitized session exports."""
from __future__ import annotations
import argparse, json, math, re, shutil, subprocess, sys
from pathlib import Path
from typing import Any

class UsageError(RuntimeError): pass
LIMITATIONS = ['Stats may contain rounded display counts.', 'No inferred costs, quota, savings, or subscription conversions.', 'Stats has no thread records; use an explicit sanitized session export.']

def run(command: str, args: list[str], root: Path | None = None) -> str:
    executable = shutil.which(command) if '/' not in command else command
    if not executable: raise UsageError('OpenCode CLI was not found; usage data is unavailable.')
    try:
        result = subprocess.run([executable, *args], cwd=root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc: raise UsageError('OpenCode command unavailable or timed out.') from exc
    if result.returncode: raise UsageError(f'OpenCode command failed (exit {result.returncode}); no usage available.')
    if len(result.stdout) > 8_000_000: raise UsageError('OpenCode output exceeds the safe size limit.')
    return result.stdout

def normalize_stats(text: str) -> dict[str, Any]:
    if not isinstance(text, str): raise UsageError('Stats must be display text, not an assumed JSON contract.')
    observed = {}; rounded = []
    labels = {'Input':'input', 'Output':'output', 'Cache Read':'cache_read', 'Cache Write':'cache_write', 'Sessions':'sessions', 'Messages':'messages'}
    for label, key in labels.items():
        match = re.search(r'│\s*' + label + r'\s+([\d,.]+[KM]?)\s*│', text)
        if match:
            value = match[1].replace(',', ''); factor = 1000 if value.endswith('K') else 1000000 if value.endswith('M') else 1
            try: observed[key] = float(value.rstrip('KM')) * factor
            except ValueError as exc: raise UsageError('Invalid stats counter.') from exc
            if not math.isfinite(observed[key]): raise UsageError('Invalid stats counter.')
            if factor != 1: rounded.append(key)
    if not observed: raise UsageError('Unrecognized OpenCode stats display; counters unavailable.')
    return {'platform':'opencode', 'status':'available', 'source':'opencode stats (display)', 'observed':observed, 'rounded':rounded, 'groups':[], 'records':[], 'limitations':LIMITATIONS}

def normalize_export(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or not isinstance(payload.get('info'), dict) or not isinstance(payload.get('messages'), list): raise UsageError('Unsupported sanitized export shape.')
    ident = payload['info'].get('id')
    if not isinstance(ident,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,160}',ident): raise UsageError('Invalid exported session id.')
    records = []
    for msg in payload['messages']:
        if not isinstance(msg,dict) or not isinstance(msg.get('info'),dict): raise UsageError('Malformed exported message.')
        info = msg['info']
        if info.get('role') != 'assistant': continue
        tokens = info.get('tokens', {})
        if not isinstance(tokens,dict) or not isinstance(tokens.get('cache',{}),dict): raise UsageError('Malformed tokens.')
        counters = {}
        for key, value in [('input',tokens.get('input')),('output',tokens.get('output')),('reasoning',tokens.get('reasoning')),('cache_read',tokens.get('cache',{}).get('read')),('cache_write',tokens.get('cache',{}).get('write'))]:
            if value is not None:
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0 or value > 10**15: raise UsageError('Invalid token count.')
                counters[key] = value
        model = info.get('modelID'); provider = info.get('providerID'); agent = info.get('agent')
        safe = lambda value: value if isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9._/#-]{1,200}',value) else None
        records.append({'thread':ident, 'model':safe(model), 'provider':safe(provider), 'agent':safe(agent), 'observed':counters})
    totals = {key:sum(record['observed'][key] for record in records if key in record['observed']) for key in {key for record in records for key in record['observed']}}
    return {'platform':'opencode','status':'available','source':'opencode export --sanitize (explicit session)', 'observed':totals,'rounded':[], 'groups':[], 'records':records,'limitations':['Only the selected session is represented; chat bodies and titles are omitted.','Missing counters are unavailable, never zero-filled.']}

def collect(command: str = 'opencode', *, root: Path | None = None, days: int | None = None, project: str | None = None, session: str | None = None, fixture: Path | None = None) -> dict[str, Any]:
    if fixture:
        if fixture.stat().st_size > 8_000_000: raise UsageError('Fixture too large.')
        try: report = normalize_export(json.loads(fixture.read_text()))
        except (OSError,ValueError) as exc: raise UsageError('Invalid export fixture.') from exc
        report['source'] = 'DEMO fixture (not live usage)'; return report
    if session:
        if not re.fullmatch(r'ses_[A-Za-z0-9_-]{1,156}',session): raise UsageError('Invalid OpenCode session id.')
        try: return normalize_export(json.loads(run(command,['export',session,'--sanitize'],root)))
        except ValueError as exc: raise UsageError('Invalid export JSON.') from exc
    args = ['stats']
    if days is not None:
        if isinstance(days,bool) or not isinstance(days,int) or not 0 <= days <= 3650: raise UsageError('Days must be 0..3650.')
        args += ['--days', str(days)]
    if project is not None:
        if not isinstance(project,str) or len(project)>160 or (project and not re.fullmatch(r'[A-Za-z0-9_-]+',project)): raise UsageError('Invalid project id.')
        args += ['--project',project]
    return normalize_stats(run(command,args,root))

def main(argv: list[str] | None = None) -> int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--command',default='opencode'); parser.add_argument('--json',action='store_true'); parser.add_argument('--days',type=int); parser.add_argument('--project'); parser.add_argument('--session'); parser.add_argument('--fixture',type=Path); args=parser.parse_args(argv)
    try: report=collect(args.command,days=args.days,project=args.project,session=args.session,fixture=args.fixture)
    except (UsageError,OSError) as exc:
        print(json.dumps({'platform':'opencode','status':'unavailable','source':'OpenCode CLI','error':str(exc)})); return 2
    print(json.dumps(report,indent=2,ensure_ascii=False)); return 0
if __name__=='__main__': raise SystemExit(main())
