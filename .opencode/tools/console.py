#!/usr/bin/env python3
"""Local browser settings and observed usage. Python stdlib only."""
from __future__ import annotations
import argparse, copy, difflib, hashlib, json, os, re, secrets, sys, tempfile, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
import usage_report

ROLES = ('owner','fast-lookup','explorer','researcher','implementer','verifier','failure-analyst','qa-operator','reviewer','advisor')
PROFILES = {
 'balanced':[36,10,22,22,34,20,22,20,22,24], 'quality':[56,16,34,34,52,32,34,32,36,40],
 'economy':[24,7,14,14,22,13,14,13,14,16], 'quota-saver':[18,5,10,10,16,9,10,9,10,12],
}
MODEL = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._/-]*(?:#[A-Za-z0-9][A-Za-z0-9._-]*)?$')
class ConsoleError(ValueError): pass

def scrub(text):
    # Remove comments without changing offsets or touching string literals.
    pattern = r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/'
    clean = re.sub(pattern,lambda m: m[0] if m[0].startswith('"') else ''.join('\n' if c=='\n' else ' ' for c in m[0]),text)
    return re.sub(r',(?=\s*[}\]])',' ',clean)

def read(path):
    if not path.exists(): return '{}\n', {}
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000: raise ConsoleError('Unsafe or oversized configuration path.')
    text = path.read_text(encoding='utf-8')
    try: value=json.loads(scrub(text))
    except ValueError as exc: raise ConsoleError('Configuration is not valid JSON/JSONC.') from exc
    if not isinstance(value,dict): raise ConsoleError('Configuration must be an object.')
    return text,value

def safe(path):
    for parent in [path,*path.parents]:
        if parent.is_symlink(): raise ConsoleError('Symlinked configuration or state path refused.')

def atomic(path,data):
    safe(path); path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as stream: stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)

def digest(text): return hashlib.sha256(text.encode()).hexdigest()

# JSONC edits preserve every unrelated byte, including comments and credentials.
def spans(text):
    clean=scrub(text); decoder=json.JSONDecoder()
    def whitespace(i):
        while i<len(clean) and clean[i].isspace(): i+=1
        return i
    def parse(i):
        i=whitespace(i); start=i
        if clean[i]!='{':
            _,end=decoder.raw_decode(clean,i); return {'start':start,'end':end,'children':{}}
        children={}; i=whitespace(i+1)
        while clean[i]!='}':
            key,end=decoder.raw_decode(clean,i); i=whitespace(end)
            if clean[i]!=':': raise ConsoleError('Invalid JSONC member.')
            child=parse(i+1); child['member_end']=end
            children[key]=child; i=whitespace(child['end'])
            if clean[i]==',': i=whitespace(i+1)
            elif clean[i]!='}': raise ConsoleError('Invalid JSONC separator.')
        return {'start':start,'end':i+1,'close':i,'children':children}
    return parse(0)

def patch(text,path,value,remove=False):
    # Work recursively; a missing parent is inserted once as a small object.
    tree=spans(text); node=tree
    for index,key in enumerate(path):
        child=node['children'].get(key)
        if child is None:
            if remove: return text
            nested=value
            for part in reversed(path[index+1:]): nested={part:nested}
            close=node.get('close')
            if close is None: raise ConsoleError('Expected object at managed field.')
            before=text[node['start']+1:close]; stripped=scrub(before).rstrip()
            separator='' if not stripped else ','
            # An existing trailing comma was scrubbed; retain it rather than add another.
            raw_no_comments=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/','',before).rstrip()
            if raw_no_comments.endswith(','): separator=''
            addition=separator+'\n'+json.dumps(key)+': '+json.dumps(nested,ensure_ascii=False)+'\n'
            return text[:close]+addition+text[close:]
        if index==len(path)-1:
            if remove:
                # Removal via null is not equivalent to absence. Locate key and separator.
                keys=list(node['children']); pos=keys.index(key)
                left=node['start']+1 if pos==0 else node['children'][keys[pos-1]]['end']
                right=node['close'] if pos==len(keys)-1 else node['children'][keys[pos+1]]['start']
                # Recover start of next member's quoted key using scrubbed structure.
                clean=scrub(text)
                key_start=clean.rfind('"',left,child['start'])
                key_start=clean.rfind('"',left,key_start)
                if pos < len(keys)-1:
                    comma=clean.find(',',child['end'],right); return text[:key_start]+text[comma+1:]
                if pos>0:
                    comma=clean.find(',',left,child['start']); return text[:comma]+text[child['end']:]
                return text[:key_start]+text[child['end']:]
            return text[:child['start']]+json.dumps(value,ensure_ascii=False)+text[child['end']:]
        node=child
    return text

