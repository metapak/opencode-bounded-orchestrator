from __future__ import annotations
import copy, json, subprocess, sys, tempfile, threading, unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.opencode/tools'))
import console, usage_report

class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve(); self.settings=console.Settings(self.root,self.root/'user')
        self.fixture=json.loads((ROOT/'tests/fixtures/opencode-breakdown.json').read_text())
    def test_exact_nonduplicated_models_styles_and_filter(self):
        report=usage_report.breakdown(self.fixture['sessions'],history=self.fixture['history'],now_ms=1790800000000,demo=True)
        self.assertEqual(report['exact_observed_total'],3075)
        self.assertEqual(sum(report['model_breakdown'].values()),3075)
        self.assertEqual(sum(report['style_breakdown'].values()),3075)
        self.assertEqual(report['observed']['cache_read'],880)
        self.assertEqual(report['style_breakdown'],{'economy':2410,'quality':665})
        self.assertEqual(report['coverage']['partial_messages'],0)
        recent=usage_report.breakdown(self.fixture['sessions'],history=self.fixture['history'],days=1,now_ms=1790855000000,demo=True)
        self.assertEqual(recent['exact_observed_total'],0)
        one=usage_report.breakdown(self.fixture['sessions'],history=self.fixture['history'],project='demo',demo=True)
        self.assertEqual(one['exact_observed_total'],3075)
        none=usage_report.breakdown(self.fixture['sessions'],history=self.fixture['history'],project='another',demo=True)
        self.assertEqual(none['exact_observed_total'],0)
    def test_unknown_before_save_crossing_restore_and_missing_components(self):
        items=copy.deepcopy(self.fixture['sessions']); history=copy.deepcopy(self.fixture['history'])
        prior=usage_report.breakdown(items,history=[],demo=True)
        self.assertEqual(prior['style_breakdown'],{'unknown':3075})
        # The change is after the assistant message but before session-list updated.
        history.insert(1,{'timestamp':items[0]['created']+120000,'project':'demo','profile':'balanced'})
        crossed=usage_report.breakdown(items,history=history,demo=True)
        self.assertEqual(crossed['style_breakdown']['unknown'],2410)
        items[0].pop('updated');items[0]['export']['info'].pop('time')
        ambiguous=usage_report.breakdown(items,history=self.fixture['history'],demo=True)
        self.assertEqual(ambiguous['style_breakdown']['unknown'],2410)
        items[0]['export']['messages'][0]['info']['tokens']['cache'].pop('write')
        partial=usage_report.breakdown(items,history=[],demo=True)
        self.assertEqual(partial['exact_observed_total'],3025)
        self.assertEqual(partial['coverage']['partial_messages'],1)
        self.assertEqual(sum(partial['model_breakdown'].values()),partial['exact_observed_total'])
    def test_history_private_save_restore_and_no_secret(self):
        subprocess.run(['git','init','-q',str(self.root)],check=True)
        target=self.settings.target('project');target.parent.mkdir(parents=True);target.write_text('{"provider":{"apiKey":"PRIVATE_SECRET"}}\n')
        request={'revision':self.settings.snapshot('project')['revision'],'profile':'economy','model':'','roles':{}}
        self.assertTrue(self.settings.save('project',request)['saved'])
        path=self.settings.historypath('project'); events=json.loads(path.read_text())
        self.assertEqual(len(events),1); self.assertEqual(events[0]['profile'],'economy'); self.assertNotIn('PRIVATE_SECRET',path.read_text())
        self.assertEqual(subprocess.run(['git','-C',str(self.root),'check-ignore','-q',str(path)]).returncode,0)
        if sys.platform!='win32': self.assertEqual(path.stat().st_mode & 0o777,0o600)
        self.settings.restore('project',self.settings.snapshot('project')['revision'])
        events=json.loads(path.read_text());self.assertEqual(len(events),2);self.assertEqual(events[-1]['profile'],'custom');self.assertGreater(events[-1]['timestamp'],events[0]['timestamp'])
        subprocess.run(['git','-C',str(self.root),'add','.'],check=True)
        staged=subprocess.run(['git','-C',str(self.root),'ls-files','--cached'],capture_output=True,text=True,check=True).stdout
        self.assertNotIn('console-settings-history',staged)
    def test_corrupt_history_save_and_restore_change_nothing(self):
        target=self.settings.target('project');target.parent.mkdir(parents=True);target.write_text('{}\n')
        manifest=self.root/'.opencode/.bounded-orchestrator/install.json';manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({'schema':1,'files':{'.opencode/opencode.jsonc':{'sha256':console.digest(target.read_text())}}}))
        history=self.settings.historypath('project');history.write_text('{broken')
        request={'revision':self.settings.snapshot('project')['revision'],'profile':'economy','model':'','roles':{}}
        before=(target.read_bytes(),manifest.read_bytes(),history.read_bytes())
        with self.assertRaises(console.ConsoleError): self.settings.save('project',request)
        self.assertEqual(before,(target.read_bytes(),manifest.read_bytes(),history.read_bytes()))
        self.assertFalse(self.settings.statepath('project').exists())
        history.write_text('[]')
        self.settings.save('project',request)
        state=self.settings.statepath('project');history.write_text('{broken again')
        before=(target.read_bytes(),manifest.read_bytes(),history.read_bytes(),state.read_bytes())
        with self.assertRaises(console.ConsoleError):self.settings.restore('project',self.settings.snapshot('project')['revision'])
        self.assertEqual(before,(target.read_bytes(),manifest.read_bytes(),history.read_bytes(),state.read_bytes()))
    def test_http_breakdown_fixture_and_auth(self):
        fixture=ROOT/'tests/fixtures/opencode-breakdown.json'
        http,url=console.server(self.settings,fixture=fixture); thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        base,token=url.split('/#')
        try:
            req=Request(base+'/api/usage?breakdown=1',headers={'X-Console-Token':token})
            result=json.load(urlopen(req));self.assertEqual(result['exact_observed_total'],3075);self.assertIn('DEMO',result['source']);self.assertNotIn('parts',json.dumps(result))
            html=urlopen(base+'/').read().decode();self.assertIn('modelBars',html);self.assertIn('styleDonut',html)
        finally:http.shutdown();http.server_close();thread.join()
    def test_cli_session_list_sanitization_and_failures(self):
        item=self.fixture['sessions'][0]
        listed=[{'id':item['id'],'directory':str(self.root),'projectId':item['project'],'created':item['created'],'title':'PRIVATE_TITLE'}]
        exported=copy.deepcopy(item['export']); exported['messages'][0]['parts']=[{'text':'PRIVATE_CHAT_BODY'}]
        with patch.object(usage_report,'run',side_effect=[json.dumps(listed),json.dumps(exported)]) as run:
            result=usage_report.collect_breakdown(root=self.root,project='',history=[])
        self.assertEqual(result['exact_observed_total'],2410)
        self.assertEqual(run.call_args_list[0].args[1],['session','list','--max-count','12','--format','json'])
        self.assertEqual(run.call_args_list[1].args[1],['export',item['id'],'--sanitize'])
        self.assertNotIn('PRIVATE_',json.dumps(result))
        with patch.object(usage_report,'run',return_value='bad json'):
            with self.assertRaises(usage_report.UsageError): usage_report.collect_breakdown(root=self.root)

if __name__=='__main__':unittest.main()
