from __future__ import annotations
import json, shutil, subprocess, unittest
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

class Keys(HTMLParser):
    def __init__(self): super().__init__(); self.keys=[]
    def handle_starttag(self, tag, attrs):
        for key,value in attrs:
            if key in ('data-i18n','data-i18n-aria','data-i18n-placeholder'): self.keys.append(value)

class ConsoleLanguageTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('node'),'Node is only needed for this static JavaScript syntax check')
    def test_both_languages_cover_every_visible_static_key_and_script_parses(self):
        script=ROOT/'.opencode/tools/console.js'; html=ROOT/'.opencode/tools/console.html'
        subprocess.run(['node','--check',str(script)],check=True,capture_output=True,text=True)
        code="const fs=require('fs');let s=fs.readFileSync(process.argv[1],'utf8');let body=s.split('const messages=')[1].split('\\n};')[0]+'\\n}';const m=Function('return '+body)();console.log(JSON.stringify(Object.fromEntries(Object.entries(m).map(([k,v])=>[k,Object.keys(v)]))))"
        result=subprocess.run(['node','-e',code,str(script)],check=True,capture_output=True,text=True)
        keys=json.loads(result.stdout); parser=Keys(); parser.feed(html.read_text())
        for language in ('tr','en'):
            missing=set(parser.keys)-set(keys[language]); self.assertFalse(missing,f'{language} missing {missing}')
        self.assertEqual(set(keys['tr']),set(keys['en']))
        self.assertIn('<select id="model"',html.read_text())
        self.assertNotIn('<input id="model"',html.read_text())
        self.assertIn("document.createElement('select')",script.read_text())
        source=script.read_text()
        self.assertIn("sessionStorage.setItem('opencode-console-token',token)",source)
        self.assertIn("sessionStorage.getItem('opencode-console-token')",source)
        self.assertNotIn("localStorage.setItem('opencode-console-token'",source)
        self.assertIn("throw clientError('sessionInvalid')",source)
        self.assertIn("status(error?.uiCode||errorSummary(errorRaw))",source)
    def test_fixture_contains_real_shape_dates_without_chat_body(self):
        fixture=json.loads((ROOT/'tests/fixtures/opencode-export.json').read_text())
        self.assertTrue(all(isinstance(msg['info']['time']['created'],int) for msg in fixture['messages']))
        self.assertNotIn('parts',json.dumps([msg['info'] for msg in fixture['messages']]))

    @unittest.skipUnless(shutil.which('node'),'Node is needed for the task recommendation check')
    def test_task_suggestions_are_eight_distinct_bounded_drafts_without_model_guesses(self):
        script=ROOT/'.opencode/tools/console.js'
        code="const fs=require('fs');let s=fs.readFileSync(process.argv[1],'utf8');let body=s.split('const teamTasks=')[1].split('\\n];')[0]+'\\n]';console.log(JSON.stringify(Function('return '+body)()))"
        tasks=json.loads(subprocess.run(['node','-e',code,str(script)],check=True,capture_output=True,text=True).stdout)
        self.assertEqual([item['key'] for item in tasks],['game','web','research','backend','mobile','data','bug','security'])
        self.assertEqual(len({(item['profile'],tuple(item['roles']),tuple(item['duties'])) for item in tasks}),8)
        self.assertEqual({item['key']:item['profile'] for item in tasks},{'game':'quality','web':'balanced','research':'balanced','backend':'quality','mobile':'balanced','data':'balanced','bug':'economy','security':'quality'})
        for item in tasks:
            self.assertIn(item['profile'],('economy','balanced','quality','quota-saver'))
            self.assertTrue(2<=len(item['roles'])<=5)
            self.assertEqual(len(item['roles']),len(item['duties']))
            self.assertNotIn('model',item)
        source=script.read_text()
        self.assertIn("old.find(slot=>slot.role===role&&slot.model)",source)
        self.assertIn('function selectableModels(catalog)',source)
        self.assertIn("$('teamChiefActor').classList.add('conducting')",source)
        self.assertIn('function syncChiefMotion()',source)
        self.assertIn('id="orchestraSelectedValue"', (ROOT/'.opencode/tools/console.html').read_text())
        css=(ROOT/'.opencode/tools/console.css').read_text()
        self.assertIn('.performer.chief.conducting .music-note{animation:orchestra-note',css)
        self.assertIn('.performer.chief.conducting .baton-arm{animation:baton-swing',css)
        self.assertIn('.team-stage-chief.conducting .team-note{animation:orchestra-note',css)
        self.assertIn('.team-stage-chief.conducting .team-baton-arm{animation:baton-swing',css)
        self.assertNotIn('.team-stage-chief.conducting .team-baton-arm,.team-stage-chief.conducting .team-note{animation:none}',css)
        self.assertIn('const TEAM_MAX=50,TEAM_PAGE=10',source)

if __name__=='__main__': unittest.main()