def get(config,path):
    node=config
    for key in path:
        if not isinstance(node,dict) or key not in node: return {'present':False}
        node=node[key]
    return {'present':True,'value':node}

class Settings:
    def __init__(self,root,user=None):
        self.root=root.resolve(); self.user=user or Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'opencode'
        self.targets={'project':self.root/'.opencode/opencode.jsonc','user':self.user/'opencode.jsonc'}
        self.lock=threading.Lock()
    def target(self,name):
        if name not in self.targets: raise ConsoleError('Unknown target.')
        path=self.targets[name]; other=path.with_suffix('.json')
        if other.exists() and path.exists(): raise ConsoleError('Both .json and .jsonc targets exist; merge them manually first.')
        path=other if other.exists() else path
        safe(path); return path
    def statepath(self,name):
        return (self.root/'.opencode/.bounded-orchestrator' if name=='project' else self.user/'.bounded-orchestrator')/'console-save.json'
    def snapshot(self,name):
        path=self.target(name); text,config=read(path)
        agents=config.get('agents',{})
        if not isinstance(agents,dict) or any(not isinstance(agents.get(role,{}),dict) for role in ROLES): raise ConsoleError('Invalid agents config.')
        roles={role:{key:value for key,value in agents.get(role,{}).items() if (key=='model' and isinstance(value,str) and MODEL.fullmatch(value)) or (key=='steps' and type(value)==int and value>0)} for role in ROLES}
        # Never return arbitrary config, provider credentials, prompts, or system text.
        return {'target':str(path),'revision':digest(text),'model':config.get('model') if isinstance(config.get('model'),str) and MODEL.fullmatch(config['model']) else '', 'roles':roles,'effective':self.effective(),'installed':(self.root/'.opencode/.bounded-orchestrator/install.json').is_file(),'profiles':list(PROFILES),'limitations':['Model availability and variants depend on the configured provider.','Markdown agent model/steps can override JSON settings; the console refuses conflicting Markdown overrides.','Parallelism has no verified numeric V2 setting; use one specialist by default.','Context, retry and report guidance are prompt preferences, not token ceilings.']}
    def effective(self):
        # Reconstruct only safe scalar fields from documented locations, never full config.
        result={'model':None,'roles':{role:{} for role in ROLES},'sources':[]}
        def apply(path):
            if not path.exists(): return
            safe(path); _,value=read(path); result['sources'].append(str(path))
            model=value.get('model')
            if isinstance(model,str) and MODEL.fullmatch(model): result['model']=model
            agents=value.get('agents',{})
            if not isinstance(agents,dict): raise ConsoleError('Invalid agents config.')
            for role in ROLES:
                values=agents.get(role,{})
                if not isinstance(values,dict): raise ConsoleError('Invalid agent config.')
                for key,item in values.items():
                    if (key=='model' and isinstance(item,str) and MODEL.fullmatch(item)) or (key=='steps' and type(item)==int and item>0): result['roles'][role][key]=item
        for ext in ['json','jsonc']: apply(self.user/('opencode.'+ext))
        ancestors=list(reversed([self.root,*self.root.parents]))
        for parent in ancestors:
            for ext in ['json','jsonc']: apply(parent/('opencode.'+ext))
        for parent in ancestors:
            for ext in ['json','jsonc']: apply(parent/'.opencode'/('opencode.'+ext))
        for folder in [self.user/'agents',*[parent/'.opencode/agents' for parent in ancestors]]:
            for role in ROLES:
                file=folder/(role+'.md')
                if not file.exists(): continue
                safe(file)
                if file.stat().st_size>100000: raise ConsoleError('Agent file too large.')
                front=file.read_text().split('---',2)
                if len(front)<3: continue
                for key in ['model','steps']:
                    found=re.search(r'^'+key+r':\s*(\S+)\s*$',front[1],re.M)
                    if found:
                        value=found[1]
                        if key=='model' and MODEL.fullmatch(value): result['roles'][role][key]=value
                        if key=='steps' and value.isdigit(): result['roles'][role][key]=int(value)
        result['limitations']=['Local scalar merge only; environment/remote config and provider catalog are not resolved. Confirm the running session with OpenCode debug config/agent.']
        return result
    def prepare(self,name,request):
        if not isinstance(request,dict) or set(request)-{'revision','profile','model','roles','allow_mixed','replace'}: raise ConsoleError('Unknown settings field.')
        path=self.target(name); text,config=read(path)
        if request.get('revision')!=digest(text): raise ConsoleError('Configuration changed. Reload before saving.')
        if not isinstance(config.get('agents',{}),dict) or any(not isinstance(config.get('agents',{}).get(role,{}),dict) for role in ROLES): raise ConsoleError('Invalid agent config.')
        profile=request.get('profile','balanced')
        if profile not in PROFILES and profile!='custom': raise ConsoleError('Invalid profile.')
        roles=request.get('roles',{})
        if not isinstance(roles,dict) or set(roles)-set(ROLES): raise ConsoleError('Unknown role.')
        changes=[]; models=[]
        model=request.get('model','')
        if not isinstance(model,str) or (model and (not MODEL.fullmatch(model) or '#' in model)): raise ConsoleError('Root model needs provider/model without #variant.')
        changes.append((['model'],{'present':bool(model),'value':model}))
        if model: models.append(model)
        for index,role in enumerate(ROLES):
            values=roles.get(role,{})
            if not isinstance(values,dict) or set(values)-{'model'}: raise ConsoleError('Role allows only a model selector.')
            selected=values.get('model','')
            if not isinstance(selected,str) or (selected and not MODEL.fullmatch(selected)): raise ConsoleError('Role model needs provider/model[#variant].')
            if selected: models.append(selected)
            agent_path=(self.root/'.opencode/agents' if name=='project' else self.user/'agents')/(role+'.md')
            if agent_path.exists():
                safe(agent_path)
                front=agent_path.read_text().split('---',2)
                if len(front)>2 and re.search(r'^model:',front[1],re.M): raise ConsoleError(f'{role} has a Markdown model override; merge it manually first.')
            changes.append((['agents',role,'model'],{'present':bool(selected),'value':selected}))
            if profile!='custom': changes.append((['agents',role,'steps'],{'present':True,'value':PROFILES[profile][index]}))
        if (len({m.split('/',1)[0] for m in models})>1 or (not model and models)) and request.get('allow_mixed') is not True: raise ConsoleError('Mixed or inherited providers require the explicit allow checkbox.')
        updated=text; operations=[]
        for keys,wanted in changes:
            previous=get(config,keys)
            if previous['present'] and ((keys[-1]=='model' and (not isinstance(previous['value'],str) or not MODEL.fullmatch(previous['value']))) or (keys[-1]=='steps' and (type(previous['value'])!=int or previous['value']<1))): raise ConsoleError('Existing managed field has an unsupported value; merge manually.')
            if previous==wanted or (not previous['present'] and not wanted['present']): continue
            # Steps in Markdown have precedence too; reject a mismatch, no hidden changes.
            if keys[-1]=='steps':
                agent_path=(self.root/'.opencode/agents' if name=='project' else self.user/'agents')/(keys[1]+'.md')
                if agent_path.exists():
                    front=agent_path.read_text().split('---',2)
                    found=re.search(r'^steps:\s*(\d+)\s*$',front[1],re.M) if len(front)>2 else None
                    if found and int(found[1])!=wanted['value']: raise ConsoleError('Profile differs from installed Markdown steps. Apply this preset with scripts/install.py first, or select custom to keep steps.')
            updated=patch(updated,keys,wanted.get('value'),not wanted['present']); operations.append({'path':keys,'before':previous,'after':wanted})
        read_value=json.loads(scrub(updated))
        for op in operations:
            if get(read_value,op['path'])!=op['after']: raise ConsoleError('Patch validation failed.')
        preview='\n'.join(''.join(difflib.unified_diff([json.dumps(op['before'],ensure_ascii=False)+'\n'],[json.dumps(op['after'],ensure_ascii=False)+'\n'],fromfile='before '+'.'.join(op['path']),tofile='after '+'.'.join(op['path']))) for op in operations)
        return path,text,updated,operations,preview
    def preview(self,name,request):
        _,_,_,ops,diff=self.prepare(name,request); return {'diff':diff or 'Değişiklik yok.','fields':len(ops)}
    def ownership(self,path,text,replace):
        manifest=self.root/'.opencode/.bounded-orchestrator/install.json'
        if path==self.targets['project'] and manifest.exists():
            safe(manifest); _,data=read(manifest)
            if data.get('schema')!=1 or not isinstance(data.get('files'),dict): raise ConsoleError('Invalid installer manifest.')
            entry=data.get('files',{}).get('.opencode/opencode.jsonc')
            if entry and entry.get('sha256')!=digest(text) and not replace: raise ConsoleError('Installer-owned config was modified. Explicit backup and replace consent is required.')
            return manifest,data,entry
        return None,None,None
    def private_runtime(self,name):
        # Backups can contain credentials: establish the package's reserved ignore
        # sentinel before writing any state, including on an uninstalled project.
        runtime=self.statepath(name).parent
        safe(runtime)
        ignore=runtime/'.gitignore'; safe(ignore)
        expected='*\n!.gitignore\n'
        if ignore.exists():
            if not ignore.is_file() or ignore.read_text(encoding='utf-8')!=expected:
                raise ConsoleError('Reserved runtime ignore is changed; restore its managed sentinel or reinstall before saving. Existing patterns were preserved.')
        else:
            runtime.mkdir(parents=True,exist_ok=True,mode=0o700)
            atomic(ignore,expected)
        try: os.chmod(runtime,0o700)
        except OSError: pass
        return runtime
    def save(self,name,request):
        with self.lock:
            path,text,updated,ops,diff=self.prepare(name,request)
            manifest,data,entry=self.ownership(path,text,request.get('replace') is True)
            if not ops: return {'saved':False,'diff':diff}
            self.private_runtime(name)
            statepath=self.statepath(name); safe(statepath)
            backup=statepath.parent/'backups'/('console-'+secrets.token_hex(8))/path.name
            atomic(backup,text)
            atomic(statepath,json.dumps({'schema':1,'target':str(path),'backup':str(backup),'operations':ops,'saved_hash':digest(updated)},indent=2)+'\n')
            atomic(path,updated)
            if entry:
                entry['sha256']=digest(updated); atomic(manifest,json.dumps(data,indent=2,sort_keys=True)+'\n')
            return {'saved':True,'fields':len(ops)}
    def restore(self,name,revision):
        with self.lock:
            path=self.target(name); text,config=read(path)
            if digest(text)!=revision: raise ConsoleError('Configuration changed. Reload first.')
            statepath=self.statepath(name); _,state=read(statepath)
            if state.get('schema')!=1 or state.get('target')!=str(path) or not isinstance(state.get('operations'),list): raise ConsoleError('No console-managed save to restore.')
            updated=text
            for op in reversed(state['operations']):
                keys=op.get('path',[])
                if not (keys==['model'] or (len(keys)==3 and keys[0]=='agents' and keys[1] in ROLES and keys[2] in {'model','steps'})): raise ConsoleError('Invalid restore field.')
                if get(config,keys)!=op['after']: raise ConsoleError('A saved field changed outside the console; restore refused.')
                updated=patch(updated,keys,op['before'].get('value'),not op['before']['present'])
            json.loads(scrub(updated)); manifest,data,entry=self.ownership(path,text,True)
            atomic(path,updated)
            if entry: entry['sha256']=digest(updated); atomic(manifest,json.dumps(data,indent=2,sort_keys=True)+'\n')
            statepath.unlink(); return {'restored':True}

