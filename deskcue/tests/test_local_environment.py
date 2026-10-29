"""Exercise the project-owned tool/cache layout without installing any tools."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


MODULE = Path(__file__).resolve().parents[1] / "LocalEnvironment.ps1"
PWSH = shutil.which("pwsh")


def quote(value):
    return "'" + str(value).replace("'", "''") + "'"


@unittest.skipUnless(PWSH, "PowerShell 7 is required for the actual environment helper")
class LocalEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.is_file(), "project-local environment helper is missing")
        scratch = MODULE.parents[1] / ".artifacts/local-environment-tests"
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="case-", dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / "project"
        self.root.mkdir()
        self.git("init", "-b", "main")
        (self.root / ".gitignore").write_text(".artifacts/\n.deskcue-tools/\n", encoding="utf-8")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "-qm", "fixture")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args], check=True,
                              capture_output=True, text=True, encoding="utf-8").stdout.strip()

    def run_ps(self, source, *, expect_success=True):
        script = self.home / "probe.ps1"
        script.write_text("$ErrorActionPreference='Stop'\n"
                          f". {quote(MODULE)}\n" + source, encoding="utf-8-sig")
        result = subprocess.run([PWSH, "-NoProfile", "-File", str(script)], capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=40)
        if expect_success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def layout(self, source=None, run=None):
        extra = f" -RunRoot {quote(run)}" if run else ""
        return self.run_ps(f"Get-DeskCueLocalEnvironment -SourceRoot {quote(source or self.root)}"
                           f"{extra} | ConvertTo-Json -Depth 5\n")

    def test_normal_checkout_owns_tools_and_every_cache_inside_its_root(self):
        result = self.layout()
        self.assertEqual(Path(result["CanonicalRoot"]), self.root)
        self.assertEqual(Path(result["ToolRoot"]), self.root / ".deskcue-tools")
        for value in result["Paths"].values():
            Path(value).relative_to(self.root / ".deskcue-tools")
        self.assertEqual(result["ProcessValues"]["DOTNET_ADD_GLOBAL_TOOLS_TO_PATH"], "0")
        self.assertEqual(result["ProcessValues"]["DOTNET_GENERATE_ASPNET_CERTIFICATE"], "false")
        self.assertFalse((self.home / ".deskcue-tools").exists())
        self.assertFalse((self.root / ".deskcue-tools").exists(), "layout inspection must not create files")

    def test_nested_worktree_reuses_the_common_project_toolchain(self):
        worktree = self.root / ".artifacts/linked-source"
        self.git("worktree", "add", "--detach", str(worktree), "HEAD")
        run = worktree / ".artifacts/run"
        result = self.layout(worktree, run)
        self.assertEqual(Path(result["SourceRoot"]), worktree)
        self.assertEqual(Path(result["CanonicalRoot"]), self.root)
        self.assertEqual(Path(result["ToolRoot"]), self.root / ".deskcue-tools")
        self.assertEqual(Path(result["ProcessValues"]["TEMP"]), run / "tmp")
        self.assertEqual(Path(result["ProcessValues"]["DESKCUE_TEST_TEMP_ROOT"]), run / "tmp/release-tests")

    def test_external_worktree_is_rejected_before_creating_a_toolchain(self):
        outside = self.home / "external-linked-source"
        self.git("worktree", "add", "--detach", str(outside), "HEAD")
        error = self.run_ps(f"Get-DeskCueLocalEnvironment -SourceRoot {quote(outside)}\n",
                            expect_success=False)
        self.assertRegex(error, "outside|contain|escape")
        self.assertFalse((self.home / ".deskcue-tools").exists())

    def test_run_root_outside_project_is_rejected_without_creating_it(self):
        outside = self.home / "outside-output"
        error = self.run_ps(f"Get-DeskCueLocalEnvironment -SourceRoot {quote(self.root)} "
                            f"-RunRoot {quote(outside)}\n", expect_success=False)
        self.assertRegex(error, "outside|contain|escape")
        self.assertFalse(outside.exists())

    def test_cache_directory_link_cannot_redirect_writes_outside_project(self):
        tool = self.root / ".deskcue-tools"
        tool.mkdir()
        outside = self.home / "outside-cache"
        outside.mkdir()
        sentinel = outside / "untouched.txt"
        sentinel.write_bytes(b"original outside bytes")
        link = tool / "dotnet-home"
        if os.name == "nt":
            self.run_ps(f"New-Item -ItemType Junction -Path {quote(link)} -Target {quote(outside)} | Out-Null\n"
                        "'{}'\n")
            self.addCleanup(lambda: os.rmdir(link) if os.path.lexists(link) else None)
        else:
            link.symlink_to(outside, target_is_directory=True)
        error = self.run_ps(f"Get-DeskCueLocalEnvironment -SourceRoot {quote(self.root)}\n",
                            expect_success=False)
        self.assertRegex(error, "link|reparse|alias")
        self.assertEqual(sentinel.read_bytes(), b"original outside bytes")
        self.assertEqual(sorted(p.name for p in outside.iterdir()), ["untouched.txt"])

    def test_ordinary_file_cannot_be_a_cache_parent(self):
        tool = self.root / ".deskcue-tools"
        tool.mkdir()
        blocker = tool / "nuget"
        blocker.write_bytes(b"must remain a file")
        error = self.run_ps(f"Get-DeskCueLocalEnvironment -SourceRoot {quote(self.root)}\n",
                            expect_success=False)
        self.assertRegex(error, "directory|parent")
        self.assertEqual(blocker.read_bytes(), b"must remain a file")

    def test_cargo_bin_directory_link_is_rejected_by_actual_layout_resolution(self):
        cargo = self.root / ".deskcue-tools/cargo"
        cargo.mkdir(parents=True)
        outside = self.home / "outside-cargo-bin"
        outside.mkdir()
        (outside / "cargo.exe").write_bytes(b"outside tool never executed")
        link = cargo / "bin"
        if os.name == "nt":
            self.run_ps(f"New-Item -ItemType Junction -Path {quote(link)} -Target {quote(outside)} | Out-Null\n"
                        "'{}'\n")
            self.addCleanup(lambda: os.rmdir(link) if os.path.lexists(link) else None)
        else:
            link.symlink_to(outside, target_is_directory=True)
        error = self.run_ps(f"Get-DeskCueLocalEnvironment -SourceRoot {quote(self.root)}\n",
                            expect_success=False)
        self.assertRegex(error, "link|reparse")
        self.assertEqual((outside / "cargo.exe").read_bytes(), b"outside tool never executed")

    def test_cargo_external_executable_link_is_rejected_by_actual_layout_resolution(self):
        cargo_bin = self.root / ".deskcue-tools/cargo/bin"
        cargo_bin.mkdir(parents=True)
        outside = self.home / "outside-cargo.exe"
        outside.write_bytes(b"outside tool never executed")
        (cargo_bin / "cargo.exe").symlink_to(outside)
        error = self.run_ps(f"Get-DeskCueLocalEnvironment -SourceRoot {quote(self.root)}\n",
                            expect_success=False)
        self.assertRegex(error, "outside|escape|contain")
        self.assertEqual(outside.read_bytes(), b"outside tool never executed")

    def test_cargo_internal_rustup_link_is_accepted_by_actual_layout_resolution(self):
        cargo_bin = self.root / ".deskcue-tools/cargo/bin"
        cargo_bin.mkdir(parents=True)
        (cargo_bin / "rustup.exe").write_bytes(b"fixture tool never executed")
        (cargo_bin / "cargo.exe").symlink_to("rustup.exe")
        result = self.layout()
        self.assertEqual(Path(result["ToolRoot"]), self.root / ".deskcue-tools")

    def test_internal_rustup_file_link_requires_read_only_opt_in(self):
        tool = self.root / ".deskcue-tools"
        tool.mkdir()
        binary = tool / "rustup.exe"
        binary.write_bytes(b"fixture, never executed")
        link = tool / "cargo.exe"
        link.symlink_to("rustup.exe")
        error = self.run_ps(f"Assert-DeskCueLocalPath -Root {quote(tool)} -Path {quote(link)}\n",
                            expect_success=False)
        self.assertRegex(error, "link|reparse")
        result = self.run_ps(f"Assert-DeskCueLocalPath -Root {quote(tool)} -Path {quote(link)} "
                             "-AllowInternalFileLink\n'{}'\n")
        self.assertEqual(result, {})
        self.assertEqual(binary.read_bytes(), b"fixture, never executed")

    def test_read_only_file_link_opt_in_still_rejects_external_target(self):
        tool = self.root / ".deskcue-tools"
        tool.mkdir()
        outside = self.home / "outside.exe"
        outside.write_bytes(b"outside original")
        link = tool / "cargo.exe"
        link.symlink_to(outside)
        error = self.run_ps(f"Assert-DeskCueLocalPath -Root {quote(tool)} -Path {quote(link)} "
                            "-AllowInternalFileLink\n", expect_success=False)
        self.assertRegex(error, "outside|escape|contain")
        self.assertEqual(outside.read_bytes(), b"outside original")

    def test_environment_scope_restores_absent_and_existing_values_after_failure(self):
        result = self.run_ps(
            f"$layout=Get-DeskCueLocalEnvironment -SourceRoot {quote(self.root)}\n"
            "$env:DESKCUE_ENV_EXISTING='original-value'\n"
            "[Environment]::SetEnvironmentVariable('DESKCUE_ENV_ABSENT',[NullString]::Value,'Process')\n"
            "[Environment]::SetEnvironmentVariable('DESKCUE_ENV_EMPTY','','Process')\n"
            "$oldPath=$env:PATH\n"
            "$oldUserPath=[Environment]::GetEnvironmentVariable('PATH','User')\n"
            "$oldMachinePath=[Environment]::GetEnvironmentVariable('PATH','Machine')\n"
            "$values=@{};foreach($entry in $layout.ProcessValues.GetEnumerator()){$values[$entry.Key]=$entry.Value}\n"
            "$values['DESKCUE_ENV_EXISTING']='temporary';$values['DESKCUE_ENV_ABSENT']='temporary'\n"
            "$values['DESKCUE_ENV_EMPTY']='temporary'\n"
            "$seen=$null;$caught=$false\n"
            "try { Invoke-WithDeskCueEnvironment -Values $values -Operation {\n"
            " $script:seen=@{flag=$env:DOTNET_ADD_GLOBAL_TOOLS_TO_PATH;tmp=$env:TEMP;cargo=$env:CARGO_HOME}\n"
            " throw 'intentional child failure'\n"
            "} } catch {if($_.Exception.Message -notlike '*intentional child failure*'){throw};$caught=$true}\n"
            "@{caught=$caught;during=$script:seen;existing=$env:DESKCUE_ENV_EXISTING;"
            "absent=[Environment]::GetEnvironmentVariable('DESKCUE_ENV_ABSENT','Process');"
            "empty=[Environment]::GetEnvironmentVariable('DESKCUE_ENV_EMPTY','Process');"
            "processPathRestored=($env:PATH -ceq $oldPath);"
            "userPathUnchanged=([Environment]::GetEnvironmentVariable('PATH','User') -ceq $oldUserPath);"
            "machinePathUnchanged=([Environment]::GetEnvironmentVariable('PATH','Machine') -ceq $oldMachinePath)}"
            "|ConvertTo-Json -Depth 3\n")
        self.assertTrue(result["caught"])
        self.assertEqual(result["during"]["flag"], "0")
        Path(result["during"]["tmp"]).relative_to(self.root)
        Path(result["during"]["cargo"]).relative_to(self.root)
        self.assertEqual(result["existing"], "original-value")
        self.assertIsNone(result["absent"])
        self.assertEqual(result["empty"], "")
        for flag in ("processPathRestored", "userPathUnchanged", "machinePathUnchanged"):
            self.assertTrue(result[flag], flag)


if __name__ == "__main__":
    unittest.main()
