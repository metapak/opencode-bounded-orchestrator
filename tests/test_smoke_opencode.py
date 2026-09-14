from __future__ import annotations

import importlib.util, json, unittest
from pathlib import Path

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
