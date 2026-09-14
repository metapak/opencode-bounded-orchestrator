from __future__ import annotations

import importlib.util, json, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]; USAGE=ROOT/".opencode/tools/usage_report.py"; EVAL=ROOT/".opencode/tools/local_eval.py"


def module(path,name):
    spec=importlib.util.spec_from_file_location(name,path); loaded=importlib.util.module_from_spec(spec); spec.loader.exec_module(loaded); return loaded


class UsageEvalTests(unittest.TestCase):
    def test_usage_reports_verified_json_without_inference(self):
        usage=module(USAGE,"usage_report_ok"); result=subprocess.CompletedProcess([],0,'{"sessions":2,"tokens":{"input":12}}','')
        with patch.object(usage.shutil,"which",return_value="/usr/bin/opencode"), patch.object(usage.subprocess,"run",return_value=result): report=usage.collect()
        self.assertEqual(report["reported"]["tokens"]["input"],12); self.assertNotIn("estimated",json.dumps(report).lower())

    def test_usage_fails_clearly_when_cli_or_json_unavailable(self):
        usage=module(USAGE,"usage_report_fail")
        with patch.object(usage.shutil,"which",return_value=None):
            with self.assertRaises(usage.UsageError): usage.collect()
        result=subprocess.CompletedProcess([],0,"not-json","")
        with patch.object(usage.shutil,"which",return_value="opencode"), patch.object(usage.subprocess,"run",return_value=result):
            with self.assertRaises(usage.UsageError): usage.collect()

    def test_local_eval_pass_and_candidate_staleness(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo=Path(temporary); subprocess.run(["git","init","-q",str(repo)],check=True)
            (repo/"tracked.txt").write_text("one"); subprocess.run(["git","-C",str(repo),"add","."] ,check=True); subprocess.run(["git","-C",str(repo),"-c","user.name=Test","-c","user.email=t@example.invalid","commit","-qm","init"],check=True)
            manifest=repo/"eval.json"; manifest.write_text(json.dumps({"label":"unit","argv":[sys.executable,"-c","print('ok')"],"timeout_seconds":10}))
            result=subprocess.run([sys.executable,str(EVAL),"--root",str(repo),"--json",str(manifest)],text=True,capture_output=True,check=False); self.assertEqual(result.returncode,0,result.stderr); payload=json.loads(result.stdout); self.assertEqual(payload["outcome"],"pass")
            (repo/"tracked.txt").write_text("two"); current=module(EVAL,"eval_mod").candidate_fingerprint(repo); self.assertNotEqual(current,payload["candidate_fingerprint"])

    def test_local_eval_rejects_shell_string_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo=Path(temporary); subprocess.run(["git","init","-q",str(repo)],check=True); manifest=repo/"eval.json"; manifest.write_text(json.dumps({"label":"bad","argv":"echo ok"}))
            result=subprocess.run([sys.executable,str(EVAL),"--root",str(repo),str(manifest)],text=True,capture_output=True,check=False); self.assertEqual(result.returncode,2); self.assertIn("argv",result.stderr)


if __name__=="__main__": unittest.main()
