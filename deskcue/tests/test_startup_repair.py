"""The real repair entry is exercised only with an in-memory task store.

No test calls the default Task Scheduler operations or the integration probe.
"""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
COMMON = Path(subprocess.check_output(
    ["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
    text=True).strip()).parent
SCRIPT = ROOT / "tools/Repair-DeskCueStartup.ps1"
SID = "S-1-5-21-111-222-333-500"
USER = "TEST\\小 café 日本語 😀"
LEGACY = "DeskCue-Logon-" + SID
CANONICAL = "DeskCue User Startup-" + SID
EXE = str(COMMON / "发布版/DeskCue.exe")
NS = "http://schemas.microsoft.com/windows/2004/02/mit/task"
ET.register_namespace("", NS)


def pinned_sdk_available():
    hosts = [COMMON / ".deskcue-tools/dotnet/dotnet.exe"]
    if os.environ.get("DOTNET_ROOT"):
        hosts.append(Path(os.environ["DOTNET_ROOT"]) / "dotnet.exe")
    if shutil.which("dotnet"):
        hosts.append(Path(shutil.which("dotnet")))
    return any(host.is_file() and (host.parent / "sdk/10.0.402").is_dir() for host in hosts)


def xml(*, canonical=False, **changes):
    # Fixtures deliberately differ from production generation; tests inject it.
    values = dict(source="DeskCue" if canonical else "DeskCue.LocalStartup.v1",
                  principal=SID, trigger=SID, command=EXE,
                  arguments="--startup --startup-source=scheduled-task" if canonical else "",
                  runlevel="LeastPrivilege", logon="InteractiveToken", enabled="true",
                  trigger_enabled="true", delay="", workdir="")
    values.update(changes)
    task = ET.Element(f"{{{NS}}}Task", version="1.4")
    def add(parent, name, value=None):
        node = ET.SubElement(parent, f"{{{NS}}}{name}")
        if value is not None:
            node.text = value
        return node
    reg = add(task, "RegistrationInfo")
    add(reg, "Source", values["source"])
    add(reg, "URI", "\\" + (CANONICAL if canonical else LEGACY))
    triggers = add(task, "Triggers")
    trigger = add(triggers, "LogonTrigger")
    add(trigger, "UserId", values["trigger"])
    if values["trigger_enabled"] is not None:
        add(trigger, "Enabled", values["trigger_enabled"])
    if values["delay"]:
        add(trigger, "Delay", values["delay"])
    principal = add(add(task, "Principals"), "Principal")
    add(principal, "UserId", values["principal"])
    add(principal, "LogonType", values["logon"])
    if values["runlevel"] is not None:
        add(principal, "RunLevel", values["runlevel"])
    settings = add(task, "Settings")
    if values["enabled"] is not None:
        add(settings, "Enabled", values["enabled"])
    action = add(add(task, "Actions"), "Exec")
    add(action, "Command", values["command"])
    add(action, "Arguments", values["arguments"])
    if values["workdir"]:
        add(action, "WorkingDirectory", values["workdir"])
    return ET.tostring(task, encoding="unicode")


HARNESS = r'''
param($ConfigPath, $ScriptPath)
$ErrorActionPreference = 'Stop'
$c = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json -AsHashtable
$state = @{ Tasks = @{}; Events = [Collections.Generic.List[string]]::new(); Counts = @{} }
foreach ($k in $c.tasks.Keys) { $state.Tasks[$k] = $c.tasks[$k] }
function Hook($operation, $name) {
    $short = if ($name -eq $c.legacy) { 'old' } else { 'new' }
    $key = "${operation}:$short"
    if (-not $state.Counts.ContainsKey($key)) { $state.Counts[$key] = 0 }
    $state.Counts[$key]++
    $event = "${key}:$($state.Counts[$key])"
    $state.Events.Add($event)
    if ($c.hooks.ContainsKey($event)) {
        $hook = $c.hooks[$event]
        if ($hook.ContainsKey('setOld')) { $state.Tasks[$c.legacy] = $hook.setOld }
        if ($hook.ContainsKey('setNew')) { $state.Tasks[$c.canonical] = $hook.setNew }
        if ($hook.ContainsKey('removeOld')) { $null = $state.Tasks.Remove($c.legacy) }
        if ($hook.ContainsKey('throw')) { throw $hook.throw }
        return $hook
    }
    return @{}
}
$ops = @{
    TaskQuery = { param($name)
        $hook = Hook 'query' $name
        if ($hook.ContainsKey('error')) { return @{ Status = 'Error'; Error = 'access denied' } }
        if ($hook.ContainsKey('missing')) { return @{ Status = 'Missing' } }
        if ($state.Tasks.ContainsKey($name)) { return @{ Status = 'Found'; Xml = $state.Tasks[$name] } }
        return @{ Status = 'Missing' }
    }
    TaskRegister = { param($name, $taskXml)
        $hook = Hook 'register' $name
        if ($state.Tasks.ContainsKey($name)) { throw 'create-only collision' }
        $state.Tasks[$name] = $taskXml
        if ($hook.ContainsKey('throwAfter')) { throw 'uncertain register completion' }
    }
    TaskDelete = { param($name)
        $hook = Hook 'delete' $name
        $null = $state.Tasks.Remove($name)
        if ($hook.ContainsKey('throwAfter')) { throw 'uncertain delete completion' }
    }
    ContractFactory = { param($exe, $sid)
        $state.Events.Add('contract')
        return @{ TaskName = $c.canonical; Xml = $c.contract; Arguments = '--startup --startup-source=scheduled-task' }
    }
    Validator = { param($name, $taskXml, $exe)
        $hook = Hook 'validate' $name
        return (-not $hook.ContainsKey('invalid'))
    }
    ProcessProbe = { param($exe)
        $state.Events.Add('process')
        if ($c.processError) { throw 'process lookup uncertain' }
        return $c.running
    }
}
$parameters = @{ Operations = $ops; CurrentUserSid = $c.sid; CurrentUserName = $c.user;
    EvidenceRoot = $c.evidence }
if ($c.apply) { $parameters.Apply = $true }
try { $result = & $ScriptPath @parameters }
catch { $result = @{ Status = 'Failed'; Reason = $_.Exception.Message } }
@{ Result = $result; Tasks = $state.Tasks; Events = @($state.Events) } | ConvertTo-Json -Depth 20 -Compress
'''


@unittest.skipUnless(os.name == "nt" and shutil.which("pwsh"), "requires PowerShell 7 on Windows")
class StartupRepairTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SCRIPT.is_file(), "explicit owned startup repair entry has not been implemented")
        scratch = COMMON / ".artifacts/elevation-controller/task2/tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)

    def run_case(self, *, old=None, new=None, absent=False, apply=True, hooks=None,
                 running=False, process_error=False, contract=None):
        tasks = {} if absent else {LEGACY: old or xml()}
        if new:
            tasks[CANONICAL] = new
        config = dict(tasks=tasks, legacy=LEGACY, canonical=CANONICAL, sid=SID, user=USER,
                      contract=contract or xml(canonical=True), hooks=hooks or {},
                      apply=apply, running=running, processError=process_error,
                      evidence=str(self.path / "evidence"))
        cfg = self.path / "case.json"
        cfg.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        harness = self.path / "harness.ps1"
        harness.write_text(HARNESS, encoding="utf-8")
        env = dict(os.environ, TEMP=str(self.path), TMP=str(self.path))
        process = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-File", str(harness),
                                  str(cfg), str(SCRIPT)], capture_output=True, text=True,
                                 encoding="utf-8", env=env, timeout=30)
        self.assertEqual(process.returncode, 0, process.stderr)
        try:
            return json.loads(process.stdout.strip())
        except ValueError:
            self.fail(process.stdout + process.stderr)

    def assert_untouched(self, value, old):
        self.assertEqual(value["Tasks"], {LEGACY: old})
        self.assertFalse(any(e.startswith(("register:", "delete:")) for e in value["Events"]))

    def test_preview_is_default_and_does_not_write_tasks_or_evidence(self):
        result = self.run_case(apply=False)
        self.assertEqual(result["Result"]["Status"], "Preview")
        self.assert_untouched(result, xml())
        self.assertFalse((self.path / "evidence").exists())

    def test_success_creates_validates_then_deletes_and_saves_backup_journal(self):
        result = self.run_case()
        self.assertEqual(result["Result"]["Status"], "Repaired", result)
        self.assertEqual(result["Tasks"], {CANONICAL: xml(canonical=True)})
        events = result["Events"]
        self.assertLess(events.index("register:new:1"), events.index("delete:old:1"))
        self.assertLess(events.index("validate:new:2"), events.index("delete:old:1"))
        journal = Path(result["Result"]["JournalPath"])
        evidence = json.loads(journal.read_text(encoding="utf-8-sig"))
        self.assertEqual(evidence["status"], "Repaired")
        self.assertIn("conditional", evidence["limitation"])
        self.assertEqual((journal.parent / "legacy.xml").read_text(encoding="utf-8-sig"), xml())
        self.assertEqual(len(evidence["legacySha256"]), 64)
        self.assertEqual(evidence["legacySha256"].lower(), hashlib.sha256(xml().encode("utf-8")).hexdigest())
        self.assertEqual(evidence["legacyFileSha256"].lower(), hashlib.sha256((journal.parent / "legacy.xml").read_bytes()).hexdigest())

    def test_defaults_username_unicode_and_zero_delay_are_owned(self):
        for extra in [dict(runlevel=None, enabled=None, trigger_enabled=None),
                      dict(principal=USER, trigger=USER, delay="PT0S", workdir=str(Path(EXE).parent))]:
            with self.subTest(extra=extra):
                value = self.run_case(old=xml(**extra))
                self.assertEqual(value["Result"]["Status"], "Repaired", value)

    def test_utf16_declared_recovery_files_are_readable_as_xml_and_preserve_text(self):
        declaration = '<?xml version="1.0" encoding="UTF-16"?>\r\n'
        old = declaration + xml()
        canonical = declaration + xml(canonical=True)
        value = self.run_case(old=old, contract=canonical)
        self.assertEqual(value["Result"]["Status"], "Repaired", value)
        journal = Path(value["Result"]["JournalPath"])
        evidence = json.loads(journal.read_text(encoding="utf-8-sig"))
        for name, original, prefix in [("legacy.xml", old, "legacy"), ("intended-canonical.xml", canonical, "intended"),
                                       ("canonical-readback.xml", canonical, "created")]:
            with self.subTest(name=name):
                path = journal.parent / name
                self.assertEqual(ET.parse(path).getroot().tag, f"{{{NS}}}Task")
                self.assertTrue(path.read_bytes().startswith(b"\xff\xfe"))
                self.assertEqual(path.read_bytes().decode("utf-16"), original)
                self.assertEqual(evidence[prefix + "Sha256"].lower(), hashlib.sha256(original.encode("utf-8")).hexdigest())
                self.assertEqual(evidence[prefix + "FileSha256"].lower(), hashlib.sha256(path.read_bytes()).hexdigest())

    def test_utf8_declared_recovery_file_preserves_text_and_encoding(self):
        old = "<?xml version='1.0' encoding='UTF-8'?>\n" + xml()
        value = self.run_case(old=old)
        self.assertEqual(value["Result"]["Status"], "Repaired", value)
        path = Path(value["Result"]["JournalPath"]).parent / "legacy.xml"
        self.assertEqual(ET.parse(path).getroot().tag, f"{{{NS}}}Task")
        self.assertEqual(path.read_bytes(), old.encode("utf-8"))

    def test_unsupported_recovery_encoding_fails_before_any_task_mutation(self):
        for encoding in ["UTF-32", "UTF-16BE", "Windows-1252"]:
            with self.subTest(encoding=encoding):
                old = f'<?xml version="1.0" encoding="{encoding}"?>' + xml()
                value = self.run_case(old=old)
                self.assertEqual(value["Result"]["Status"], "Failed", value)
                self.assert_untouched(value, old)

    def test_foreign_or_disabled_legacy_is_never_adopted(self):
        for field, bad in [("source", "foreign"), ("principal", "S-1-5-18"),
                           ("trigger", "S-1-5-18"), ("command", r"F:\Other\DeskCue.exe"),
                           ("arguments", "--other"), ("runlevel", "HighestAvailable"),
                           ("logon", "S4U"), ("logon", "Password"), ("enabled", "false"),
                           ("trigger_enabled", "false"), ("enabled", "garbage"),
                           ("delay", "PT1M"), ("workdir", r"F:\Other"),
                           ("command", EXE.replace("发布版", r"发布版\..\发布版")),
                           ("command", '"' + EXE + '"')]:
            with self.subTest(field=field, bad=bad):
                old = xml(**{field: bad})
                value = self.run_case(old=old)
                self.assertEqual(value["Result"]["Status"], "Failed", value)
                self.assert_untouched(value, old)

    def test_ambiguous_raw_xml_structure_is_rejected(self):
        for xpath, tag in [("Actions", "Exec"), ("Actions", "ComHandler"),
                           ("Principals", "Principal"), ("Principals/Principal", "GroupId"),
                           ("Triggers", "LogonTrigger"), ("Triggers", "TimeTrigger"),
                           ("RegistrationInfo", "Source"), ("Settings", "Enabled"),
                           ("Actions/Exec", "Arguments"), ("RegistrationInfo", "Exec"),
                           ("Settings", "Principal")]:
            with self.subTest(xpath=xpath, tag=tag):
                doc = ET.fromstring(xml())
                node = doc.find("/".join(f"{{{NS}}}{p}" for p in xpath.split("/")))
                ET.SubElement(node, f"{{{NS}}}{tag}").text = "foreign"
                old = ET.tostring(doc, encoding="unicode")
                value = self.run_case(old=old)
                self.assertEqual(value["Result"]["Status"], "Failed", value)
                self.assert_untouched(value, old)

    def test_existing_canonical_collision_aborts_even_when_preferred(self):
        value = self.run_case(new=xml(canonical=True))
        self.assertEqual(value["Result"]["Status"], "Failed")
        self.assertFalse(any(e.startswith(("register:", "delete:")) for e in value["Events"]))

    def test_idempotent_only_for_absent_legacy_and_strict_preferred_canonical(self):
        value = self.run_case(absent=True, new=xml(canonical=True))
        self.assertEqual(value["Result"]["Status"], "AlreadyRepaired", value)
        self.assertNotIn("process", value["Events"])
        for new in [None, xml(canonical=True, enabled="false"), xml(canonical=True, source="foreign")]:
            value = self.run_case(absent=True, new=new)
            self.assertEqual(value["Result"]["Status"], "Failed", value)
            self.assertFalse(any(e.startswith(("register:", "delete:")) for e in value["Events"]))

    def test_process_running_or_lookup_error_blocks_apply(self):
        for flags in [dict(running=True), dict(process_error=True)]:
            value = self.run_case(**flags)
            self.assertEqual(value["Result"]["Status"], "Failed", value)
            self.assert_untouched(value, xml())

    def test_query_access_error_is_never_treated_as_missing(self):
        for event in ["query:old:1", "query:new:1", "query:old:2", "query:new:2"]:
            with self.subTest(event=event):
                value = self.run_case(hooks={event: {"error": True}})
                self.assertEqual(value["Result"]["Status"], "Failed", value)
                self.assert_untouched(value, xml())

    def test_precreate_races_preserve_external_changes(self):
        for event, change in [("query:old:2", {"setOld": xml(arguments="external")}),
                              ("query:new:2", {"setNew": xml(canonical=True, source="external")})]:
            value = self.run_case(hooks={event: change})
            self.assertEqual(value["Result"]["Status"], "Failed", value)
            self.assertFalse(any(e.startswith(("register:", "delete:")) for e in value["Events"]))

    def test_registration_failure_keeps_legacy(self):
        value = self.run_case(hooks={"register:new:1": {"throw": "registration failed"}})
        self.assertEqual(value["Result"]["Status"], "Failed")
        self.assertEqual(value["Tasks"], {LEGACY: xml()})

    def test_uncertain_create_failure_still_restores_legacy_if_proven_absent(self):
        value = self.run_case(hooks={"register:new:1": {"removeOld": True, "throw": "uncertain create result"}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"], {LEGACY: xml()}, value)
        self.assertIn("register:old:1", value["Events"])

    def test_create_collision_race_never_overwrites_external_canonical(self):
        changed = xml(canonical=True, source="external")
        value = self.run_case(hooks={"register:new:1": {"setNew": changed}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"], {LEGACY: xml(), CANONICAL: changed}, value)
        self.assertNotIn("delete:new:1", value["Events"])

    def test_create_completion_uncertainty_keeps_uncaptured_canonical(self):
        value = self.run_case(hooks={"register:new:1": {"throwAfter": True}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"], {LEGACY: xml(), CANONICAL: xml(canonical=True)}, value)
        self.assertNotIn("delete:new:1", value["Events"])

    def test_delete_completion_uncertainty_restores_old_then_cleans_new(self):
        value = self.run_case(hooks={"delete:old:1": {"throwAfter": True}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"], {LEGACY: xml()}, value)
        events = value["Events"]
        self.assertLess(events.index("register:old:1"), events.index("delete:new:1"))

    def test_restore_collision_never_overwrites_external_legacy(self):
        changed = xml(arguments="external")
        value = self.run_case(hooks={"query:new:5": {"error": True},
                                     "register:old:1": {"setOld": changed}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"], {LEGACY: changed, CANONICAL: xml(canonical=True)}, value)
        self.assertNotIn("delete:new:1", value["Events"])

    def test_invalid_first_readback_is_uncaptured_and_preserved_for_inspection(self):
        value = self.run_case(hooks={"validate:new:2": {"invalid": True}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"], {LEGACY: xml(), CANONICAL: xml(canonical=True)})
        self.assertNotIn("delete:new:1", value["Events"])

    def test_readback_uncertainty_keeps_necessary_entries_and_journal(self):
        value = self.run_case(hooks={"query:new:3": {"error": True}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertIn(LEGACY, value["Tasks"])
        self.assertIn(CANONICAL, value["Tasks"])
        self.assertNotIn("delete:old:1", value["Events"])

    def test_delete_failure_keeps_legacy_and_rolls_back_new(self):
        value = self.run_case(hooks={"delete:old:1": {"throw": "delete failed"}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"], {LEGACY: xml()})

    def test_postdelete_failure_restores_old_before_removing_new(self):
        value = self.run_case(hooks={"query:new:5": {"error": True}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"], {LEGACY: xml()}, value)
        events = value["Events"]
        self.assertLess(events.index("register:old:1"), events.index("delete:new:1"))

    def test_restore_failure_preserves_new(self):
        value = self.run_case(hooks={"query:new:5": {"error": True},
                                     "register:old:1": {"throw": "restore failed"}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"], {CANONICAL: xml(canonical=True)}, value)
        self.assertNotIn("delete:new:1", value["Events"])

    def test_external_new_mutation_is_never_deleted(self):
        changed = xml(canonical=True, arguments="external")
        value = self.run_case(hooks={"query:new:4": {"setNew": changed}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"], {LEGACY: xml(), CANONICAL: changed}, value)
        self.assertNotIn("delete:old:1", value["Events"])
        self.assertNotIn("delete:new:1", value["Events"])

    def test_external_old_mutation_is_never_overwritten_or_deleted(self):
        changed = xml(arguments="external")
        value = self.run_case(hooks={"query:old:3": {"setOld": changed}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Tasks"][LEGACY], changed, value)
        self.assertNotIn("delete:old:1", value["Events"])
        self.assertNotIn("register:old:1", value["Events"])

    def test_invalid_intended_contract_is_refused_before_any_query(self):
        value = self.run_case(contract=xml(canonical=True, source="foreign"))
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertEqual(value["Events"], ["contract"])

    def test_predelete_uncertainty_never_deletes_legacy(self):
        for event in ["query:old:3", "query:new:4"]:
            value = self.run_case(hooks={event: {"error": True}})
            self.assertEqual(value["Result"]["Status"], "Failed", value)
            self.assertIn(LEGACY, value["Tasks"])
            self.assertNotIn("delete:old:1", value["Events"])

    def test_uncertain_legacy_rollback_retains_canonical(self):
        value = self.run_case(hooks={"query:new:5": {"error": True},
                                     "query:old:5": {"error": True}})
        self.assertEqual(value["Result"]["Status"], "Failed", value)
        self.assertIn(CANONICAL, value["Tasks"])
        self.assertNotIn("delete:new:1", value["Events"])


@unittest.skipUnless(os.name == "nt" and pinned_sdk_available(), "requires the pinned SDK 10.0.402 host")
class StartupPureContractTests(unittest.TestCase):
    """Freshly build before invoking recognized pure modes; never run old flags."""
    @classmethod
    def setUpClass(cls):
        cls.run_root = COMMON / ".artifacts/elevation-controller/task2" / ("pure-" + uuid.uuid4().hex)
        cls.run_root.mkdir(parents=True)
        build = cls.run_root / "build.ps1"
        build.write_text(r'''
param($SourceRoot, $RunRoot)
$ErrorActionPreference = 'Stop'
# Dot-source with a COMPLETE inert operation set, then test the actual pure
# builder function. No native query/register/delete operation is reachable.
$inert = @{
    TaskQuery = { throw 'Synthetic query must not run' }; TaskRegister = { throw 'No register' }
    TaskDelete = { throw 'No delete' }; ProcessProbe = { throw 'No process lookup' }
    ContractFactory = { throw 'Inert initialization only' }; Validator = { throw 'No validate' }
}
$null = . (Join-Path $SourceRoot 'tools/Repair-DeskCueStartup.ps1') -Operations $inert `
    -CurrentUserSid 'S-1-5-21-111-222-333-500' -CurrentUserName 'Synthetic'
$portable = Join-Path $local.Paths.DotNetRoot 'dotnet.exe'
$shared = if (Test-Path -LiteralPath $portable -PathType Leaf) { '' }
    elseif ($env:DOTNET_ROOT -and (Test-Path -LiteralPath (Join-Path $env:DOTNET_ROOT 'dotnet.exe') -PathType Leaf)) {
        Join-Path $env:DOTNET_ROOT 'dotnet.exe'
    } else { (Get-Command dotnet -ErrorAction Stop).Source }
$built = Initialize-PureHelper -SharedDotnet $shared
Invoke-WithDeskCueEnvironment -Values $built.Environment.ProcessValues -Operation {
    $env:DESKCUE_PURE_DLL = $built.Dll
    $env:DESKCUE_PURE_DOTNET = $built.Dotnet
    python (Join-Path $SourceRoot 'deskcue/tests/test_startup_repair.py') --pure-child $RunRoot
    if ($LASTEXITCODE -ne 0) { throw 'Pure helper checks failed' }
}
''', encoding="utf-8")
        cls.process = subprocess.run(["pwsh", "-NoProfile", "-NonInteractive", "-File", str(build),
                                      str(ROOT), str(cls.run_root)], capture_output=True, text=True,
                                     encoding="utf-8", timeout=180)

    def test_fresh_production_helper_pure_modes(self):
        self.assertEqual(self.process.returncode, 0,
                         self.process.stdout + self.process.stderr + " Evidence: " + str(self.run_root))


def pure_child(run):
    """Called only inside the shared process-scoped tool environment."""
    def invoke(*args):
        return subprocess.run([os.environ["DESKCUE_PURE_DOTNET"], os.environ["DESKCUE_PURE_DLL"], *args],
                              capture_output=True, text=True, encoding="utf-8", timeout=20)
    path = str(run / "小 café 日本語 😀/DeskCue.exe")
    emitted = invoke("--emit-startup-contract", path)
    assert emitted.returncode == 0, emitted.stderr
    contract = json.loads(emitted.stdout)
    assert contract["Arguments"] == "--startup --startup-source=scheduled-task"
    assert contract["TaskName"].startswith("DeskCue User Startup-S-1-")
    document = ET.fromstring(contract["Xml"])
    q = lambda tag: f"{{{NS}}}{tag}"
    assert document.find(q("Actions") + "/" + q("Exec") + "/" + q("Command")).text == path
    file = run / "fixture.xml"
    def validate(doc, task_name=contract["TaskName"]):
        file.write_text(ET.tostring(doc, encoding="unicode"), encoding="utf-8")
        return invoke("--validate-startup-contract", path, task_name, str(file))
    assert validate(document).returncode == 0
    # The repair writer preserves production's UTF-16 declaration with BOM.
    file.write_bytes(b"\xff\xfe" + contract["Xml"].encode("utf-16-le"))
    assert invoke("--validate-startup-contract", path, contract["TaskName"], str(file)).returncode == 0
    # Scheduler may omit default values; production parser normalizes them.
    principal = document.find(q("Principals") + "/" + q("Principal"))
    principal.remove(principal.find(q("RunLevel")))
    for parent in [document.find(q("Settings")), document.find(q("Triggers") + "/" + q("LogonTrigger"))]:
        parent.remove(parent.find(q("Enabled")))
    assert validate(document).returncode == 0
    assert validate(document, "foreign-task").returncode != 0
    for xpath, tag in [("Actions", "ComHandler"), ("Triggers", "TimeTrigger"),
                       ("Principals/Principal", "GroupId"), ("RegistrationInfo", "Source")]:
        changed = ET.fromstring(contract["Xml"])
        parent = changed.find("/".join(q(p) for p in xpath.split("/")))
        ET.SubElement(parent, q(tag)).text = "foreign"
        assert validate(changed).returncode != 0, (xpath, tag)
    changed = ET.fromstring(contract["Xml"])
    changed.find(q("Principals") + "/" + q("Principal") + "/" + q("RunLevel")).text = "HighestAvailable"
    assert validate(changed).returncode != 0
    # This unknown flag is safe only because we have just built the new dispatcher.
    assert invoke("--unknown-pure-mode").returncode != 0
    print("PASS pure emit/validate: Unicode, omitted defaults, actual query identity, extra actions/triggers/principals, privilege and unknown mode")


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--pure-child":
        pure_child(Path(sys.argv[2]))
    else:
        unittest.main()
