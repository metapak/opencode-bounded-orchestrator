from __future__ import annotations
import importlib.util, json, os, subprocess, sys, tempfile, threading, unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError
ROOT=Path(__file__).resolve().parents[1]; TOOLS=ROOT/'.opencode/tools'; sys.path.insert(0,str(TOOLS))
import console, usage_report

class ConsoleTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name).resolve(); self.settings=console.Settings(self.root,self.root/'user'); self.path=self.settings.target('project'); self.path.parent.mkdir(parents=True); self.path.write_text('{\n // keep comment\n "provider": {"secret":"DO_NOT_SHOW"},\n "unrelated": [1,2],\n "agents":{"reviewer":{"steps":22}},\n}\n')
    def tearDown(self): self.tmp.cleanup()
    def request(self,**kwargs):
        return {'revision':self.settings.snapshot('project')['revision'],'profile':'custom','model':'acme/base','roles':{'reviewer':{'model':'acme/review#high'}},**kwargs}
    def test_atomic_preserves_exact_lf_bytes_on_every_platform(self):
        console.atomic(self.path,'first\nsecond\n')
        self.assertEqual(self.path.read_bytes(),b'first\nsecond\n')
    def test_preview_save_restore_preserves_unrelated_bytes_and_edits(self):
        before=self.path.read_text(); request=self.request(); preview=self.settings.preview('project',request)
        self.assertNotIn('DO_NOT_SHOW',preview['diff']); self.assertNotIn('DO_NOT_SHOW',json.dumps(self.settings.snapshot('project'))); self.assertEqual(self.path.read_text(),before)
        self.settings.save('project',request); current=self.path.read_text(); self.assertIn('// keep comment',current); self.assertIn('"unrelated": [1,2]',current)
        current=current.replace('[1,2]','[1,2,3]'); self.path.write_text(current); snapshot=self.settings.snapshot('project'); self.assertTrue(snapshot['restore_available']); revision=snapshot['revision']; self.settings.restore('project',revision)
        value=json.loads(console.scrub(self.path.read_text())); self.assertEqual(value['unrelated'],[1,2,3]); self.assertNotIn('model',value); self.assertNotIn('model',value['agents']['reviewer']); self.assertEqual(value['provider']['secret'],'DO_NOT_SHOW')
    def test_stale_unknown_invalid_and_symlink_requests_refused(self):
        bad=self.request(); bad['revision']='stale'
        with self.assertRaises(console.ConsoleError): self.settings.save('project',bad)
        for values in ({'model':'acme/a#high'},{'profile':'missing'},{'roles':{'evil':{}}},{'model':'a/m;touch /tmp/x'}):
            with self.assertRaises(console.ConsoleError): self.settings.preview('project',self.request(**values))
        self.path.unlink(); self.path.symlink_to(self.root/'elsewhere')
        with self.assertRaises(console.ConsoleError): self.settings.snapshot('project')
    def test_superseded_model_cannot_be_newly_selected_but_unchanged_legacy_survives(self):
        original=self.path.read_bytes()
        for selected in ('openai/gpt-5.5','openai/gpt-5.6-sol','openrouter/openai/gpt-5.6-sol'):
            with self.assertRaisesRegex(console.ConsoleError,'superseded'):
                self.settings.preview('project',self.request(model=selected,roles={}))
            with self.assertRaisesRegex(console.ConsoleError,'superseded'):
                self.settings.save('project',self.request(model='',roles={'reviewer':{'model':selected}}))
            self.assertEqual(self.path.read_bytes(),original)
        self.path.write_text('{"model":"openai/gpt-5.6-sol","agents":{"reviewer":{"model":"openai/gpt-5.5"}}}\n')
        unchanged={'revision':self.settings.snapshot('project')['revision'],'profile':'economy','model':'openai/gpt-5.6-sol','roles':{'reviewer':{'model':'openai/gpt-5.5'}}}
        self.settings.preview('project',unchanged)
        self.settings.save('project',unchanged)
        saved=json.loads(self.path.read_text())
        self.assertEqual(saved['model'],'openai/gpt-5.6-sol')
        self.assertEqual(saved['agents']['reviewer']['model'],'openai/gpt-5.5')
        self.assertEqual(saved['agents']['owner']['steps'],24)
    def test_target_selection_and_installer_ownership(self):
        user_before=self.settings.snapshot('user'); self.settings.save('user',{'revision':user_before['revision'],'profile':'economy','model':'','roles':{}})
        self.assertNotIn('model',json.loads(console.scrub(self.path.read_text())))
        manifest=self.root/'.opencode/.bounded-orchestrator/install.json'; manifest.parent.mkdir(parents=True,exist_ok=True); manifest.write_text(json.dumps({'schema':1,'files':{'.opencode/opencode.jsonc':{'sha256':'0'*64}}}))
        with self.assertRaises(console.ConsoleError): self.settings.save('project',self.request())
        self.settings.save('project',self.request(replace=True)); data=json.loads(manifest.read_text()); self.assertEqual(data['files']['.opencode/opencode.jsonc']['sha256'],console.digest(self.path.read_text()))
    def test_managed_restore_conflict_and_presets(self):
        self.settings.save('project',self.request(profile='economy')); config=json.loads(console.scrub(self.path.read_text())); self.assertEqual(config['agents']['owner']['steps'],24)
        self.path.write_text(self.path.read_text().replace('acme/base','acme/changed'))
        with self.assertRaises(console.ConsoleError): self.settings.restore('project',self.settings.snapshot('project')['revision'])
    def test_fresh_project_private_backups_ignored_before_first_save(self):
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        (self.root/'.gitignore').write_text('.opencode/opencode.jsonc\n')
        self.settings.save('project',self.request())
        runtime=self.root/'.opencode/.bounded-orchestrator'
        self.assertEqual((runtime/'.gitignore').read_text(),'*\n!.gitignore\n')
        backups=list((runtime/'backups').rglob('opencode.jsonc')); self.assertEqual(len(backups),1)
        self.assertIn('DO_NOT_SHOW',backups[0].read_text())
        for path in [*backups,runtime/'console-save.json']:
            self.assertEqual(subprocess.run(['git','-C',str(self.root),'check-ignore','-q',str(path)]).returncode,0)
            if sys.platform!='win32': self.assertEqual(path.stat().st_mode & 0o777,0o600)
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True)
        staged=subprocess.run(['git','-C',str(self.root),'ls-files','--cached'],check=True,text=True,capture_output=True).stdout
        self.assertNotIn('backups/',staged); self.assertNotIn('console-save.json',staged)
        staged_diff=subprocess.run(['git','-C',str(self.root),'diff','--cached'],check=True,text=True,capture_output=True).stdout
        self.assertNotIn('DO_NOT_SHOW',staged_diff)

    def test_changed_runtime_ignore_is_preserved_and_save_refused(self):
        runtime=self.root/'.opencode/.bounded-orchestrator'; runtime.mkdir(parents=True)
        ignore=runtime/'.gitignore'; ignore.write_text('custom-pattern\n!backups/\n')
        before=self.path.read_text()
        with self.assertRaises(console.ConsoleError): self.settings.save('project',self.request())
        self.assertEqual(ignore.read_text(),'custom-pattern\n!backups/\n')
        self.assertEqual(self.path.read_text(),before); self.assertFalse((runtime/'backups').exists()); self.assertFalse((runtime/'console-save.json').exists())

    def test_jsonc_patch_and_remove_variants(self):
        for source in ['{}','{"a":1}','{"a":1,}','{/*comment*/"a":1 //comment\n}','{"a":{"x":1,"y":2},"b":3}']:
            added=console.patch(source,['agents','owner','model'],'acme/base'); self.assertEqual(json.loads(console.scrub(added))['agents']['owner']['model'],'acme/base')
            removed=console.patch(added,['agents','owner','model'],None,True); self.assertNotIn('model',json.loads(console.scrub(removed))['agents']['owner'])
        for source in ['{"model":"a/b","x":2}','{"x":2,"model":"a/b"}','{"x":2,"model":"a/b","y":3}','{"model":"a/b",}']:
            removed=console.patch(source,['model'],None,True); self.assertNotIn('model',json.loads(console.scrub(removed)))
    def test_model_catalog_observed_ids_refresh_and_offline_unavailable(self):
        result=subprocess.CompletedProcess([],0,'openai/gpt-6.1-sol\nanthropic/claude-sonnet\nSECRET=not-a-model\n', '')
        with patch.object(console.shutil,'which',return_value='/usr/bin/opencode'), patch.object(console.subprocess,'run',return_value=result) as run:
            catalog=console.model_catalog(self.root)
            self.assertEqual(catalog['status'],'connected'); self.assertEqual(catalog['models'],['anthropic/claude-sonnet','openai/gpt-6.1-sol'])
            self.assertEqual(run.call_args.args[0],['/usr/bin/opencode','models'])
            console.model_catalog(self.root,refresh=True)
            self.assertEqual(run.call_args.args[0],['/usr/bin/opencode','models','--refresh'])
        with patch.object(console.shutil,'which',return_value=None):
            offline=console.model_catalog(self.root)
        self.assertEqual(offline['status'],'unavailable'); self.assertEqual(offline['reason'],'missing'); self.assertEqual(offline['models'],[]); self.assertIn('connect OpenCode',' '.join(offline['limitations']))
        with patch.object(console.shutil,'which',return_value='opencode'), patch.object(console.subprocess,'run',side_effect=subprocess.TimeoutExpired('opencode',20)):
            self.assertEqual(console.model_catalog(self.root)['status'],'unavailable')

    def test_actual_http_security_settings_and_missing_cli(self):
        http,url=console.server(self.settings); thread=threading.Thread(target=http.serve_forever,daemon=True); thread.start(); base,token=url.split('/#')
        def request(path,body=None,headers=None):
            return Request(base+path,data=json.dumps(body).encode() if body else None,headers={'X-Console-Token':token,**({'Content-Type':'application/json'} if body else {}),**(headers or {})})
        try:
            self.assertEqual(http.server_address[0],'127.0.0.1')
            with urlopen(base+'/') as page:
                self.assertIn('charset=utf-8',page.headers.get('Content-Type','').lower())
                self.assertIn(b'\xc3\x87al\xc4\xb1\xc5\x9fmalar',page.read())
            snap=json.load(urlopen(request('/api/settings'))); self.assertNotIn('DO_NOT_SHOW',json.dumps(snap))
            for headers in [{'Origin':'https://evil.example'},{'Host':'evil.example'},{'X-Console-Token':'bad'}]:
                with self.assertRaises(HTTPError) as error: urlopen(request('/api/save',{'target':'project','settings':self.request()},headers))
                self.assertEqual(error.exception.code,403); error.exception.close()
            with patch.object(console.shutil,'which',return_value=None): catalog=json.load(urlopen(request('/api/models'))); self.assertEqual(catalog['status'],'unavailable')
            with self.assertRaises(HTTPError) as refresh_error: urlopen(request('/api/models/refresh',{}, {'Origin':'https://evil.example'}))
            self.assertEqual(refresh_error.exception.code,403); refresh_error.exception.close()
            with patch.object(usage_report.shutil,'which',return_value=None): data=json.load(urlopen(request('/api/usage')))
            self.assertEqual(data['status'],'unavailable'); self.assertNotIn('observed',data)
            payload={'target':'project','settings':self.request()}; self.assertEqual(json.load(urlopen(request('/api/preview',payload)))['fields'],2); self.assertTrue(json.load(urlopen(request('/api/save',payload)))['saved'])
        finally: http.shutdown(); http.server_close(); thread.join()

    @unittest.skipIf(os.name=='nt','Browser removal is unavailable on Windows')
    def test_browser_uninstall_preview_cancel_stale_and_modified_file(self):
        installer=console.install_module(ROOT/'scripts/install.py')
        installer.install(self.root,'balanced',True,False,None,{},False)
        modified=self.root/'.opencode/agents/explorer.md';modified.write_text(modified.read_text()+'\nmy change\n')
        agents=self.root/'AGENTS.md';edited_agents=agents.read_text().replace(installer.END,'my instruction\n'+installer.END)
        agents.write_text(edited_agents)
        owned=self.root/'.opencode/agents/implementer.md';manifest=self.root/installer.MANIFEST
        user_config=self.settings.target('user');user_config.parent.mkdir(parents=True,exist_ok=True);user_config.write_text('{"model":"user/example"}')
        http,url=console.server(self.settings,installer=installer);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base,token=url.split('/#')
        def post(path,body):
            request=Request(base+path,data=json.dumps(body).encode(),headers={'X-Console-Token':token,'Content-Type':'application/json'})
            return json.load(urlopen(request))
        def rejected(path,body,code=400):
            with self.assertRaises(HTTPError) as error: post(path,body)
            self.assertEqual(error.exception.code,code);error.exception.close()
        target={'project':str(self.root)}
        try:
            with self.assertRaises(HTTPError) as denied:
                urlopen(Request(base+'/api/team/uninstall/preview',data=b'{}',headers={'Content-Type':'application/json'}))
            self.assertEqual(denied.exception.code,403);denied.exception.close()
            preview=post('/api/team/uninstall/preview',target)
            self.assertIn('KEEP .opencode/agents/explorer.md (modified)',preview['actions'])
            self.assertIn('KEEP AGENTS.md managed block (modified)',preview['actions'])
            self.assertIn('REMOVE .opencode/agents/implementer.md',preview['actions'])
            rejected('/api/team/uninstall/confirm',{**target,'preview_id':preview['preview_id'],'confirm':False})
            post('/api/team/uninstall/cancel',target)
            rejected('/api/team/uninstall/confirm',{**target,'preview_id':preview['preview_id'],'confirm':True})
            self.assertTrue(owned.exists());self.assertTrue(manifest.exists())
            preview=post('/api/team/uninstall/preview',target)
            modified.write_text(modified.read_text()+'another change\n')
            rejected('/api/team/uninstall/confirm',{**target,'preview_id':preview['preview_id'],'confirm':True})
            self.assertTrue(owned.exists());self.assertTrue(manifest.exists())
            preview=post('/api/team/uninstall/preview',target)
            result=post('/api/team/uninstall/confirm',{**target,'preview_id':preview['preview_id'],'confirm':True})
            self.assertTrue(result['removed']);self.assertFalse(owned.exists());self.assertTrue(modified.exists());self.assertFalse(manifest.exists())
            self.assertEqual(agents.read_text(),edited_agents)
            self.assertEqual(user_config.read_text(),'{"model":"user/example"}')
            self.assertEqual((self.root/'.opencode/.bounded-orchestrator/.gitignore').read_text(),'*\n!.gitignore\n')
            rejected('/api/team/uninstall/preview',target)
        finally: http.shutdown();http.server_close();thread.join()

    def test_browser_uninstall_rejects_wrong_target_and_manifest_escape(self):
        installer=console.install_module(ROOT/'scripts/install.py')
        manifest=self.root/installer.MANIFEST;manifest.parent.mkdir(parents=True,exist_ok=True)
        manifest.write_text(json.dumps({'schema':1,'files':{'../../escape':{'sha256':'0'*64}}}))
        http,url=console.server(self.settings,installer=installer);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base,token=url.split('/#')
        def post(body):
            request=Request(base+'/api/team/uninstall/preview',data=json.dumps(body).encode(),headers={'X-Console-Token':token,'Content-Type':'application/json'})
            return urlopen(request)
        try:
            for body in ({'project':str(self.root.parent)},{'project':str(self.root)}):
                with self.assertRaises(HTTPError) as error: post(body)
                self.assertEqual(error.exception.code,400);error.exception.close()
            self.assertTrue(manifest.exists())
        finally: http.shutdown();http.server_close();thread.join()

    @unittest.skipIf(os.name=='nt','Browser removal is unavailable on Windows')
    def test_browser_uninstall_rejects_file_appearing_after_approved_preview(self):
        installer=console.install_module(ROOT/'scripts/install.py')
        installer.install(self.root,'balanced',True,False,None,{},False)
        missing=self.root/'.opencode/agents/explorer.md';missing.unlink()
        manifest=self.root/installer.MANIFEST;owned=self.root/'.opencode/agents/owner.md'
        http,url=console.server(self.settings,installer=installer);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base,token=url.split('/#')
        def post(path,body):
            request=Request(base+path,data=json.dumps(body).encode(),headers={'X-Console-Token':token,'Content-Type':'application/json'})
            return json.load(urlopen(request))
        original=installer.uninstall
        def file_appears(project,dry_run,expected_actions=None):
            if not dry_run: missing.write_bytes((ROOT/'.opencode/agents/explorer.md').read_bytes())
            return original(project,dry_run,expected_actions)
        try:
            target={'project':str(self.root)};preview=post('/api/team/uninstall/preview',target)
            self.assertNotIn('REMOVE .opencode/agents/explorer.md',preview['actions'])
            with patch.object(installer,'uninstall',file_appears):
                with self.assertRaises(HTTPError) as error:
                    post('/api/team/uninstall/confirm',{**target,'preview_id':preview['preview_id'],'confirm':True})
                self.assertEqual(error.exception.code,400);error.exception.close()
            self.assertTrue(missing.exists());self.assertTrue(owned.exists());self.assertTrue(manifest.exists())
        finally: http.shutdown();http.server_close();thread.join()

    @unittest.skipIf(os.name=='nt','Windows symlink creation needs elevated privileges')
    def test_browser_uninstall_rejects_symlinked_managed_parent(self):
        installer=console.install_module(ROOT/'scripts/install.py')
        outside=self.root/'outside';outside.mkdir();sentinel=outside/'owner.md';sentinel.write_text('keep me')
        agents=self.root/'.opencode/agents';agents.parent.mkdir(parents=True,exist_ok=True);agents.symlink_to(outside,target_is_directory=True)
        manifest=self.root/installer.MANIFEST;manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({'schema':1,'files':{'.opencode/agents/owner.md':{'sha256':installer.digest(sentinel)}}}))
        with self.assertRaises(console.ConsoleError): console.uninstall_plan(self.settings,installer,{'project':str(self.root)})
        self.assertEqual(sentinel.read_text(),'keep me');self.assertTrue(manifest.exists())

    @unittest.skipUnless(os.name=='nt','Windows-only browser removal gate')
    def test_browser_uninstall_is_disabled_on_windows_without_mutation(self):
        installer=console.install_module(ROOT/'scripts/install.py')
        installer.install(self.root,'balanced',True,False,None,{},False)
        manifest=self.root/installer.MANIFEST;managed=self.root/'.opencode/agents/owner.md'
        before=(manifest.read_bytes(),managed.read_bytes())
        with self.assertRaisesRegex(console.ConsoleError,'unavailable on Windows'):
            console.uninstall_plan(self.settings,installer,{'project':str(self.root)})
        self.assertEqual((manifest.read_bytes(),managed.read_bytes()),before)

