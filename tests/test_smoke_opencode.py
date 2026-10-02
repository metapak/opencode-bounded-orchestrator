from __future__ import annotations

import importlib.util, json, unittest
from pathlib import Path
from unittest.mock import patch
import subprocess

ROOT=Path(__file__).resolve().parents[1]; SCRIPT=ROOT/"scripts/smoke_opencode.py"; ROLES={"owner","fast-lookup","explorer","researcher","implementer","verifier","failure-analyst","qa-operator","reviewer","advisor"}


def load():
    spec=importlib.util.spec_from_file_location("smoke_opencode",SCRIPT); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def base_permissions(role):
    if role=="owner": return [{"action":"edit","resource":"*","effect":"deny"},{"action":"subagent","resource":"*","effect":"deny"},*[{"action":"subagent","resource":child,"effect":"allow"} for child in sorted(ROLES-{"owner"})]]
    return [{"action":"edit","resource":"*","effect":"allow" if role=="implementer" else "deny"},{"action":"shell","resource":"*","effect":"ask" if role in {"implementer","verifier","qa-operator"} else "deny"},*([{"action":"shell","resource":"git status*","effect":"allow"}] if role in {"verifier","qa-operator"} else []),{"action":"subagent","resource":"*","effect":"deny"}]


class SmokeParserTests(unittest.TestCase):
    def fixture(self):
        config={"default_agent":"owner","agents":{role:{} for role in ROLES}}
        debug_config=[{"type":"document","path":"/tmp/project/.opencode/opencode.jsonc","info":config}]
        debug_agents=[{"id":role,"permissions":[{"action":"*","resource":"*","effect":"allow"},*base_permissions(role)]} for role in ROLES]
        return debug_config,debug_agents

    def test_accepts_v203_debug_shapes_and_effective_permissions(self):
        report=load().verify(*self.fixture()); self.assertEqual(report["status"],"pass"); self.assertEqual(set(report["loaded_roles"]),ROLES)

    def test_rejects_missing_role_and_wrong_order(self):
        smoke=load()
        config,agents=self.fixture(); agents=[item for item in agents if item["id"]!="reviewer"]
        with self.assertRaises(smoke.SmokeError): smoke.verify(config,agents)
        config,agents=self.fixture(); owner=next(item for item in agents if item["id"]=="owner"); owner["permissions"].append({"action":"subagent","resource":"*","effect":"deny"})
        with self.assertRaises(smoke.SmokeError): smoke.verify(config,agents)

    def test_failed_live_check_reports_only_safe_cli_identity_fields(self):
        smoke=load();config,agents=self.fixture()
        config[0]['info']['credentials']='PRIVATE_CONFIG'
        agents=[{'id':'builtin','prompt':'PRIVATE_PROMPT','permissions':[]},
                {'id':'bad\nPRIVATE_ID','body':'PRIVATE_TRANSCRIPT'}]
        responses=[subprocess.CompletedProcess([],0,json.dumps(config),''),
                   subprocess.CompletedProcess([],0,json.dumps(agents),''),
                   subprocess.CompletedProcess([],0,'opencode v2.0.3\n','PRIVATE_STDERR')]
        with patch.object(smoke.subprocess,'run',side_effect=responses), patch.object(smoke.time,'monotonic',side_effect=[0,5]):
            with self.assertRaises(smoke.SmokeError) as caught:
                smoke.run(['test-cli'])
        message=str(caught.exception)
        self.assertIn('missing bounded roles',message)
        self.assertIn('"cli_version": "opencode v2.0.3"',message)
        self.assertIn('"returned_agent_ids": ["builtin"]',message)
        self.assertIn('project_config_path',message)
        self.assertNotIn('PRIVATE',message)

    def test_retries_only_project_roles_waiting_for_plugin_activation(self):
        smoke=load();config,agents=self.fixture()
        responses=[subprocess.CompletedProcess([],0,json.dumps(config),''),
                   subprocess.CompletedProcess([],0,json.dumps([{'id':'build'}]),''),
                   subprocess.CompletedProcess([],0,json.dumps(agents),'')]
        with patch.object(smoke.subprocess,'run',side_effect=responses) as run, patch.object(smoke.time,'sleep') as sleep, patch.object(smoke.time,'monotonic',return_value=0):
            self.assertEqual(smoke.run(['test-cli'])['status'],'pass')
        self.assertEqual(run.call_count,3);sleep.assert_called_once_with(0.5)
        self.assertLessEqual(run.call_args.kwargs['timeout'],5)

    def test_permanent_missing_roles_still_fail_after_at_most_ten_reads(self):
        smoke=load();config,_=self.fixture()
        responses=[subprocess.CompletedProcess([],0,json.dumps(config),'')]
        responses += [subprocess.CompletedProcess([],0,'[]','') for _ in range(10)]
        responses += [subprocess.CompletedProcess([],0,'opencode v2.0.3','')]
        with patch.object(smoke.subprocess,'run',side_effect=responses) as run, patch.object(smoke.time,'sleep') as sleep, patch.object(smoke.time,'monotonic',return_value=0):
            with self.assertRaisesRegex(smoke.SmokeError,'missing bounded roles.*diagnostics='):
                smoke.run(['test-cli'])
        self.assertEqual(run.call_count,12);self.assertEqual(sleep.call_count,9)

    def test_partial_registry_with_unsafe_permissions_is_never_retried(self):
        cases=[('owner','edit','src/file.py','allow'),
               ('owner','subagent','unlisted','allow'),
               ('explorer','shell','anything','allow'),
               ('verifier','shell','rm file','allow')]
        for role,action,resource,effect in cases:
            with self.subTest(role=role,action=action):
                smoke=load();config,agents=self.fixture()
                item=next(agent for agent in agents if agent['id']==role)
                item['permissions'].append({'action':action,'resource':resource,'effect':effect})
                partial=[item]
                responses=[subprocess.CompletedProcess([],0,json.dumps(config),''),
                           subprocess.CompletedProcess([],0,json.dumps(partial),''),
                           subprocess.CompletedProcess([],0,'opencode v2.0.3','')]
                with patch.object(smoke.subprocess,'run',side_effect=responses) as run, patch.object(smoke.time,'sleep') as sleep:
                    with self.assertRaises(smoke.SmokeError) as caught: smoke.run(['test-cli'])
                self.assertNotIn('missing bounded roles',str(caught.exception))
                self.assertEqual(run.call_count,3);sleep.assert_not_called()

    def test_readiness_deadline_stops_without_another_agent_command(self):
        smoke=load();config,_=self.fixture()
        responses=[subprocess.CompletedProcess([],0,json.dumps(config),''),
                   subprocess.CompletedProcess([],0,'[]',''),
                   subprocess.CompletedProcess([],0,'opencode v2.0.3','')]
        with patch.object(smoke.subprocess,'run',side_effect=responses) as run, patch.object(smoke.time,'sleep') as sleep, patch.object(smoke.time,'monotonic',side_effect=[0,5]):
            with self.assertRaisesRegex(smoke.SmokeError,'missing bounded roles'):
                smoke.run(['test-cli'])
        self.assertEqual(run.call_count,3);sleep.assert_not_called()

    def test_readiness_retry_never_masks_config_schema_or_permission_errors(self):
        for failure in ('config','schema','malformed-items','permission'):
            with self.subTest(failure=failure):
                smoke=load();config,agents=self.fixture()
                if failure=='config': config[0]['info']['default_agent']='wrong'
                elif failure=='schema': agents={}
                elif failure=='malformed-items': agents=[{}]
                else: next(item for item in agents if item['id']=='owner')['permissions'].append({'action':'edit','resource':'*','effect':'allow'})
                responses=[subprocess.CompletedProcess([],0,json.dumps(config),''),
                           subprocess.CompletedProcess([],0,json.dumps(agents),''),
                           subprocess.CompletedProcess([],0,'opencode v2.0.3','')]
                with patch.object(smoke.subprocess,'run',side_effect=responses) as run, patch.object(smoke.time,'sleep') as sleep:
                    with self.assertRaises(smoke.SmokeError): smoke.run(['test-cli'])
                self.assertEqual(run.call_count,3);sleep.assert_not_called()

    def test_project_config_rejects_ambiguous_document(self):
        smoke=load(); payload=[{"type":"document","path":"/a/.opencode/opencode.jsonc","info":{"agents":{}}},{"type":"document","path":"/b/.opencode/opencode.jsonc","info":{"agents":{}}}]
        with self.assertRaises(smoke.SmokeError): smoke.project_config(payload)

    def test_project_config_accepts_windows_document_path(self):
        smoke=load(); config={"agents":{"owner":{}}}
        payload=[{"type":"document","path":r"D:\project\.opencode\opencode.jsonc","info":config}]
        self.assertIs(smoke.project_config(payload),config)

    def test_npm_launcher_uses_windows_command_wrapper(self):
        smoke=load()
        self.assertEqual(smoke.command_prefix("opencode","@opencode/cli@2.0.3","nt")[0],"npm.cmd")
        self.assertEqual(smoke.command_prefix("opencode","@opencode/cli@2.0.3","posix")[0],"npm")
        self.assertEqual(smoke.command_prefix("custom-opencode",None,"nt"),["custom-opencode"])


if __name__=="__main__": unittest.main()
