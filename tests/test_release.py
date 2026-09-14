from __future__ import annotations
import importlib.util, tempfile, unittest, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]; BUILD=ROOT/"scripts/build_release.py"


def load():
    spec=importlib.util.spec_from_file_location("release_builder",BUILD); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


class ReleaseTests(unittest.TestCase):
    def test_builds_three_archives_checksums_and_excludes_private_runtime(self):
        runtime=ROOT/".opencode/.bounded-orchestrator/backups/private"; runtime.mkdir(parents=True,exist_ok=True); secret=runtime/"secret.txt"; secret.write_text("private")
        candidate=ROOT/".opencode/.candidate/candidate.json"; candidate.write_text('{"private":true}')
        pyc=ROOT/"tests/junk.pyc"; pyc.write_bytes(b"junk")
        try:
            with tempfile.TemporaryDirectory() as temporary:
                result=load().build(Path(temporary)); self.assertEqual(set(result["artifacts"]),{"source","macos-linux","windows"}); self.assertTrue(Path(result["checksums"]).is_file())
                for item in result["artifacts"].values():
                    path=Path(item["path"]); self.assertTrue(path.is_file())
                    with zipfile.ZipFile(path) as archive:
                        names=archive.namelist(); self.assertFalse(any("/.git/" in n or n.endswith(".pyc") or "/backups/" in n or n.endswith("candidate.json") for n in names)); self.assertTrue(any(n.endswith(".opencode/.bounded-orchestrator/.gitignore") for n in names))
                        notice=archive.read(next(name for name in names if name.endswith("/NOTICE"))).decode()
                        self.assertIn("codex-astra-luna-orchestrator",notice); self.assertIn("donvito",notice); self.assertIn("https://github.com/donvito/codex-astra-luna-orchestrator",notice); self.assertIn("Apache License, Version 2.0",notice); self.assertIn("not affiliated with or endorsed",notice)
        finally:
            if secret.exists(): secret.unlink()
            if runtime.exists(): runtime.rmdir()
            parent=runtime.parent
            if parent.exists() and not any(parent.iterdir()): parent.rmdir()
            if candidate.exists(): candidate.unlink()
            if pyc.exists(): pyc.unlink()


if __name__=="__main__": unittest.main()