class UsageShapeTests(unittest.TestCase):
    def export(self):
        return {'info':{'id':'ses_safe','title':'SECRET'},'messages':[{'info':{'role':'assistant','modelID':'model','providerID':'acme','agent':'implementer','time':{'created':1790677800000},'tokens':{'input':100,'output':12,'reasoning':4,'cache':{'read':9,'write':2}}},'parts':[{'text':'SECRET BODY'}]}]}
    def test_export_only_allowlisted_counters(self):
        result=usage_report.normalize_export(self.export()); self.assertEqual(result['observed']['input'],100); self.assertEqual(result['observed']['cache_read'],9); self.assertNotIn('SECRET',json.dumps(result)); self.assertEqual(result['records'][0]['thread'],'ses_safe'); self.assertEqual(result['records'][0]['created'],1790677800000)
    def test_malformed_shapes_and_missing_fields(self):
        for payload in [[],{}, {'info':{},'messages':[]}, {'info':{'id':'ses_x'},'messages':[1]}]:
            with self.assertRaises(usage_report.UsageError): usage_report.normalize_export(payload)
        for count in [-1,True,'100',float('inf')]:
            payload=self.export(); payload['messages'][0]['info']['tokens']['input']=count
            with self.assertRaises(usage_report.UsageError): usage_report.normalize_export(payload)
        payload=self.export(); payload['messages'][0]['info'].pop('tokens'); self.assertEqual(usage_report.normalize_export(payload)['observed'],{})
    def test_cli_failure_timeout_invalid_json_and_argv(self):
        with patch.object(usage_report.shutil,'which',return_value='opencode'):
            for side in [subprocess.TimeoutExpired('opencode',30),OSError('secret detail')]:
                with patch.object(usage_report.subprocess,'run',side_effect=side):
                    with self.assertRaises(usage_report.UsageError): usage_report.collect()
            for result in [subprocess.CompletedProcess([],1,'','SECRET'),subprocess.CompletedProcess([],0,'not-json','')]:
                with patch.object(usage_report.subprocess,'run',return_value=result):
                    with self.assertRaises(usage_report.UsageError): usage_report.collect(session='ses_safe')
            with patch.object(usage_report.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps(self.export()),'')) as run:
                usage_report.collect(session='ses_safe'); self.assertEqual(run.call_args.args[0],['opencode','export','ses_safe','--sanitize'])
            with self.assertRaises(usage_report.UsageError): usage_report.collect(session='--help')
    def test_fixture_explicit_demo(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture=Path(directory)/'export.json'; fixture.write_text(json.dumps(self.export())); result=usage_report.collect(fixture=fixture); self.assertIn('DEMO',result['source'])

if __name__=='__main__': unittest.main()
