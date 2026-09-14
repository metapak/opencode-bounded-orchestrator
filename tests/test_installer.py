from __future__ import annotations

import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; INSTALL=ROOT/"scripts/install.py"; ROLES=("owner","fast-lookup","explorer","researcher","implementer","verifier","failure-analyst","qa-operator","reviewer","advisor")


class InstallerTests(unittest.TestCase):
    def setUp(self): self.tmp=tempfile.TemporaryDirectory(); self.target=Path(self.tmp.name)/"project"; self.target.mkdir()
    def tearDown(self): self.tmp.cleanup()
    def invoke(self,*args): return subprocess.run([sys.executable,str(INSTALL),"--target",str(self.target),*args],text=True,capture_output=True,check=False)

    def test_fresh_install_and_update(self):
        first=self.invoke("--action","install","--profile","balanced"); self.assertEqual(first.returncode,0,first.stderr)
        config=json.loads((self.target/".opencode/opencode.jsonc").read_text()); self.assertNotIn("model",config); self.assertTrue((self.target/".opencode/.bounded-orchestrator/install.json").is_file())
        second=self.invoke("--action","install","--profile","quality"); self.assertEqual(second.returncode,0,second.stderr)
        changed=json.loads((self.target/".opencode/opencode.jsonc").read_text()); self.assertGreater(changed["agents"]["owner"]["steps"],config["agents"]["owner"]["steps"])
        self.assertIn("steps: 56",(self.target/".opencode/agents/owner.md").read_text())

    def test_dry_run_writes_nothing(self):
        result=self.invoke("--action","dry-run","--profile","balanced"); self.assertEqual(result.returncode,0,result.stderr); self.assertIn("DRY RUN",result.stdout); self.assertEqual(list(self.target.iterdir()),[])

    def test_conflict_kept_then_backed_up_on_replace(self):
        path=self.target/".opencode/opencode.jsonc"; path.parent.mkdir(); path.write_text("user config")
        kept=self.invoke("--action","install","--profile","balanced"); self.assertEqual(kept.returncode,0); self.assertEqual(path.read_text(),"user config")
        replaced=self.invoke("--action","install","--profile","balanced","--replace"); self.assertEqual(replaced.returncode,0,replaced.stderr); self.assertNotEqual(path.read_text(),"user config")
        backups=list((self.target/".opencode/.bounded-orchestrator/backups").rglob("opencode.jsonc")); self.assertEqual(len(backups),1); self.assertEqual(backups[0].read_text(),"user config")

    def test_modified_file_is_preserved_on_uninstall(self):
        self.assertEqual(self.invoke("--action","install","--profile","balanced").returncode,0)
        role=self.target/".opencode/agents/explorer.md"; role.write_text(role.read_text()+"\nuser change\n")
        removed=self.invoke("--action","uninstall"); self.assertEqual(removed.returncode,0,removed.stderr); self.assertTrue(role.exists()); self.assertIn("KEEP .opencode/agents/explorer.md (modified)",removed.stdout); self.assertFalse((self.target/".opencode/agents/implementer.md").exists())

    def test_rejects_manifest_path_escape(self):
        runtime=self.target/".opencode/.bounded-orchestrator"; runtime.mkdir(parents=True)
        (runtime/"install.json").write_text(json.dumps({"schema":1,"files":{"../../outside":{"sha256":"0"*64}}}))
        result=self.invoke("--action","uninstall"); self.assertEqual(result.returncode,2); self.assertIn("unmanaged path",result.stderr)

    def test_all_profiles_have_distinct_finite_budgets(self):
        observed={}
        for profile in ("balanced","quality","economy","quota-saver"):
            result=self.invoke("--action","install","--profile",profile,"--replace"); self.assertEqual(result.returncode,0,result.stderr)
            observed[profile]=json.loads((self.target/".opencode/opencode.jsonc").read_text())["agents"]["owner"]["steps"]
        self.assertEqual(len(set(observed.values())),4); self.assertLess(observed["quota-saver"],observed["economy"]); self.assertLess(observed["balanced"],observed["quality"])

    def test_custom_exact_selectors_and_variant(self):
        result=self.invoke("--action","install","--profile","custom","--model","acme/base","--role-model","reviewer=acme/review#deep")
        self.assertEqual(result.returncode,0,result.stderr); config=json.loads((self.target/".opencode/opencode.jsonc").read_text()); self.assertEqual(config["model"],"acme/base"); self.assertEqual(config["agents"]["reviewer"]["model"],"acme/review#deep"); self.assertIn("model: acme/review#deep",(self.target/".opencode/agents/reviewer.md").read_text())

    def test_custom_rejects_injection_unknown_role_and_mixed_provider(self):
        for arguments in (("--model","a/model;touch-x"),("--role-model","missing=a/model"),("--model","a/base","--role-model","reviewer=b/review")):
            result=self.invoke("--action","install","--profile","custom",*arguments); self.assertEqual(result.returncode,2); self.assertFalse((self.target/".opencode/opencode.jsonc").exists())

    def test_bundled_profiles_reject_model_overrides(self):
        result=self.invoke("--action","install","--profile","balanced","--model","a/base")
        self.assertEqual(result.returncode,2); self.assertIn("custom profile",result.stderr)

    def test_mixed_provider_requires_explicit_gate(self):
        result=self.invoke("--action","install","--profile","custom","--model","a/base","--role-model","reviewer=b/review","--allow-mixed-providers")
        self.assertEqual(result.returncode,0,result.stderr)

    def test_platform_wrappers_exist_and_reference_installer(self):
        for path in (ROOT/"setup.command",ROOT/"setup.ps1",ROOT/"setup.cmd",ROOT/"scripts/install.sh",ROOT/"scripts/install.ps1"):
            self.assertTrue(path.is_file(),path)
        self.assertIn("install.py",(ROOT/"scripts/install.sh").read_text())
        self.assertIn("setup.ps1",(ROOT/"setup.cmd").read_text())

    @unittest.skipIf(os.name == "nt", "Windows symlink creation needs elevated privileges")
    def test_rejects_symlinked_managed_parent(self):
        outside=Path(self.tmp.name)/"outside"; outside.mkdir(); (self.target/".opencode").symlink_to(outside, target_is_directory=True)
        result=self.invoke("--action","install","--profile","balanced")
        self.assertEqual(result.returncode,2); self.assertIn("symlinked parent",result.stderr); self.assertEqual(list(outside.iterdir()),[])


if __name__=="__main__": unittest.main()
