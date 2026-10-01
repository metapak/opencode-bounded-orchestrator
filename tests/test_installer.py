from __future__ import annotations

import json, os, subprocess, sys, tempfile, unittest
from unittest.mock import patch
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
        self.assertNotIn("steps:",(self.target/".opencode/agents/owner.md").read_text())

    def test_private_ignore_sentinel_is_canonical_after_crlf_source_checkout(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        source=ROOT/'.opencode/.bounded-orchestrator/.gitignore';original=Path.read_bytes
        def crlf_source(path):
            if path==source:return b'*\r\n!.gitignore\r\n'
            return original(path)
        with patch.object(Path,'read_bytes',crlf_source):
            install.install(self.target,'balanced',False,False,None,{},False)
        sentinel=self.target/'.opencode/.bounded-orchestrator/.gitignore'
        self.assertEqual(sentinel.read_bytes(),b'*\n!.gitignore\n')

    def test_installed_console_launcher_and_managed_uninstall(self):
        self.assertEqual(self.invoke("--action","install","--profile","balanced").returncode,0)
        for name in ("console.py","console.html","console.js","console.css"):
            self.assertTrue((self.target/".opencode/tools"/name).is_file())
        process=subprocess.Popen([sys.executable,str(self.target/".opencode/tools/console.py"),"--root",str(self.target),"--no-browser"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        try:
            line=process.stdout.readline(); self.assertIn("http://127.0.0.1:",line)
            from urllib.request import urlopen
            with urlopen(line.strip().split("console: ")[1].split("/#")[0]) as page:
                self.assertIn('charset=utf-8',page.headers.get('Content-Type','').lower())
                self.assertIn(b'\xc3\x87al\xc4\xb1\xc5\x9fmalar',page.read())
        finally:
            process.terminate(); process.communicate(timeout=5)
        result=self.invoke("--action","uninstall"); self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.target/".opencode/tools/console.py").exists())

    def test_root_variant_rejected_role_slash_model_supported(self):
        self.assertEqual(self.invoke("--action","install","--profile","custom","--model","acme/base#high").returncode,2)
        result=self.invoke("--action","install","--profile","custom","--model","acme/base","--role-model","reviewer=acme/vendor/model#high"); self.assertEqual(result.returncode,0,result.stderr)

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
        removed=self.invoke("--action","uninstall"); self.assertEqual(removed.returncode,0,removed.stderr); self.assertTrue(role.exists()); self.assertIn(f"KEEP {Path('.opencode/agents/explorer.md')} (modified)",removed.stdout); self.assertFalse((self.target/".opencode/agents/implementer.md").exists())

    def test_uninstall_preserves_user_edit_inside_agents_block(self):
        self.assertEqual(self.invoke("--action","install","--profile","balanced").returncode,0)
        agents=self.target/'AGENTS.md';edited=agents.read_text().replace('<!-- opencode-bounded-orchestrator:end -->','User note inside managed block.\n<!-- opencode-bounded-orchestrator:end -->')
        agents.write_text(edited)
        sys.path.insert(0,str(ROOT/'scripts'));import install
        self.assertIn('KEEP AGENTS.md managed block (modified)',install.uninstall(self.target,True))
        removed=self.invoke('--action','uninstall')
        self.assertEqual(removed.returncode,0,removed.stderr)
        self.assertIn('KEEP AGENTS.md managed block (modified)',removed.stdout)
        self.assertEqual(agents.read_text(),edited)
        self.assertFalse((self.target/install.MANIFEST).exists())

    def test_uninstall_removes_only_original_agents_block(self):
        agents=self.target/'AGENTS.md';prefix='User intro  \n\n';suffix='\n\nUser outro  \n'
        agents.write_text(prefix)
        self.assertEqual(self.invoke('--action','install','--profile','balanced').returncode,0)
        installed=agents.read_text();agents.write_text(installed+suffix)
        sys.path.insert(0,str(ROOT/'scripts'));import install
        block=installed[installed.index(install.START):installed.index(install.END)+len(install.END)]
        expected=(installed+suffix).replace(block,'',1)
        result=self.invoke('--action','uninstall')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('REMOVE AGENTS.md managed block',result.stdout)
        self.assertEqual(agents.read_text(),expected)

    def test_uninstall_restores_exact_original_agents_format_when_untouched(self):
        agents=self.target/'AGENTS.md';original=b'My original project instructions\r\n'
        agents.write_bytes(original)
        self.assertEqual(self.invoke('--action','install','--profile','balanced').returncode,0)
        self.assertEqual(self.invoke('--action','uninstall').returncode,0)
        self.assertEqual(agents.read_bytes(),original)

    def test_uninstall_preserves_mixed_line_endings_outside_agents_block(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        install.install(self.target,'balanced',False,False,None,{},False)
        agents=self.target/'AGENTS.md';original=agents.read_bytes()
        start=original.index(install.START.encode());end=original.index(install.END.encode())+len(install.END)
        block=original[start:end]
        prefix=b'User CRLF\r\nUser LF\n\r\n';suffix=b'\r\nUser tail\r\n'
        agents.write_bytes(prefix+block+suffix)
        actions=install.uninstall(self.target,False)
        self.assertIn('REMOVE AGENTS.md managed block',actions)
        self.assertEqual(agents.read_bytes(),prefix+suffix)

    def test_uninstall_rejects_agents_edit_after_snapshot(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        install.install(self.target,'balanced',False,False,None,{},False)
        agents=self.target/'AGENTS.md';managed=self.target/'.opencode/opencode.jsonc';manifest=self.target/install.MANIFEST
        original=Path.read_bytes;original_managed=managed.read_bytes();changed=False
        def edit_after_read(path):
            nonlocal changed
            data=original(path)
            if path==agents and not changed:
                changed=True;path.write_bytes(data+b'User edit after snapshot\r\n')
            return data
        with patch.object(Path,'read_bytes',edit_after_read):
            with self.assertRaisesRegex(install.InstallError,'Path changed during uninstall: AGENTS.md'):
                install.uninstall(self.target,False)
        self.assertIn(b'User edit after snapshot\r\n',agents.read_bytes())
        self.assertEqual(managed.read_bytes(),original_managed)
        self.assertTrue(manifest.exists())

    def test_uninstall_failure_restores_removed_files_and_agents_block(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        install.install(self.target,'balanced',False,False,None,{},False)
        first=self.target/'.opencode/opencode.jsonc';second=self.target/'.opencode/bounded-orchestrator.eval.example.json'
        agents=self.target/'AGENTS.md';manifest=self.target/install.MANIFEST
        before=(first.read_bytes(),second.read_bytes(),agents.read_bytes(),manifest.read_bytes())
        original=install.os.rename
        def fail_second(source,destination,*args,**kwargs):
            if source==second.name: raise OSError('simulated stage failure')
            return original(source,destination,*args,**kwargs)
        with patch.object(install.os,'rename',fail_second):
            with self.assertRaisesRegex(OSError,'simulated stage failure'):
                install.uninstall(self.target,False)
        self.assertEqual((first.read_bytes(),second.read_bytes(),agents.read_bytes(),manifest.read_bytes()),before)

    def test_uninstall_rollback_keeps_edit_to_new_agents_file(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        install.install(self.target,'balanced',False,False,None,{},False)
        agents=self.target/'AGENTS.md';original_agents=agents.read_bytes()
        managed=self.target/'.opencode/opencode.jsonc';original_managed=managed.read_bytes()
        manifest=self.target/install.MANIFEST;rename=install.os.rename;injected=False
        def edit_then_fail_manifest(source,destination,*args,**kwargs):
            nonlocal injected
            if source==manifest.name and not injected:
                injected=True;agents.write_bytes(agents.read_bytes()+b'User edit during uninstall\n')
                raise OSError('simulated manifest stage failure')
            return rename(source,destination,*args,**kwargs)
        with patch.object(install.os,'rename',edit_then_fail_manifest):
            with self.assertRaisesRegex(install.InstallError,'rollback incomplete'):
                install.uninstall(self.target,False)
        self.assertTrue(injected)
        self.assertIn(b'User edit during uninstall\n',agents.read_bytes())
        self.assertEqual(managed.read_bytes(),original_managed)
        self.assertTrue(manifest.exists())
        staged=list((self.target/install.BACKUPS.parent).glob('uninstall-*/file-*'))
        self.assertIn(original_agents,[path.read_bytes() for path in staged])

    @unittest.skipIf(os.name == 'nt', 'Directory-fd staging is POSIX-only')
    def test_uninstall_rollback_does_not_replace_new_managed_file(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        install.install(self.target,'balanced',False,False,None,{},False)
        owner=self.target/'.opencode/agents/advisor.md';original_owner=owner.read_bytes()
        explorer=self.target/'.opencode/agents/explorer.md';manifest=self.target/install.MANIFEST
        rename=install.os.rename;link=install.os.link;injected=False
        def fail_explorer(source,destination,*args,**kwargs):
            if source==explorer.name: raise OSError('simulated stage failure')
            return rename(source,destination,*args,**kwargs)
        def collide_at_restore(source,destination,*args,**kwargs):
            nonlocal injected
            if destination==owner.name and not injected:
                injected=True;owner.write_bytes(b'concurrent user file\n')
            return link(source,destination,*args,**kwargs)
        with patch.object(install.os,'rename',fail_explorer),patch.object(install.os,'link',collide_at_restore):
            with self.assertRaisesRegex(install.InstallError,'rollback incomplete'):
                install.uninstall(self.target,False)
        self.assertTrue(injected)
        self.assertEqual(owner.read_bytes(),b'concurrent user file\n')
        self.assertTrue(manifest.exists())
        recovery=list((self.target/install.BACKUPS.parent).glob('uninstall-recovery-*/file-*'))
        self.assertIn(original_owner,[path.read_bytes() for path in recovery])

    @unittest.skipIf(os.name == 'nt', 'Directory-fd staging is POSIX-only')
    def test_uninstall_rollback_does_not_replace_new_agents_file(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        install.install(self.target,'balanced',False,False,None,{},False)
        agents=self.target/'AGENTS.md';original_agents=agents.read_bytes();manifest=self.target/install.MANIFEST
        rename=install.os.rename;link=install.os.link;edited=b'User edit to cleaned AGENTS.md\n';injected=False
        def edit_then_fail_manifest(source,destination,*args,**kwargs):
            if source==manifest.name:
                agents.write_bytes(agents.read_bytes()+edited)
                raise OSError('simulated manifest failure')
            return rename(source,destination,*args,**kwargs)
        def collide_at_restore(source,destination,*args,**kwargs):
            nonlocal injected
            if source.startswith('created-') and destination==agents.name and not injected:
                injected=True;agents.write_bytes(b'new concurrent AGENTS.md\n')
            return link(source,destination,*args,**kwargs)
        with patch.object(install.os,'rename',edit_then_fail_manifest),patch.object(install.os,'link',collide_at_restore):
            with self.assertRaisesRegex(install.InstallError,'rollback incomplete'):
                install.uninstall(self.target,False)
        self.assertTrue(injected)
        self.assertEqual(agents.read_bytes(),b'new concurrent AGENTS.md\n')
        self.assertTrue(manifest.exists())
        recovery=list((self.target/install.BACKUPS.parent).glob('uninstall-recovery-*/*'))
        recovered=[path.read_bytes() for path in recovery if path.is_file()]
        self.assertIn(original_agents,recovered)
        self.assertTrue(any(edited in data for data in recovered))

    @unittest.skipIf(os.name == 'nt', 'Directory-fd staging is POSIX-only')
    def test_uninstall_retains_open_inode_edit_after_validation(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        install.install(self.target,'balanced',False,False,None,{},False)
        managed=self.target/'.opencode/opencode.jsonc';manifest=self.target/install.MANIFEST
        fd=os.open(managed,os.O_RDWR);rename=install.os.rename;injected=False
        def edit_staged_inode(source,destination,*args,**kwargs):
            nonlocal injected
            if source==manifest.name and not injected:
                injected=True;os.lseek(fd,0,os.SEEK_END);os.write(fd,b'\nUser edit through open handle\n')
            return rename(source,destination,*args,**kwargs)
        try:
            with patch.object(install.os,'rename',edit_staged_inode):
                install.uninstall(self.target,False)
        finally: os.close(fd)
        self.assertTrue(injected)
        self.assertFalse(managed.exists());self.assertFalse(manifest.exists())
        recovery=list((self.target/install.BACKUPS.parent).glob('uninstall-recovery-*/file-*'))
        self.assertTrue(any(b'User edit through open handle' in path.read_bytes() for path in recovery))

    def test_uninstall_rechecks_managed_file_before_first_removal(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        install.install(self.target,'balanced',False,False,None,{},False)
        first=self.target/'.opencode/opencode.jsonc';manifest=self.target/install.MANIFEST
        original=install.os.rename;changed=False
        def edit_before_stage(source,destination,*args,**kwargs):
            nonlocal changed
            if source==first.name and not changed:
                changed=True;first.write_bytes(first.read_bytes()+b'\nuser change\n')
            return original(source,destination,*args,**kwargs)
        with patch.object(install.os,'rename',edit_before_stage):
            with self.assertRaisesRegex(install.InstallError,'Path changed during uninstall'):
                install.uninstall(self.target,False)
        self.assertIn(b'user change',first.read_bytes())
        self.assertTrue(manifest.exists())
        self.assertTrue((self.target/'.opencode/agents/owner.md').exists())

    @unittest.skipIf(os.name == 'nt', 'Directory-fd staging is POSIX-only')
    def test_uninstall_parent_swap_never_removes_outside_file(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        install.install(self.target,'balanced',False,False,None,{},False)
        agents_dir=self.target/'.opencode/agents';moved=self.target/'.opencode/agents-moved'
        outside=Path(self.tmp.name)/'outside-agents';outside.mkdir()
        outside_owner=outside/'owner.md';outside_owner.write_text('unrelated outside user file')
        manifest=self.target/install.MANIFEST;original=install.os.rename;swapped=False
        def swap_before_stage(source,destination,*args,**kwargs):
            nonlocal swapped
            if source=='owner.md' and not swapped:
                swapped=True;agents_dir.rename(moved);agents_dir.symlink_to(outside,target_is_directory=True)
            return original(source,destination,*args,**kwargs)
        with patch.object(install.os,'rename',swap_before_stage):
            with self.assertRaises((OSError,install.InstallError)):
                install.uninstall(self.target,False)
        self.assertEqual(outside_owner.read_text(),'unrelated outside user file')
        self.assertTrue(manifest.exists())
        self.assertTrue((moved/'owner.md').exists())

    def test_rejects_manifest_path_escape(self):
        runtime=self.target/".opencode/.bounded-orchestrator"; runtime.mkdir(parents=True)
        (runtime/"install.json").write_text(json.dumps({"schema":1,"files":{"../../outside":{"sha256":"0"*64}}}))
        result=self.invoke("--action","uninstall"); self.assertEqual(result.returncode,2); self.assertIn("unmanaged path",result.stderr)

    @unittest.skipIf(os.name == 'nt', 'Windows symlink creation needs elevated privileges')
    def test_symlinked_manifest_leaf_rejected_before_dry_run_or_install(self):
        outside=Path(self.tmp.name)/'outside.json';outside.write_text(json.dumps({'schema':1,'files':{}}))
        runtime=self.target/'.opencode/.bounded-orchestrator';runtime.mkdir(parents=True)
        (runtime/'install.json').symlink_to(outside)
        original=outside.read_bytes()
        for action in ('dry-run','install'):
            result=self.invoke('--action',action,'--profile','balanced')
            self.assertEqual(result.returncode,2,result.stdout)
            self.assertIn('unsafe install manifest',result.stderr)
            self.assertEqual(outside.read_bytes(),original)
            self.assertFalse((self.target/'.opencode/opencode.jsonc').exists())

    def test_all_profiles_have_distinct_finite_budgets(self):
        observed={}
        for profile in ("balanced","quality","economy","quota-saver"):
            result=self.invoke("--action","install","--profile",profile,"--replace"); self.assertEqual(result.returncode,0,result.stderr)
            observed[profile]=json.loads((self.target/".opencode/opencode.jsonc").read_text())["agents"]["owner"]["steps"]
        self.assertEqual(len(set(observed.values())),4); self.assertLess(observed["quota-saver"],observed["economy"]); self.assertLess(observed["balanced"],observed["quality"])

    def test_custom_exact_selectors_and_variant(self):
        result=self.invoke("--action","install","--profile","custom","--model","acme/base","--role-model","reviewer=acme/review#deep")
        self.assertEqual(result.returncode,0,result.stderr); config=json.loads((self.target/".opencode/opencode.jsonc").read_text()); self.assertEqual(config["model"],"acme/base"); self.assertEqual(config["agents"]["reviewer"]["model"],"acme/review#deep"); self.assertNotIn("model:",(self.target/".opencode/agents/reviewer.md").read_text())

    def test_role_only_override_requires_unknown_inherited_provider_gate(self):
        rejected=self.invoke("--action","install","--profile","custom","--role-model","reviewer=acme/review")
        self.assertEqual(rejected.returncode,2); self.assertIn("unknown inherited default provider",rejected.stderr)
        accepted=self.invoke("--action","install","--profile","custom","--role-model","reviewer=acme/review","--allow-mixed-providers")
        self.assertEqual(accepted.returncode,0,accepted.stderr)

    def test_custom_rejects_injection_unknown_role_and_mixed_provider(self):
        for arguments in (("--model","a/model;touch-x"),("--role-model","missing=a/model"),("--model","a/base","--role-model","reviewer=b/review")):
            result=self.invoke("--action","install","--profile","custom",*arguments); self.assertEqual(result.returncode,2); self.assertFalse((self.target/".opencode/opencode.jsonc").exists())

    def test_bundled_profiles_reject_model_overrides(self):
        result=self.invoke("--action","install","--profile","balanced","--model","a/base")
        self.assertEqual(result.returncode,2); self.assertIn("custom profile",result.stderr)

    def test_mixed_provider_requires_explicit_gate(self):
        result=self.invoke("--action","install","--profile","custom","--model","a/base","--role-model","reviewer=b/review","--allow-mixed-providers")
        self.assertEqual(result.returncode,0,result.stderr)

    def test_team_slots_are_distinct_owned_agents_and_uninstall_safely(self):
        sys.path.insert(0,str(ROOT/"scripts"))
        import install
        team=[{"role":"researcher","model":"acme/research#high","duty":"Find current evidence"},{"role":"researcher","model":"acme/research#low","duty":"Check sources"},{"role":"implementer","model":"acme/build","duty":"Write scoped code"}]
        dry=install.install(self.target,"balanced",False,True,"acme/base",{},False,team)
        self.assertEqual(list(self.target.iterdir()),[])
        self.assertIn(f"INSTALL {Path('.opencode/agents/helper-03.md')}",dry)
        install.install(self.target,"balanced",False,False,"acme/base",{},False,team)
        config=json.loads((self.target/".opencode/opencode.jsonc").read_text())
        owner=config["agents"]["owner"]["permissions"]
        allows=[rule["resource"] for rule in owner if rule["action"]=="subagent" and rule["effect"]=="allow"]
        self.assertEqual(allows,["helper-01","helper-02","helper-03"])
        self.assertEqual(config["agents"]["helper-01"]["model"],"acme/research#high")
        self.assertEqual(config["agents"]["helper-02"]["model"],"acme/research#low")
        self.assertEqual(config["agents"]["helper-01"]["permissions"][-1],{"action":"subagent","resource":"*","effect":"deny"})
        self.assertIn("Find current evidence",(self.target/".opencode/agents/helper-01.md").read_text())
        install.install(self.target,"balanced",True,False,"acme/base",{},False,team[:1])
        self.assertFalse((self.target/".opencode/agents/helper-02.md").exists())
        self.assertFalse((self.target/".opencode/agents/helper-03.md").exists())
        install.uninstall(self.target,False)
        self.assertFalse((self.target/".opencode/agents/helper-01.md").exists())

    def test_fifty_planned_slots_install_shrink_and_uninstall(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        team=[{'role':'researcher' if i%2 else 'implementer','model':'','duty':f'Scope {i:02d}'} for i in range(1,51)]
        self.assertEqual(len(install.validate_team(team)),50)
        with self.assertRaises(install.InstallError):install.validate_team(team+[team[0]])
        install.install(self.target,'balanced',False,False,None,{},False,team)
        config=json.loads((self.target/'.opencode/opencode.jsonc').read_text())
        allows=[r['resource'] for r in config['agents']['owner']['permissions'] if r['action']=='subagent' and r['effect']=='allow']
        self.assertEqual(allows,[f'helper-{i:02d}' for i in range(1,51)])
        self.assertTrue((self.target/'.opencode/agents/helper-50.md').exists())
        install.install(self.target,'quality',False,False,None,{},False,team[:1])
        self.assertFalse((self.target/'.opencode/agents/helper-50.md').exists())
        self.assertTrue(list((self.target/'.opencode/.bounded-orchestrator/backups').rglob('helper-50.md')))
        install.uninstall(self.target,False)
        self.assertFalse((self.target/'.opencode/agents/helper-01.md').exists())

    def test_install_mid_write_failure_restores_active_files(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        team=[{'role':'researcher','model':'','duty':'First'}]
        install.install(self.target,'balanced',False,False,None,{},False,team)
        paths=[self.target/'.opencode/opencode.jsonc',self.target/'.opencode/agents/owner.md',self.target/'.opencode/agents/helper-01.md',self.target/'.opencode/.bounded-orchestrator/install.json']
        before=[path.read_bytes() for path in paths]
        original=install.atomic_bytes
        def fail_once(path,data):
            if path==self.target/'.opencode/agents/helper-02.md':
                raise OSError('injected write failure')
            return original(path,data)
        with patch.object(install,'atomic_bytes',side_effect=fail_once):
            with self.assertRaises(OSError):install.install(self.target,'quality',False,False,None,{},False,team+[{'role':'verifier','model':'','duty':'Second'}])
        self.assertEqual([path.read_bytes() for path in paths],before)
        self.assertFalse((self.target/'.opencode/agents/helper-02.md').exists())

    def test_concurrent_new_helper_is_never_overwritten_or_removed(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        helper=self.target/'.opencode/agents/helper-01.md'
        sentinel=self.target/'.opencode/.bounded-orchestrator/.gitignore'
        original=install.atomic_bytes
        def create_external_after_sentinel(path,data):
            original(path,data)
            if path==sentinel:helper.parent.mkdir(parents=True,exist_ok=True);helper.write_text('USER-SENTINEL')
        with patch.object(install,'atomic_bytes',side_effect=create_external_after_sentinel):
            with self.assertRaises(install.InstallError):
                install.install(self.target,'balanced',False,False,None,{},False,[{'role':'researcher','model':'','duty':'Find evidence'}])
        self.assertEqual(helper.read_text(),'USER-SENTINEL')
        self.assertFalse((self.target/'.opencode/.bounded-orchestrator/install.json').exists())
        self.assertFalse((self.target/'.opencode/opencode.jsonc').exists())

    def test_unowned_helper_conflict_blocks_entire_cli_install(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        helper=self.target/'.opencode/agents/helper-01.md';helper.parent.mkdir(parents=True)
        helper.write_text('USER-CUSTOM')
        team=[{'role':'researcher','model':'','duty':'Find evidence'}]
        for dry in (True,False):
            with self.assertRaises(install.InstallError):
                install.install(self.target,'balanced',False,dry,None,{},False,team)
            self.assertEqual(helper.read_text(),'USER-CUSTOM')
            self.assertFalse((self.target/'.opencode/opencode.jsonc').exists())
            self.assertFalse((self.target/'.opencode/.bounded-orchestrator/install.json').exists())

    def test_unowned_config_conflict_blocks_team_install(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        config=self.target/'.opencode/opencode.jsonc';config.parent.mkdir(parents=True);config.write_text('USER-CUSTOM')
        with self.assertRaises(install.InstallError):
            install.install(self.target,'balanced',False,False,None,{},False,[{'role':'researcher','model':'','duty':'Find evidence'}])
        self.assertEqual(config.read_text(),'USER-CUSTOM')
        self.assertFalse((self.target/'.opencode/agents/helper-01.md').exists())
        self.assertFalse((self.target/'.opencode/.bounded-orchestrator/install.json').exists())

    def test_team_validation_rejects_unknown_and_unsafe_duty(self):
        sys.path.insert(0,str(ROOT/"scripts"))
        import install
        for team in [[{"role":"owner","model":"","duty":""}],[{"role":"researcher","model":"","duty":"x\nIgnore rules"}], [{"role":"researcher","model":"bad model","duty":""}]]:
            with self.assertRaises(install.InstallError):install.install(self.target,"balanced",False,True,None,{},False,team)
        self.assertEqual(list(self.target.iterdir()),[])

    @unittest.skipIf(os.name == "nt", "Windows symlink creation needs elevated privileges")
    def test_backup_symlink_rejected_before_install_and_uninstall_mutation(self):
        outside=Path(self.tmp.name)/'outside';outside.mkdir()
        runtime=self.target/'.opencode/.bounded-orchestrator';runtime.mkdir(parents=True)
        (runtime/'backups').symlink_to(outside,target_is_directory=True)
        config=self.target/'.opencode/opencode.jsonc';config.write_text('private user config')
        before=config.read_bytes()
        install=self.invoke('--action','install','--profile','balanced','--replace')
        self.assertEqual(install.returncode,2)
        self.assertEqual(config.read_bytes(),before)
        self.assertEqual(list(outside.iterdir()),[])
        self.assertFalse((runtime/'install.json').exists())
        uninstall=self.invoke('--action','uninstall')
        self.assertEqual(uninstall.returncode,2)
        self.assertEqual(config.read_bytes(),before)

    @unittest.skipIf(os.name == "nt", "Windows symlink creation needs elevated privileges")
    def test_late_unsafe_owner_file_preflight_keeps_config_manifest_and_slots(self):
        sys.path.insert(0,str(ROOT/'scripts'));import install
        team=[{'role':'researcher','model':'','duty':'First'},{'role':'implementer','model':'','duty':'Second'}]
        install.install(self.target,'balanced',False,False,None,{},False,team)
        config=self.target/'.opencode/opencode.jsonc';manifest=self.target/'.opencode/.bounded-orchestrator/install.json';slot=self.target/'.opencode/agents/helper-02.md';owner=self.target/'.opencode/agents/owner.md'
        outside=Path(self.tmp.name)/'outside.md';outside.write_text('outside')
        owner.unlink();owner.symlink_to(outside)
        before=(config.read_bytes(),manifest.read_bytes(),slot.read_bytes())
        with self.assertRaises(install.InstallError):install.install(self.target,'balanced',True,False,None,{},False,team[:1])
        self.assertEqual(before,(config.read_bytes(),manifest.read_bytes(),slot.read_bytes()))
        self.assertEqual(outside.read_text(),'outside')

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

    def test_uninstall_keeps_ignore_sentinels_for_backups_and_runtime_state(self):
        subprocess.run(["git","init","-q",str(self.target)],check=True)
        self.assertEqual(self.invoke("--action","install","--profile","balanced").returncode,0)
        config=self.target/".opencode/opencode.jsonc"; config.write_text(config.read_text()+"\n")
        self.assertEqual(self.invoke("--action","install","--profile","balanced","--replace").returncode,0)
        runtime=self.target/".opencode/.bounded-orchestrator"
        data=[runtime/"runs/run.json",runtime/"evals/unit.json",runtime/"current.json",self.target/".opencode/.candidate/candidate.json"]
        for path in data: path.parent.mkdir(parents=True,exist_ok=True); path.write_text("{}\n")
        backups=list((runtime/"backups").rglob("opencode.jsonc")); self.assertTrue(backups)
        subprocess.run(["git","-C",str(self.target),"add",".opencode/.bounded-orchestrator/.gitignore",".opencode/.candidate/.gitignore"],check=True)
        subprocess.run(["git","-C",str(self.target),"-c","user.name=Test","-c","user.email=t@example.invalid","commit","-qm","ignore sentinels"],check=True)
        result=self.invoke("--action","uninstall"); self.assertEqual(result.returncode,0,result.stderr)
        for sentinel in (runtime/".gitignore",self.target/".opencode/.candidate/.gitignore"):
            self.assertTrue(sentinel.is_file()); self.assertEqual(sentinel.read_text(),"*\n!.gitignore\n")
        for path in [*data,*backups]:
            self.assertTrue(path.exists(),path)
            ignored=subprocess.run(["git","-C",str(self.target),"check-ignore","-q",str(path)],check=False)
            self.assertEqual(ignored.returncode,0,path)
        status=subprocess.run(["git","-C",str(self.target),"status","--porcelain","--untracked-files=all"],text=True,capture_output=True,check=True).stdout
        for path in [*data,*backups]: self.assertNotIn(path.name,status)


if __name__=="__main__": unittest.main()