def server(settings,port=0,fixture=None):
    token=secrets.token_urlsafe(32)
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def send(self,status,payload,kind='application/json; charset=utf-8'):
            body=payload.encode() if isinstance(payload,str) else json.dumps(payload,ensure_ascii=False).encode()
            self.send_response(status); self.send_header('Content-Type',kind); self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.send_header('X-Content-Type-Options','nosniff'); self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'"); self.end_headers(); self.wfile.write(body)
        def authorized(self):
            host=f'127.0.0.1:{self.server.server_port}'
            return self.headers.get('Host')==host and (self.headers.get('Origin') in (None,'http://'+host)) and self.headers.get('X-Console-Token')==token
        def do_GET(self):
            parsed=urlsplit(self.path)
            host=f'127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host')!=host: return self.send(403,{'error':'Host refused.'})
            if parsed.path in {'/','/console.js','/console.css'}:
                name={'/':'console.html','/console.js':'console.js','/console.css':'console.css'}[parsed.path]
                body=(Path(__file__).parent/name).read_text(); return self.send(200,body,{'/':'text/html; charset=utf-8','/console.js':'text/javascript; charset=utf-8','/console.css':'text/css; charset=utf-8'}[parsed.path])
            if not self.authorized(): return self.send(403,{'error':'Session token required.'})
            try:
                query=parse_qs(parsed.query,keep_blank_values=True); target=query.get('target',['project'])[0]
                if parsed.path=='/api/settings': return self.send(200,settings.snapshot(target))
                if parsed.path=='/api/usage':
                    try:
                        days=int(query['days'][0]) if query.get('days',[''])[0] else None
                        payload=usage_report.collect(root=settings.root,days=days,project=query.get('project',[None])[0],session=query.get('session',[None])[0] or None,fixture=fixture)
                    except (usage_report.UsageError,OSError,ValueError) as exc: payload={'platform':'opencode','status':'unavailable','source':'OpenCode CLI','error':str(exc),'records':[]}
                    return self.send(200,payload)
                return self.send(404,{'error':'Unknown endpoint.'})
            except (ConsoleError,OSError,ValueError): return self.send(400,{'error':'Configuration unavailable or invalid; inspect selected local file.'})
        def do_POST(self):
            if not self.authorized(): return self.send(403,{'error':'Origin, host or session token refused.'})
            try:
                length=int(self.headers.get('Content-Length','0'))
                if not 0<length<=65536 or self.headers.get('Content-Type')!='application/json': raise ConsoleError('Invalid body.')
                body=json.loads(self.rfile.read(length)); name=body.get('target','project')
                if self.path=='/api/preview': result=settings.preview(name,body.get('settings'))
                elif self.path=='/api/save': result=settings.save(name,body.get('settings'))
                elif self.path=='/api/restore': result=settings.restore(name,body.get('revision'))
                else: return self.send(404,{'error':'Unknown endpoint.'})
                self.send(200,result)
            except (ConsoleError,OSError,ValueError,TypeError,AttributeError) as exc: self.send(400,{'error':str(exc) if isinstance(exc,ConsoleError) else 'Invalid request or local file.'})
    http=ThreadingHTTPServer(('127.0.0.1',port),Handler); http.daemon_threads=True
    return http,'http://127.0.0.1:'+str(http.server_port)+'/#'+token

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('action',nargs='?',choices=['configure','dashboard'],default='configure'); parser.add_argument('--root',type=Path,default=Path.cwd()); parser.add_argument('--port',type=int,default=0); parser.add_argument('--no-browser',action='store_true'); parser.add_argument('--fixture',type=Path); args=parser.parse_args(argv)
    if not args.root.is_dir() or not 0<=args.port<=65535: parser.error('Existing root and port 0..65535 required.')
    http,url=server(Settings(args.root),args.port,args.fixture); print('OpenCode local console: '+url,flush=True)
    if not args.no_browser: webbrowser.open(url)
    try: http.serve_forever()
    except KeyboardInterrupt: pass
    finally: http.server_close()
    return 0
if __name__=='__main__': raise SystemExit(main())
