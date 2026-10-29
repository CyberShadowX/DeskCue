"""Release evidence is accepted only after validating the bytes on disk."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[1] / "release_contract.py"
if MODULE.exists():
    spec = importlib.util.spec_from_file_location("deskcue_release_contract", MODULE)
    contract = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contract)
else:
    contract = None


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value), encoding="utf-8")


def write_pe(path, machine=0x8664):
    image = bytearray(256)
    image[:2] = b"MZ"
    struct.pack_into("<I", image, 0x3C, 0x80)
    image[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<H", image, 0x84, machine)
    Path(path).write_bytes(image)


class ReleaseContractTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(contract, "release validator has not been implemented")
        scratch = Path(os.environ.get("DESKCUE_TEST_TEMP_ROOT", MODULE.parents[1] / ".artifacts" / "release-contract-tests"))
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "deskcue").mkdir()
        (self.root / "deskcue/brand.py").write_text("# fixture recipe\n", encoding="utf-8")
        self.commit = "a" * 40
        self.config = {
            "schemaVersion": 1, "productName": "DeskCue",
            "repository": "CyberShadowX/DeskCue", "upstreamRepository": "Tianyu199509/DeskBox",
            "upstreamRef": "v1.5.9", "upstreamCommit": "b" * 40,
            "upstreamVersion": "1.5.9", "brandingRevision": 1, "productVersion": "1.5.9.1",
        }
        write_json(self.root / "deskcue/config.json", self.config)
        self.provenance = {
            **self.config, "recipeSha256": digest(self.root / "deskcue/brand.py"),
            "configSha256": digest(self.root / "deskcue/config.json"),
            "sourceTreeSha256": "c" * 64, "sourceFileCount": 25,
        }
        self.write_provenance()
        (self.root / "LICENSE").write_text("GNU GENERAL PUBLIC LICENSE\nVersion 3, 29 June 2007\n", encoding="utf-8")
        (self.root / "UPSTREAM.md").write_text("Derived from https://github.com/Tianyu199509/DeskBox\n", encoding="utf-8")
        self.payload = self.root / "payload"
        self.payload.mkdir()
        self.pe_names = [
            "DeskCue.exe", "DeskCue.Updater.exe", "DeskCue.ThumbnailProxy.exe", "deskcue_native.dll",
            "EverythingSdk.dll", "Microsoft.WindowsAppRuntime.Insights.Resource.dll",
        ]
        for name in self.pe_names:
            write_pe(self.payload / name)
        for name in ["DeskCue.pri", "Microsoft.UI.Input.dll", "Microsoft.ui.xaml.dll",
                     "Microsoft.WindowsAppRuntime.dll", "ThirdParty/Everything/LICENSE.txt"]:
            path = self.payload / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"runtime fixture\n")
        for name in ("LICENSE", "UPSTREAM.md"):
            (self.payload / name).write_bytes((self.root / name).read_bytes())
        self.manifest = self.payload / "DeskCue.InstallManifest.txt"
        self.write_manifest()
        self.summary = {
            "schemaVersion": 1, "productProfile": "retail", "deploymentProfile": "full",
            "configuration": "Release", "smokeHarnessEnabled": False,
            "selfContained": True, "windowsAppSdkSelfContained": True,
            "gitCommit": self.commit, "gitDirty": False, "sourceStableDuringPublish": True,
            "platform": "x64", "runtimeIdentifier": "win-x64",
            "publishDirectory": str(self.payload), "installManifest": str(self.manifest),
            "installManifestFileCount": len(list(self.payload.rglob("*"))) - 2,
            "unexpectedWarningCodes": [], "smokeHarnessBinaryMatches": [],
            "rustNative": {"publishMatchesStaging": True, "sha256": digest(self.payload / "deskcue_native.dll")},
            "peFiles": [self.pe_entry(name) for name in self.pe_names],
        }
        self.summary_path = self.root / "summary.json"
        self.write_summary()
        self.trx = self.root / "tests.trx"
        self.write_trx()
        self.management = self.root / "management-tests.json"
        write_json(self.management, {"schemaVersion": 1, "status": "passed",
                                    "total": 5, "passed": 5, "failed": 0, "skipped": 0})
        self.installer = self.root / "DeskCue_Setup_1.5.9.1_x64.exe"
        write_pe(self.installer, 0x14C)

    def write_provenance(self):
        write_json(self.root / "deskcue/provenance.json", self.provenance)

    def pe_entry(self, name):
        path = self.payload / name
        return {"file": name, "machine": "0x8664", "bytes": path.stat().st_size, "sha256": digest(path)}

    def write_manifest(self):
        names = {p.relative_to(self.payload).as_posix() for p in self.payload.rglob("*") if p.is_file()}
        names.add("DeskCue.InstallManifest.txt")
        self.manifest.write_text("\n".join(sorted(names)) + "\n", encoding="utf-8")

    def write_summary(self):
        self.summary["installManifestFileCount"] = sum(p.is_file() for p in self.payload.rglob("*"))
        self.summary["publishFileCount"] = self.summary["installManifestFileCount"]
        write_json(self.summary_path, self.summary)

    def write_trx(self, *, outcome="Completed", aborted=0, result="Passed", total=2, passed=2):
        self.trx.write_text(
            '<TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010">'
            '<Results>' + ''.join(f'<UnitTestResult testId="{i}" outcome="{result}" />' for i in range(total)) +
            f'</Results><ResultSummary outcome="{outcome}"><Counters total="{total}" executed="{total}" '
            f'passed="{passed}" failed="0" error="0" timeout="0" aborted="{aborted}" '
            'inconclusive="0" passedButRunAborted="0" notExecuted="0" disconnected="0" '
            'warning="0" completed="0" inProgress="0" pending="0" /></ResultSummary></TestRun>', encoding="utf-8")

    def receipt(self):
        return contract.create_receipt(self.root, self.summary_path, self.installer, [self.trx],
                                       self.management, "x64", self.commit)

    def test_valid_completed_build_yields_own_portable_receipt(self):
        value = self.receipt()
        self.assertEqual((value["schemaVersion"], value["status"], value["sourceCommit"]),
                         (1, "passed", self.commit))
        self.assertEqual(value["tests"], {"total": 7, "passed": 7, "failed": 0, "skipped": 0})
        self.assertEqual(value["installer"]["path"], self.installer.name)
        self.assertEqual(value["installer"]["sha256"], digest(self.installer))
        self.assertNotIn(str(self.root), json.dumps(value))

    def test_changed_pe_bytes_fail_even_when_summary_claims_success(self):
        with (self.payload / "DeskCue.exe").open("ab") as stream:
            stream.write(b"changed after publish")
        with self.assertRaisesRegex(contract.ReleaseContractError, "hash|bytes"):
            self.receipt()

    def test_wrong_architecture_fails_even_with_matching_hash(self):
        write_pe(self.payload / "DeskCue.exe", 0xAA64)
        self.summary["peFiles"][0] = self.pe_entry("DeskCue.exe")
        self.write_summary()
        with self.assertRaisesRegex(contract.ReleaseContractError, "machine|architecture"):
            self.receipt()

    def test_aborted_trx_is_rejected_even_if_all_reported_tests_passed(self):
        self.write_trx(aborted=1)
        with self.assertRaisesRegex(contract.ReleaseContractError, "aborted|TRX"):
            self.receipt()

    def test_trx_counters_must_match_actual_results(self):
        self.write_trx(result="Failed")
        with self.assertRaisesRegex(contract.ReleaseContractError, "TRX|Passed"):
            self.receipt()

    def test_missing_trx_does_not_produce_a_receipt(self):
        self.trx.unlink()
        with self.assertRaises(contract.ReleaseContractError):
            self.receipt()

    def test_inconsistent_upstream_provenance_is_rejected(self):
        self.provenance["upstreamCommit"] = "d" * 40
        self.write_provenance()
        with self.assertRaisesRegex(contract.ReleaseContractError, "provenance|upstreamCommit"):
            self.receipt()

    def test_recipe_changed_since_branding_is_rejected(self):
        (self.root / "deskcue/brand.py").write_text("changed recipe", encoding="utf-8")
        with self.assertRaisesRegex(contract.ReleaseContractError, "recipe|provenance"):
            self.receipt()

    def test_failed_retail_or_changed_source_cannot_pass(self):
        for field, value in [("sourceStableDuringPublish", False), ("gitDirty", True),
                             ("gitCommit", "e" * 40), ("smokeHarnessEnabled", True)]:
            with self.subTest(field=field):
                original = self.summary[field]
                self.summary[field] = value
                self.write_summary()
                with self.assertRaises(contract.ReleaseContractError):
                    self.receipt()
                self.summary[field] = original

    def test_missing_copyleft_or_upstream_credit_is_rejected(self):
        (self.payload / "UPSTREAM.md").unlink()
        self.write_manifest()
        self.write_summary()
        with self.assertRaisesRegex(contract.ReleaseContractError, "UPSTREAM"):
            self.receipt()

    def test_manifest_cannot_escape_payload(self):
        with self.manifest.open("a", encoding="utf-8") as stream:
            stream.write("../outside.txt\n")
        with self.assertRaisesRegex(contract.ReleaseContractError, "manifest|path"):
            self.receipt()

    def test_manifest_must_declare_every_published_file(self):
        (self.payload / "undeclared.txt").write_text("untracked payload", encoding="utf-8")
        with self.assertRaisesRegex(contract.ReleaseContractError, "manifest"):
            self.receipt()

    def test_foreign_installer_name_is_rejected(self):
        foreign = self.root / "DeskBox_Setup_1.5.9.1_x64.exe"
        self.installer.rename(foreign)
        with self.assertRaisesRegex(contract.ReleaseContractError, "installer|DeskCue"):
            contract.create_receipt(self.root, self.summary_path, foreign, [self.trx],
                                    self.management, "x64", self.commit)

    def test_failed_management_tests_are_rejected(self):
        write_json(self.management, {"schemaVersion": 1, "status": "failed", "total": 5,
                                    "passed": 4, "failed": 1, "skipped": 0})
        with self.assertRaisesRegex(contract.ReleaseContractError, "management|test"):
            self.receipt()

    def test_failed_promotion_preserves_previous_receipt_and_installer(self):
        release = self.root / "release"
        release.mkdir()
        value = self.receipt()
        contract.promote_receipt(release, value, self.installer)
        previous = {p.name: p.read_bytes() for p in release.iterdir()}
        with self.installer.open("ab") as stream:
            stream.write(b"corrupt")
        with self.assertRaises(contract.ReleaseContractError):
            contract.promote_receipt(release, value, self.installer)
        self.assertEqual(previous, {p.name: p.read_bytes() for p in release.iterdir()})

    def test_existing_different_bytes_are_not_overwritten_for_same_release(self):
        release = self.root / "release"
        release.mkdir()
        value = self.receipt()
        contract.promote_receipt(release, value, self.installer)
        previous = (release / "receipt.json").read_bytes()
        with self.installer.open("ab") as stream:
            stream.write(b"different valid build")
        different = self.receipt()
        with self.assertRaisesRegex(contract.ReleaseContractError, "existing|immutable|different"):
            contract.promote_receipt(release, different, self.installer)
        self.assertEqual(previous, (release / "receipt.json").read_bytes())

    def local_run_result(self):
        run_id = "r-0123456789abcdef"
        run = self.root / ".artifacts/deskcue-release/win-x64/runs" / run_id
        frozen = self.root / ".artifacts/b" / run_id
        (frozen / "deskcue").mkdir(parents=True)
        for name in ("deskcue/config.json", "deskcue/provenance.json", "deskcue/brand.py", "LICENSE", "UPSTREAM.md"):
            shutil.copyfile(self.root / name, frozen / name)
        payload = frozen / "payload"
        shutil.copytree(self.payload, payload)
        summary = {**self.summary, "publishDirectory": str(payload),
                   "installManifest": str(payload / "DeskCue.InstallManifest.txt")}
        summary_path = frozen / "summary.json"
        write_json(summary_path, summary)
        packages = run / "packages"
        packages.mkdir(parents=True)
        installer = packages / self.installer.name
        shutil.copyfile(self.installer, installer)
        value = contract.create_receipt(frozen, summary_path, installer, [self.trx], self.management, "x64", self.commit)
        receipt = run / "receipt.json"
        write_json(receipt, value)
        result = {
            "schemaVersion": 1, "frozenSource": str(frozen), "payloadDirectory": str(payload),
            "retailSummary": str(summary_path), "receipt": str(receipt),
            "installer": str(installer), "payloadFiles": contract.payload_inventory(payload),
        }
        path = run / "run-result.json"
        write_json(path, result)
        return path

    def test_local_staging_preserves_full_runtime_license_and_exact_installer(self):
        result = self.local_run_result()
        staging = result.parent / "staged"
        contract.stage_local(result, staging)
        self.assertEqual((staging / "LICENSE").read_bytes(), (self.root / "LICENSE").read_bytes())
        self.assertEqual((staging / "UPSTREAM.md").read_bytes(), (self.root / "UPSTREAM.md").read_bytes())
        self.assertEqual(digest(staging / self.installer.name), digest(self.installer))
        self.assertTrue((staging / "Microsoft.WindowsAppRuntime.dll").is_file())
        self.assertTrue((staging / "receipt.json").is_file())

    def test_changed_non_pe_runtime_cannot_replace_an_existing_local_release(self):
        result = self.local_run_result()
        stable = self.root / "published"
        stable.mkdir()
        (stable / "DeskCue.exe").write_bytes(b"old known-good application")
        payload = Path(json.loads(result.read_text(encoding="utf-8"))["payloadDirectory"])
        (payload / "DeskCue.pri").write_bytes(b"changed after successful build")
        with self.assertRaisesRegex(contract.ReleaseContractError, "payload changed"):
            contract.stage_local(result, result.parent / "staging")
        self.assertEqual((stable / "DeskCue.exe").read_bytes(), b"old known-good application")
        self.assertFalse((result.parent / "staging").exists())

    def test_retail_contract_cli_rejects_changed_payload_before_packaging_receipt(self):
        result = self.local_run_result()
        run = json.loads(result.read_text(encoding="utf-8"))
        payload = Path(run["payloadDirectory"])
        baseline = result.parent / "retail-evidence.json"
        write_json(baseline, {"sourceRoot": run["frozenSource"], "payloadDirectory": str(payload),
                              "files": contract.payload_inventory(payload)})
        (payload / "DeskCue.pri").write_bytes(b"changed during installer build")
        command = subprocess.run([
            sys.executable, str(MODULE), "check-retail-snapshot", "--evidence", str(baseline),
        ], capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(command.returncode, 0)
        self.assertIn("payload changed", command.stderr)

    def fixture_build_source(self):
        wrapper = MODULE.with_name("Build-DeskCue.ps1")
        self.assertTrue(wrapper.is_file(), "shared build wrapper has not been implemented")
        (self.root / "deskcue/Build-DeskCue.ps1").write_bytes(wrapper.read_bytes())
        (self.root / "deskcue/LocalEnvironment.ps1").write_bytes(MODULE.with_name("LocalEnvironment.ps1").read_bytes())
        (self.root / "deskcue/release_contract.py").write_bytes(MODULE.read_bytes())
        (self.root / ".gitignore").write_text(".artifacts/\n.deskcue-tools/\n", encoding="utf-8")
        (self.root / "DeskCue.sln").write_text("fixture solution\n", encoding="utf-8")
        for name in ("src/DeskCue/DeskCue.csproj", "scripts/publish-aot-retail.ps1", "installer/DeskCue.iss"):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")
        # Fake tools are used only to prove failure propagation, never a passing build.
        self.fake_dotnet = self.root / "failed-dotnet.cmd"
        self.fake_dotnet.write_text("@exit /b 19\n", encoding="ascii")
        self.fake_iscc = self.root / "unused-iscc.cmd"
        self.fake_iscc.write_text("@exit /b 27\n", encoding="ascii")
        for args in [("init", "-b", "main"), ("add", "."),
                     ("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")]:
            subprocess.run(["git", "-C", str(self.root), *args], check=True, capture_output=True)
        self.release_root = self.root / ".artifacts/deskcue-release/win-x64"
        self.release_root.mkdir(parents=True)
        self.previous_receipt = self.release_root / "receipt.json"
        self.previous_receipt.write_text('{"status":"previous-valid-fixture"}\n', encoding="utf-8")

    def run_fixture_build(self):
        return subprocess.run([
            shutil.which("pwsh") or "pwsh", "-NoProfile", "-File", str(self.root / "deskcue/Build-DeskCue.ps1"),
            "-Platform", "x64", "-SourceRoot", str(self.root),
            "-DotNetPath", str(self.fake_dotnet), "-IsccPath", str(self.fake_iscc),
        ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)

    def test_nonzero_child_exit_cannot_replace_previous_success_receipt(self):
        self.fixture_build_source()
        previous = self.previous_receipt.read_bytes()
        result = self.run_fixture_build()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("exit 19", result.stdout + result.stderr)
        self.assertEqual(self.previous_receipt.read_bytes(), previous)

    def assert_failed_builder_environment(self, hosted):
        self.fixture_build_source()
        observed = self.root / ".artifacts/observed-build-environment.json"
        probe = self.root / "probe-environment.ps1"
        keys = ("DOTNET_ROOT", "DOTNET_CLI_HOME", "DOTNET_ADD_GLOBAL_TOOLS_TO_PATH", "NUGET_PACKAGES",
                "NUGET_HTTP_CACHE_PATH", "NUGET_PLUGINS_CACHE_PATH", "CARGO_HOME", "RUSTUP_HOME",
                "MSBUILDUSEREXTENSIONSPATH", "TEMP", "TMP", "DESKCUE_TEST_TEMP_ROOT", "PATH")
        quote = lambda value: "'" + str(value).replace("'", "''") + "'"
        probe.write_text(
            "$values=@{}\nforeach($key in @(" + ",".join(quote(key) for key in keys) + ")) "
            "{$values[$key]=[Environment]::GetEnvironmentVariable($key,'Process')}\n"
            f"$values|ConvertTo-Json|Set-Content -LiteralPath {quote(observed)} -Encoding utf8\n",
            encoding="utf-8-sig")
        self.fake_dotnet.write_text(
            '@"%SystemRoot%\\System32\\WindowsPowerShell\\v1.0\\powershell.exe" '
            '-NoProfile -File "%~dp0probe-environment.ps1"\n@exit /b 19\n', encoding="ascii")
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.root), "-c", "user.name=Fixture", "-c",
                        "user.email=fixture@example.invalid", "commit", "-qm", "environment fixture"],
                       check=True, capture_output=True)
        harness = self.root / ".artifacts/run-environment-check.ps1"
        harness.write_text(
            "$ErrorActionPreference='Stop'\n"
            f"$env:GITHUB_ACTIONS='{str(hosted).lower()}'\n"
            f"$env:DOTNET_CLI_HOME={quote(self.root / 'hosted-dotnet-home')}\n"
            f"$env:NUGET_PACKAGES={quote(self.root / 'hosted-nuget')}\n"
            f"$env:CARGO_HOME={quote(self.root / 'hosted-cargo')}\n"
            "$env:DOTNET_ADD_GLOBAL_TOOLS_TO_PATH='original-path-flag'\n"
            "$keys=@(" + ",".join(quote(key) for key in keys) + ")\n"
            "$before=@{};foreach($key in $keys){$before[$key]=[Environment]::GetEnvironmentVariable($key,'Process')}\n"
            "$userPath=[Environment]::GetEnvironmentVariable('PATH','User')\n"
            "$machinePath=[Environment]::GetEnvironmentVariable('PATH','Machine')\n"
            "$message=$null\ntry {\n"
            f"& {quote(self.root / 'deskcue/Build-DeskCue.ps1')} -SourceRoot {quote(self.root)} "
            f"-DotNetPath {quote(self.fake_dotnet)} -IsccPath {quote(self.fake_iscc)}\n"
            "}catch{$message=$_.Exception.Message}\n"
            "$restored=$true;foreach($key in $keys){if([Environment]::GetEnvironmentVariable($key,'Process') "
            "-cne $before[$key]){$restored=$false}}\n"
            "$answer=@{failure=$message;allSelectedProcessValuesRestored=$restored;"
            "userPathUnchanged=([Environment]::GetEnvironmentVariable('PATH','User') -ceq $userPath);"
            "machinePathUnchanged=([Environment]::GetEnvironmentVariable('PATH','Machine') -ceq $machinePath)}\n"
            "Write-Output ('DESKCUE_ENV_RESULT '+($answer|ConvertTo-Json -Compress))\n",
            encoding="utf-8-sig")
        child = subprocess.run([shutil.which("pwsh") or "pwsh", "-NoProfile", "-File", str(harness)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=80)
        self.assertEqual(child.returncode, 0, child.stdout + child.stderr)
        results = [line.removeprefix("DESKCUE_ENV_RESULT ") for line in child.stdout.splitlines()
                   if line.startswith("DESKCUE_ENV_RESULT ")]
        self.assertEqual(len(results), 1, child.stdout + child.stderr)
        answer = json.loads(results[0])
        self.assertIn("exit 19", answer["failure"])
        self.assertTrue(answer["allSelectedProcessValuesRestored"])
        self.assertTrue(answer["userPathUnchanged"])
        self.assertTrue(answer["machinePathUnchanged"])
        during = json.loads(observed.read_text(encoding="utf-8-sig"))
        self.assertEqual(during["DOTNET_ADD_GLOBAL_TOOLS_TO_PATH"], "0")
        Path(during["TEMP"]).relative_to(self.root / ".artifacts")
        Path(during["MSBUILDUSEREXTENSIONSPATH"]).relative_to(self.root / ".deskcue-tools")
        if hosted:
            self.assertEqual(Path(during["DOTNET_CLI_HOME"]), self.root / "hosted-dotnet-home")
            self.assertEqual(Path(during["NUGET_PACKAGES"]), self.root / "hosted-nuget")
            self.assertEqual(Path(during["CARGO_HOME"]), self.root / "hosted-cargo")
        else:
            for key in ("DOTNET_CLI_HOME", "NUGET_PACKAGES", "NUGET_HTTP_CACHE_PATH",
                        "NUGET_PLUGINS_CACHE_PATH", "CARGO_HOME", "RUSTUP_HOME"):
                Path(during[key]).relative_to(self.root / ".deskcue-tools")

    def test_failed_local_build_keeps_caches_in_project_and_restores_environment(self):
        self.assert_failed_builder_environment(hosted=False)

    def test_failed_hosted_build_preserves_configured_caches_and_restores_environment(self):
        self.assert_failed_builder_environment(hosted=True)

    def test_actual_build_rejects_external_worktree_before_creating_any_artifacts(self):
        self.fixture_build_source()
        outside_temp = tempfile.TemporaryDirectory(prefix="external-case-", dir=self.root.parent)
        self.addCleanup(outside_temp.cleanup)
        outside = Path(outside_temp.name) / "linked-source"
        subprocess.run(["git", "-C", str(self.root), "worktree", "add", "--detach", str(outside), "HEAD"],
                       check=True, capture_output=True)
        self.assertFalse((outside / ".artifacts").exists())
        result = subprocess.run([
            shutil.which("pwsh") or "pwsh", "-NoProfile", "-File", str(outside / "deskcue/Build-DeskCue.ps1"),
            "-SourceRoot", str(outside), "-DotNetPath", str(self.fake_dotnet), "-IsccPath", str(self.fake_iscc),
        ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex((result.stdout + result.stderr).lower(), "outside|escape|contain")
        self.assertFalse((outside / ".artifacts").exists(), "rejected external source must receive no build files")

    def test_actual_freeze_uses_a_short_guarded_source_directory(self):
        self.fixture_build_source()
        result = self.run_fixture_build()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("exit 19", result.stdout + result.stderr)
        worktrees = subprocess.run(["git", "-C", str(self.root), "worktree", "list", "--porcelain"],
                                  capture_output=True, text=True, encoding="utf-8", check=True).stdout
        paths = [Path(line.removeprefix("worktree ")) for line in worktrees.splitlines() if line.startswith("worktree ")]
        frozen = next(path for path in paths if path != self.root)
        relative = frozen.relative_to(self.root)
        self.assertEqual(relative.parts[:2], (".artifacts", "b"))
        self.assertEqual(len(relative.parts), 3)
        self.assertRegex(relative.name, r"^r-[0-9a-f]{16}$")
        canonical_run = self.release_root / "runs" / relative.name
        self.assertTrue((canonical_run / "logs/freeze-source.log").is_file())
        steps = json.loads((canonical_run / "steps.json").read_text(encoding="utf-8"))
        self.assertEqual((steps[-1]["name"], steps[-1]["exitCode"]), ("restore", 19))
        self.assertFalse((canonical_run / "s").exists())
        self.assertLess(len(str(frozen)), len(str(canonical_run / "s")))
        source_head = subprocess.run(["git", "-C", str(self.root), "rev-parse", "HEAD"],
                                     capture_output=True, text=True, check=True).stdout.strip()
        frozen_head = subprocess.run(["git", "-C", str(frozen), "rev-parse", "HEAD"],
                                     capture_output=True, text=True, check=True).stdout.strip()
        self.assertEqual(source_head, frozen_head)

    def test_dirty_source_is_rejected_before_any_build(self):
        self.fixture_build_source()
        previous = self.previous_receipt.read_bytes()
        (self.root / "src/DeskCue/DeskCue.csproj").write_text("unreviewed edit\n", encoding="utf-8")
        result = self.run_fixture_build()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("clean", (result.stdout + result.stderr).lower())
        self.assertFalse((self.release_root / "runs").exists())
        self.assertEqual(self.previous_receipt.read_bytes(), previous)

    def directory_link(self, link, destination):
        if os.name == "nt":
            quote = lambda value: "'" + str(value).replace("'", "''") + "'"
            command = subprocess.run([
                shutil.which("pwsh") or "pwsh", "-NoProfile", "-Command",
                f"New-Item -ItemType Junction -Path {quote(link)} -Target {quote(destination)} | Out-Null",
            ], capture_output=True, text=True, encoding="utf-8", errors="replace")
            self.assertEqual(command.returncode, 0, command.stdout + command.stderr)
        else:
            link.symlink_to(destination, target_is_directory=True)
        self.addCleanup(lambda: os.rmdir(link) if os.path.lexists(link) else None)
        return link

    def test_payload_root_junction_is_rejected_before_resolving_alias(self):
        actual = self.root / "actual-payload"
        self.payload.rename(actual)
        self.directory_link(self.payload, actual)
        before = {p.relative_to(actual).as_posix(): p.read_bytes() for p in actual.rglob("*") if p.is_file()}
        with self.assertRaisesRegex(contract.ReleaseContractError, "link|reparse|junction|alias"):
            self.receipt()
        self.assertEqual(before, {p.relative_to(actual).as_posix(): p.read_bytes() for p in actual.rglob("*") if p.is_file()})

    def test_installer_parent_junction_is_rejected_without_creating_receipt(self):
        outside = self.root / "outside-installers"
        outside.mkdir()
        foreign_path = outside / self.installer.name
        shutil.copyfile(self.installer, foreign_path)
        link = self.directory_link(self.root / "installer-alias", outside)
        before = foreign_path.read_bytes()
        with self.assertRaisesRegex(contract.ReleaseContractError, "link|reparse|junction|alias"):
            contract.create_receipt(self.root, self.summary_path, link / self.installer.name, [self.trx],
                                    self.management, "x64", self.commit)
        self.assertEqual(foreign_path.read_bytes(), before)
        self.assertFalse((outside / "receipt.json").exists())

    def test_receipt_parent_junction_cannot_be_read_or_written(self):
        outside = self.root / "outside-receipts"
        outside.mkdir()
        receipt = outside / "receipt.json"
        receipt.write_bytes(b'{"status":"outside-do-not-touch"}\n')
        link = self.directory_link(self.root / "receipt-alias", outside)
        before = receipt.read_bytes()
        with self.assertRaisesRegex(contract.ReleaseContractError, "link|reparse|junction|alias"):
            contract.load_json(link / "receipt.json")
        with self.assertRaisesRegex(contract.ReleaseContractError, "link|reparse|junction|alias"):
            contract.atomic_write(link / "receipt.json", b"replacement")
        self.assertEqual(receipt.read_bytes(), before)

    def test_release_root_junction_does_not_create_partial_publication(self):
        outside = self.root / "outside-release"
        outside.mkdir()
        (outside / "sentinel.txt").write_bytes(b"outside original")
        link = self.directory_link(self.root / "release-alias", outside)
        value = self.receipt()
        with self.assertRaisesRegex(contract.ReleaseContractError, "link|reparse|junction|alias"):
            contract.promote_receipt(link, value, self.installer)
        self.assertEqual({p.name: p.read_bytes() for p in outside.iterdir()}, {"sentinel.txt": b"outside original"})

    def test_lexical_containment_rejects_an_ordinary_outside_directory(self):
        with self.assertRaisesRegex(contract.ReleaseContractError, "escaped"):
            contract.safe_path(self.root / "ordinary-outside/output.json", self.payload)
        self.assertFalse((self.root / "ordinary-outside").exists())

    def test_local_staging_parent_junction_preserves_outside_bytes(self):
        result = self.local_run_result()
        outside = self.root / "outside-staging"
        outside.mkdir()
        (outside / "sentinel.txt").write_bytes(b"outside original")
        link = self.directory_link(result.parent / "staging-alias", outside)
        with self.assertRaisesRegex(contract.ReleaseContractError, "link|reparse|junction|alias"):
            contract.stage_local(result, link / "new-release")
        self.assertEqual({p.name: p.read_bytes() for p in outside.iterdir()}, {"sentinel.txt": b"outside original"})

    def test_nested_payload_junction_is_rejected_before_tree_descent(self):
        outside = self.root / "outside-nested-runtime"
        outside.mkdir()
        (outside / "sentinel.txt").write_bytes(b"outside original")
        self.directory_link(self.payload / "nested-runtime-alias", outside)
        with self.assertRaisesRegex(contract.ReleaseContractError, "link|reparse|junction|alias"):
            contract.payload_inventory(self.payload)
        self.assertEqual({p.name: p.read_bytes() for p in outside.iterdir()}, {"sentinel.txt": b"outside original"})

    def test_build_runs_parent_junction_cannot_write_outside_artifact_root(self):
        self.fixture_build_source()
        outside = self.root / ".artifacts/external-runs"
        outside.mkdir()
        (outside / "sentinel.txt").write_bytes(b"outside original")
        self.directory_link(self.release_root / "runs", outside)
        before = self.previous_receipt.read_bytes()
        result = self.run_fixture_build()
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex((result.stdout + result.stderr).lower(), "link|reparse|junction|alias")
        self.assertEqual({p.name: p.read_bytes() for p in outside.iterdir()}, {"sentinel.txt": b"outside original"})
        self.assertEqual(self.previous_receipt.read_bytes(), before)

    def test_short_checkout_parent_junction_cannot_write_outside_source_root(self):
        self.fixture_build_source()
        outside = self.root / ".artifacts/external-source"
        outside.mkdir()
        (outside / "sentinel.txt").write_bytes(b"outside original")
        self.directory_link(self.root / ".artifacts/b", outside)
        before = self.previous_receipt.read_bytes()
        result = self.run_fixture_build()
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex((result.stdout + result.stderr).lower(), "link|reparse|junction|alias")
        self.assertEqual({p.name: p.read_bytes() for p in outside.iterdir()}, {"sentinel.txt": b"outside original"})
        self.assertEqual(self.previous_receipt.read_bytes(), before)

    def test_private_run_cannot_select_another_runs_short_checkout(self):
        result = self.local_run_result()
        value = json.loads(result.read_text(encoding="utf-8"))
        value["frozenSource"] = str(self.root / ".artifacts/b/r-fedcba9876543210")
        write_json(result, value)
        with self.assertRaisesRegex(contract.ReleaseContractError, "paired short checkout"):
            contract.stage_local(result, result.parent / "staged")
        self.assertFalse((result.parent / "staged").exists())

    def test_source_root_alias_is_refused_before_build_side_effects(self):
        self.fixture_build_source()
        alias = self.root / ".artifacts/source-alias"
        self.directory_link(alias, self.root)
        result = subprocess.run([
            shutil.which("pwsh") or "pwsh", "-NoProfile", "-File", str(self.root / "deskcue/Build-DeskCue.ps1"),
            "-SourceRoot", str(alias), "-DotNetPath", str(self.fake_dotnet), "-IsccPath", str(self.fake_iscc),
        ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        self.assertNotEqual(result.returncode, 0)
        self.assertRegex((result.stdout + result.stderr).lower(), "link|reparse|junction|alias")
        self.assertFalse((self.release_root / "runs").exists())

    def test_actual_publish_wrapper_restores_old_release_after_second_move_fails(self):
        self.fixture_build_source()
        result_path = self.local_run_result()
        run = result_path.parent
        evidence = json.loads(result_path.read_text(encoding="utf-8"))
        stub_result = self.root / "stub-build-result.json"
        write_json(stub_result, {"RunResult": str(result_path), "Installer": evidence["installer"],
                                 "RuntimeIdentifier": "win-x64"})
        stable = self.root / "发布版"
        stable.mkdir()
        (stable / "DeskCue.exe").write_bytes(b"old known-good executable")
        (stable / "retained.txt").write_bytes(b"old release extra file")
        before = {p.name: p.read_bytes() for p in stable.iterdir()}
        publisher = MODULE.parents[1] / "tools/Publish-DeskCue.ps1"
        quote = lambda value: "'" + str(value).replace("'", "''") + "'"
        harness = self.root / "invoke-publish.ps1"
        harness.write_text(
            "$ErrorActionPreference = 'Stop'\n"
            f"$fixtureResult = Get-Content -LiteralPath {quote(stub_result)} -Raw | ConvertFrom-Json\n"
            "$build = { param($Wrapper, $Parameters) $fixtureResult }.GetNewClosure()\n"
            "$move = { param($From, $To) if ((Split-Path -Leaf $From) -eq 'local-release-staging') "
            "{ throw 'fixture second move failed' }; [IO.Directory]::Move($From, $To) }\n"
            f"& {quote(publisher)} -SourceRoot {quote(self.root)} -BuildOperation $build -MoveDirectoryOperation $move\n",
            encoding="utf-8")
        result = subprocess.run([shutil.which("pwsh") or "pwsh", "-NoProfile", "-File", str(harness)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("fixture second move failed", result.stdout + result.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in stable.iterdir()}, before)
        self.assertFalse((run / "previous-local-release").exists())
        self.assertTrue((run / "local-release-staging/DeskCue.exe").is_file())


if __name__ == "__main__":
    unittest.main()
