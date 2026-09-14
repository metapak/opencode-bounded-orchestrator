from __future__ import annotations
import importlib.util, json, subprocess, sys, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def validator_module():
    spec=importlib.util.spec_from_file_location("repository_validator",ROOT/"scripts/validate.py"); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


class RepositoryTests(unittest.TestCase):
    def test_validator_passes(self):
        result=subprocess.run([sys.executable,str(ROOT/"scripts/validate.py")],text=True,capture_output=True,check=False); self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_default_is_provider_neutral_and_single_model(self):
        config=json.loads((ROOT/".opencode/opencode.jsonc").read_text()); self.assertNotIn("model",config)
        self.assertTrue(all("model" not in agent for agent in config["agents"].values()))

    def test_only_implementer_can_edit_and_all_children_deny_subagent(self):
        config=json.loads((ROOT/".opencode/opencode.jsonc").read_text())
        for role,agent in config["agents"].items():
            self.assertTrue(all(set(p)=={"action","resource","effect"} for p in agent["permissions"]))
            edit_allow=any(p["action"]=="edit" and p["effect"]=="allow" for p in agent["permissions"])
            self.assertEqual(edit_allow,role=="implementer")
            if role!="owner":
                self.assertEqual(agent["permissions"][-1],{"action":"subagent","resource":"*","effect":"deny"})

    def test_permission_order_matches_last_rule_wins(self):
        config=json.loads((ROOT/".opencode/opencode.jsonc").read_text())
        owner=[p for p in config["agents"]["owner"]["permissions"] if p["action"]=="subagent"]
        deny=next(i for i,p in enumerate(owner) if p["resource"]=="*" and p["effect"]=="deny")
        self.assertTrue(all(i>deny for i,p in enumerate(owner) if p["effect"]=="allow"))
        for role in ("verifier","qa-operator"):
            shell=[p for p in config["agents"][role]["permissions"] if p["action"]=="shell"]
            broad=next(i for i,p in enumerate(shell) if p["resource"]=="*")
            self.assertTrue(all(i>broad for i,p in enumerate(shell) if p["effect"]=="allow"))

    def test_no_api_keys_or_v1_config_keys(self):
        raw=(ROOT/".opencode/opencode.jsonc").read_text().lower(); self.assertNotIn("api_key",raw)
        for key in ('"agent":','"tools":','"max_depth":','"model_reasoning_effort":'): self.assertNotIn(key,raw)
        self.assertNotIn('"pattern":',raw); self.assertNotIn('"permission":',raw)
        for path in (ROOT/".opencode/agents").glob("*.md"):
            frontmatter=path.read_text().split("---",2)[1]
            self.assertNotIn("pattern:",frontmatter); self.assertNotIn("permission:",frontmatter)
            self.assertIn("resource:",frontmatter); self.assertIn("effect:",frontmatter)

    def test_validator_rejects_legacy_permission_item_keys(self):
        validator=validator_module()
        self.assertFalse(validator.valid_permission_rule({"action":"edit","pattern":"*","permission":"deny"}))
        self.assertTrue(validator.valid_permission_rule({"action":"edit","resource":"*","effect":"deny"}))

    def test_upstream_attribution_is_complete(self):
        combined=(ROOT/"NOTICE").read_text()+"\n"+(ROOT/"docs/provenance.md").read_text()
        for value in ("codex-astra-luna-orchestrator","donvito","https://github.com/donvito/codex-astra-luna-orchestrator","Apache License, Version 2.0","not affiliated with or endorsed"):
            self.assertIn(value,combined)


if __name__=="__main__": unittest.main()
