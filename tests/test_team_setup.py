from __future__ import annotations
import importlib.util,json,subprocess,sys,tempfile,threading,unittest
from unittest.mock import patch
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request,urlopen
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.opencode/tools'))
import console,team_editor

class TeamSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve()/'project';self.root.mkdir()
        self.settings=console.Settings(self.root,self.root/'user')
        self.installer=console.install_module(ROOT/'scripts/install.py')
    def request(self,team=None):
        return {'project':str(self.root),'team':team or [{'role':'researcher','model':'','duty':'Find evidence'},{'role':'implementer','model':'','duty':'Write code'}],'profile':'balanced','model':'','replace':False,'allow_mixed':False,'revision':console.team_revision(self.root)}
    def install(self):
        request=self.request();console.team_request(self.settings,self.installer,request,'save')
        return request
    def test_distribution_preview_install_and_installed_edit(self):
        initial=self.request()
        self.assertGreater(console.team_request(self.settings,self.installer,initial,'preview')['fields'],0)
        self.assertEqual(list(self.root.iterdir()),[])
        console.team_request(self.settings,self.installer,initial,'save')
        config=json.loads((self.root/'.opencode/opencode.jsonc').read_text())
        allows=[r['resource'] for r in config['agents']['owner']['permissions'] if r['action']=='subagent' and r['effect']=='allow']
        self.assertEqual(allows,['helper-01','helper-02'])
        events=self.settings.history('project');self.assertEqual(len(events),1);self.assertEqual(events[0]['profile'],'balanced')
        owner=(self.root/'.opencode/agents/owner.md').read_text()
        self.assertIn('resource: helper-01',owner);self.assertNotIn('resource: implementer, effect: allow',owner)
        team=initial['team'][:1];request=self.request(team);request['revision']=console.team_revision(self.root)
        self.assertEqual(console.team_request(self.settings,None,request,'preview')['fields'],3)
        console.team_request(self.settings,None,request,'save')
        self.assertFalse((self.root/'.opencode/agents/helper-02.md').exists())
        self.assertTrue(list((self.root/'.opencode/.bounded-orchestrator/backups').rglob('helper-02.md')))
        self.assertEqual(console.team_request(self.settings,None,{'project':str(self.root)},'inspect')['team'],team)
    def test_team_api_rejects_new_superseded_models_and_preserves_saved_legacy(self):
        fresh=self.request();fresh['model']='openai/gpt-5.6-sol'
        with self.assertRaisesRegex(console.ConsoleError,'superseded'):
            console.team_request(self.settings,self.installer,fresh,'preview')
        with self.assertRaisesRegex(console.ConsoleError,'superseded'):
            console.team_request(self.settings,self.installer,fresh,'save')
        fresh_helper=self.request();fresh_helper['team'][0]['model']='openai/gpt-5.5';fresh_helper['allow_mixed']=True
        with self.assertRaisesRegex(console.ConsoleError,'superseded'):
            console.team_request(self.settings,self.installer,fresh_helper,'preview')
        self.assertEqual(list(self.root.iterdir()),[])
        team=self.request()['team'];team[0]['model']='openai/gpt-5.5'
        self.installer.install(self.root,'balanced',False,False,'openai/gpt-5.6-sol',{},False,team)
        config=self.root/'.opencode/opencode.jsonc';manifest=self.root/'.opencode/.bounded-orchestrator/install.json'
        request=self.request(team);request['model']='openai/gpt-5.6-sol';request['team'][0]['duty']='Compare evidence';request['revision']=console.team_revision(self.root)
        self.assertGreater(console.team_request(self.settings,None,request,'preview')['fields'],0)
        console.team_request(self.settings,None,request,'save')
        self.assertEqual(json.loads(config.read_text())['model'],'openai/gpt-5.6-sol')
        self.assertEqual(json.loads(manifest.read_text())['team'][0]['model'],'openai/gpt-5.5')
        changed=self.request([{'role':'researcher','model':'openai/gpt-5.6-sol','duty':'New choice'},*request['team'][1:]])
        changed['model']='openai/gpt-5.6-sol';changed['revision']=console.team_revision(self.root)
        before=(config.read_bytes(),manifest.read_bytes())
        for mode in ('preview','save'):
            with self.assertRaisesRegex(console.ConsoleError,'superseded'):
                console.team_request(self.settings,None,changed,mode)
        changed_chief=self.request(request['team']);changed_chief['model']='openai/gpt-5.5';changed_chief['revision']=console.team_revision(self.root)
        with self.assertRaisesRegex(console.ConsoleError,'superseded'):
            console.team_request(self.settings,None,changed_chief,'preview')
        direct={key:changed[key] for key in ('team','profile','model','replace','allow_mixed')};direct['revision']=None
        with self.assertRaisesRegex(team_editor.TeamError,'superseded'):
            team_editor.prepare(self.root,direct)
        self.assertEqual((config.read_bytes(),manifest.read_bytes()),before)
    def test_installed_editor_conflicts_and_private_backup(self):
        self.install();slot=self.root/'.opencode/agents/helper-02.md';slot.write_text(slot.read_text()+'\nprivate user edit')
        req=self.request(self.request()['team'][:1]);req['revision']=console.team_revision(self.root)
        with self.assertRaises(console.ConsoleError):console.team_request(self.settings,None,req,'preview')
        self.assertIn('private user edit',slot.read_text())
        req=self.request();req['revision']=console.team_revision(self.root)
        req['model']='acme/base';req['team'][0]['model']='acme/research#deep';req['allow_mixed']=False;req['replace']=True
        # Different models with the same provider are supported; variant stays exact.
        console.team_request(self.settings,None,req,'save')
        config=json.loads((self.root/'.opencode/opencode.jsonc').read_text())
        self.assertEqual(config['agents']['helper-01']['model'],'acme/research#deep')
        backup=list((self.root/'.opencode/.bounded-orchestrator/backups').rglob('opencode.jsonc'))
        self.assertTrue(backup)
        self.assertEqual(subprocess.run(['git','init','-q',str(self.root)]).returncode,0)
        self.assertEqual(subprocess.run(['git','-C',str(self.root),'check-ignore','-q',str(backup[-1])]).returncode,0)
    @unittest.skipIf(sys.platform=='win32','Windows symlink creation needs elevated privileges')
    def test_installed_backup_symlink_rejected_without_mutation(self):
        self.install();outside=Path(self.tmp.name).resolve()/'outside';outside.mkdir()
        runtime=self.root/'.opencode/.bounded-orchestrator';backups=runtime/'backups'
        if backups.exists():
            import shutil
            shutil.rmtree(backups)
        backups.symlink_to(outside,target_is_directory=True)
        config=self.root/'.opencode/opencode.jsonc';manifest=runtime/'install.json'
        before=(config.read_bytes(),manifest.read_bytes())
        request=self.request();request['team'][0]['duty']='Changed duty';request['revision']=console.team_revision(self.root)
        with self.assertRaises(console.ConsoleError):console.team_request(self.settings,None,request,'save')
        self.assertEqual(before,(config.read_bytes(),manifest.read_bytes()))
        self.assertEqual(list(outside.iterdir()),[])

    def test_empty_slot_override_preserves_base_role_model(self):
        team=[{'role':'implementer','model':'','duty':'Write code'}]
        self.installer.install(self.root,'custom',False,False,'acme/base',{'implementer':'acme/build'},False,team)
        config_path=self.root/'.opencode/opencode.jsonc'
        self.assertEqual(json.loads(config_path.read_text())['agents']['helper-01']['model'],'acme/build')
        request=self.request(team);request['profile']='custom';request['model']='acme/base';request['revision']=console.team_revision(self.root)
        console.team_request(self.settings,None,request,'save')
        self.assertEqual(json.loads(config_path.read_text())['agents']['helper-01']['model'],'acme/build')

    def test_preferences_profile_updates_and_restores_installed_helper_steps(self):
        self.install();path=self.root/'.opencode/opencode.jsonc'
        before=json.loads(path.read_text())
        self.assertEqual(before['agents']['helper-01']['steps'],before['agents']['researcher']['steps'])
        request={'revision':self.settings.snapshot('project')['revision'],'profile':'quality','model':'','roles':{}}
        preview=self.settings.preview('project',request)
        self.assertGreater(preview['fields'],10)
        self.settings.save('project',request)
        self.assertTrue(self.settings.snapshot('project')['restore_available'])
        after=json.loads(path.read_text())
        self.assertEqual(after['agents']['helper-01']['steps'],after['agents']['researcher']['steps'])
        self.assertGreater(after['agents']['helper-01']['steps'],before['agents']['helper-01']['steps'])
        self.assertEqual(self.settings.profile_from_config(path.read_text()),'quality')
        self.settings.restore('project',self.settings.snapshot('project')['revision'])
        restored=json.loads(path.read_text())
        self.assertEqual(restored['agents']['helper-01']['steps'],before['agents']['helper-01']['steps'])
        self.assertFalse(self.settings.snapshot('project')['restore_available'])

    def test_preferences_restore_failure_rolls_back_config_manifest_and_state(self):
        self.install();config=self.root/'.opencode/opencode.jsonc';manifest=self.root/'.opencode/.bounded-orchestrator/install.json'
        request={'revision':self.settings.snapshot('project')['revision'],'profile':'quality','model':'','roles':{}}
        self.settings.save('project',request)
        state=self.settings.statepath('project');before=(config.read_bytes(),manifest.read_bytes(),state.read_bytes())
        original=console.atomic
        def fail_manifest(path,data):
            if path==manifest: raise OSError('injected restore manifest failure')
            return original(path,data)
        with patch.object(console,'atomic',side_effect=fail_manifest):
            with self.assertRaises(OSError):self.settings.restore('project',self.settings.snapshot('project')['revision'])
        self.assertEqual((config.read_bytes(),manifest.read_bytes(),state.read_bytes()),before)
        self.assertTrue(self.settings.snapshot('project')['restore_available'])

    def test_roster_change_does_not_offer_preferences_undo(self):
        self.install();self.assertFalse(self.settings.snapshot('project')['restore_available'])
        reduced=self.request(self.request()['team'][:1]);reduced['revision']=console.team_revision(self.root)
        console.team_request(self.settings,None,reduced,'save')
        self.assertFalse(self.settings.snapshot('project')['restore_available'])

    def test_fifty_slots_installed_editor_reload_shrink_and_preferences_restore(self):
        team=[{'role':'implementer' if i%2 else 'researcher','model':'','duty':f'Scope {i:02d}'} for i in range(1,51)]
        req=self.request(team);console.team_request(self.settings,self.installer,req,'save')
        self.assertEqual(len(console.team_request(self.settings,None,{'project':str(self.root)},'inspect')['team']),50)
        path=self.root/'.opencode/opencode.jsonc';before=json.loads(path.read_text())
        preference={'revision':self.settings.snapshot('project')['revision'],'profile':'quality','model':'','roles':{}}
        self.settings.save('project',preference)
        self.assertGreater(json.loads(path.read_text())['agents']['helper-50']['steps'],before['agents']['helper-50']['steps'])
        self.settings.restore('project',self.settings.snapshot('project')['revision'])
        self.assertEqual(json.loads(path.read_text())['agents']['helper-50']['steps'],before['agents']['helper-50']['steps'])
        reduced=self.request(team[:1]);reduced['revision']=console.team_revision(self.root)
        console.team_request(self.settings,None,reduced,'save')
        self.assertFalse((self.root/'.opencode/agents/helper-50.md').exists())
        self.assertEqual(len(console.team_request(self.settings,None,{'project':str(self.root)},'inspect')['team']),1)

    def test_installed_editor_mid_write_failure_rolls_back(self):
        self.install();config=self.root/'.opencode/opencode.jsonc';manifest=self.root/'.opencode/.bounded-orchestrator/install.json';owner=self.root/'.opencode/agents/owner.md'
        before=[path.read_bytes() for path in (config,manifest,owner)]
        request=self.request();request.pop('project');request['team'][0]['duty']='Changed';request['profile']='quality';request['revision']=team_editor.prepare(self.root,{**request,'revision':None})['revision']
        original=console.atomic
        def fail_once(path,data):
            if path==self.root/'.opencode/agents/helper-01.md': raise OSError('injected write failure')
            return original(path,data)
        with patch.object(console,'atomic',side_effect=fail_once):
            with self.assertRaises(OSError):team_editor.save(self.root,request)
        self.assertEqual([path.read_bytes() for path in (config,manifest,owner)],before)

    def test_history_write_failure_rolls_back_team_files(self):
        self.install();config=self.root/'.opencode/opencode.jsonc';manifest=self.root/'.opencode/.bounded-orchestrator/install.json';slot=self.root/'.opencode/agents/helper-01.md'
        before=[path.read_bytes() for path in (config,manifest,slot)]
        request=self.request();request['team'][0]['duty']='Changed';request['profile']='quality';request['revision']=console.team_revision(self.root)
        with patch.object(self.settings,'record_history',side_effect=OSError('injected history failure')):
            with self.assertRaises(OSError):console.team_request(self.settings,None,request,'save')
        self.assertEqual([path.read_bytes() for path in (config,manifest,slot)],before)

    def test_editor_rechecks_new_helper_created_after_prepare(self):
        self.install();config=self.root/'.opencode/opencode.jsonc';manifest=self.root/'.opencode/.bounded-orchestrator/install.json';helper=self.root/'.opencode/agents/helper-03.md'
        before=(config.read_bytes(),manifest.read_bytes())
        request=self.request(self.request()['team']+[{'role':'verifier','model':'','duty':'Verify changes'}]);request.pop('project');request['profile']='quality'
        request['revision']=team_editor.prepare(self.root,{**request,'revision':None})['revision']
        original=console.atomic
        def create_external(path,data):
            original(path,data)
            if path==config:helper.write_text('USER-SENTINEL')
        with patch.object(console,'atomic',side_effect=create_external):
            with self.assertRaises(team_editor.TeamError):team_editor.save(self.root,request)
        self.assertEqual(helper.read_text(),'USER-SENTINEL')
        self.assertEqual((config.read_bytes(),manifest.read_bytes()),before)

    def test_http_rejects_oversized_team_body_without_mutation(self):
        http,url=console.server(self.settings,installer=self.installer);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();base,token=url.split('/#')
        try:
            data=b' '+b'x'*65536
            request=Request(base+'/api/team/save',data=data,headers={'Content-Type':'application/json','X-Console-Token':token,'Origin':base})
            with self.assertRaises(HTTPError) as error:urlopen(request)
            self.assertEqual(error.exception.code,400)
            error.exception.close()
            self.assertFalse((self.root/'.opencode/opencode.jsonc').exists())
        finally:http.shutdown();thread.join(timeout=3);http.server_close()

    def test_malformed_history_blocks_team_save_before_any_mutation(self):
        self.install();config=self.root/'.opencode/opencode.jsonc';manifest=self.root/'.opencode/.bounded-orchestrator/install.json'
        history=self.settings.historypath('project');history.write_text('{malformed')
        before=(config.read_bytes(),manifest.read_bytes())
        request=self.request();request['team'][0]['duty']='Changed';request['revision']=console.team_revision(self.root)
        with self.assertRaises(console.ConsoleError):console.team_request(self.settings,None,request,'save')
        self.assertEqual(before,(config.read_bytes(),manifest.read_bytes()))

    def test_tampered_other_project_is_refused_even_in_distribution_mode(self):
        other=Path(self.tmp.name).resolve()/'other';other.mkdir()
        request=self.request();request['project']=str(other)
        with self.assertRaises(console.ConsoleError):console.team_request(self.settings,self.installer,request,'preview')
        self.assertEqual(list(other.iterdir()),[])

    def test_http_team_auth_preview_and_close(self):
        http,url=console.server(self.settings,installer=self.installer);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        base,token=url.split('/#')
        def post(path,payload,key=token):
            data=json.dumps(payload).encode();return urlopen(Request(base+path,data=data,headers={'Content-Type':'application/json','X-Console-Token':key,'Origin':base}))
        try:
            with self.assertRaises(HTTPError) as error:post('/api/team/inspect',{'project':str(self.root)},'bad')
            self.assertEqual(error.exception.code,403)
            info=json.load(post('/api/team/inspect',{'project':str(self.root)}))
            self.assertFalse(info['installed']);self.assertEqual(info['mode'],'distribution')
            result=json.load(post('/api/team/preview',self.request()))
            self.assertGreater(result['fields'],0)
            self.assertFalse((self.root/'.opencode/opencode.jsonc').exists())
            self.assertTrue(json.load(post('/api/team/save',self.request()))['saved'])
            self.assertTrue((self.root/'.opencode/opencode.jsonc').exists())
            self.assertTrue(json.load(post('/api/close',{}))['closed'])
            thread.join(timeout=3);self.assertFalse(thread.is_alive())
        finally:http.server_close()

if __name__=='__main__':unittest.main()
