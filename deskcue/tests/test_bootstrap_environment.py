"""Offline bootstrap checks; never download or execute a tool installer."""

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PWSH = shutil.which("pwsh")


@unittest.skipUnless(PWSH, "PowerShell 7 is required")
class BootstrapEnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / "deskcue/bootstrap.ps1").is_file(), "bootstrap implementation is missing")
        base = ROOT / ".artifacts/bootstrap-tests"
        base.mkdir(parents=True, exist_ok=True)
        self.directory = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True, capture_output=True)
        for name in ("global.json", "rust-toolchain.toml"):
            shutil.copyfile(ROOT / name, self.root / name)

    def invoke(self, body, expected=0):
        data = self.root / "case.json"
        data.write_text(json.dumps({"source": str(ROOT), "root": str(self.root)}), encoding="utf-8")
        script = self.root / "case.ps1"
        script.write_text(
            "$ErrorActionPreference='Stop'\nSet-StrictMode -Version Latest\n"
            "$case=Get-Content -LiteralPath $args[0] -Raw | ConvertFrom-Json\n"
            ". (Join-Path $case.source 'deskcue/LocalEnvironment.ps1')\n"
            ". (Join-Path $case.source 'deskcue/bootstrap.ps1')\n"
            "$context=Get-DeskCueLocalEnvironment -SourceRoot $case.root\n" + body,
            encoding="utf-8",
        )
        result = subprocess.run(
            [PWSH, "-NoProfile", "-File", str(script), str(data)],
            capture_output=True, text=True, encoding="utf-8", timeout=90,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout.strip().splitlines()[-1])

    def test_pins_are_exact_reviewed_official_distributions(self):
        value = self.invoke("Get-DeskCueBootstrapPins | ConvertTo-Json -Depth 5 -Compress\n")
        self.assertEqual(value["DotNet"]["Version"], "10.0.402")
        self.assertEqual(value["DotNet"]["Algorithm"], "SHA512")
        self.assertEqual(len(value["DotNet"]["Hash"]), 128)
        self.assertTrue(value["DotNet"]["Uri"].startswith("https://builds.dotnet.microsoft.com/"))
        self.assertEqual(value["Rustup"]["Version"], "1.29.2")
        self.assertEqual(value["Rustup"]["Hash"].upper(), "00F139DA614DCED87D3C3D4121C43EEBDAC3C1BF8A5EE86B9D80DFD71C8D70FD")
        self.assertEqual(value["RustVersion"], "1.96.0")
        self.assertEqual(value["Inno"]["Version"], "6.7.3")

    def test_verified_cache_is_promoted_once_and_reused(self):
        digest = hashlib.sha256(b"complete fixture").hexdigest()
        value = self.invoke(f"""
$pin=@{{FileName='fixture.exe';Uri='https://example.invalid/fixture';Algorithm='SHA256';Hash='{digest}'}}
$script:calls=0
$download={{param($Uri,$Destination,$Proxy); $script:calls++; [IO.File]::WriteAllText($Destination,'complete fixture')}}
$first=Get-DeskCueBootstrapDownload -Root $context.ToolRoot -Pin $pin -DownloadOperation $download
$second=Get-DeskCueBootstrapDownload -Root $context.ToolRoot -Pin $pin -DownloadOperation $download
@{{calls=$script:calls;same=($first -eq $second);bytes=[IO.File]::ReadAllText($first);partial=@(Get-ChildItem -LiteralPath (Split-Path $first) -Filter '*.partial').Count}} | ConvertTo-Json -Compress
""")
        self.assertEqual(value, {"calls": 1, "same": True, "bytes": "complete fixture", "partial": 0})

    def test_bad_download_keeps_previous_cache_and_removes_partial(self):
        digest = hashlib.sha256(b"expected complete fixture").hexdigest()
        value = self.invoke(f"""
$cache=Join-Path $context.ToolRoot 'downloads'; New-Item -ItemType Directory -Path $cache -Force | Out-Null
$target=Join-Path $cache 'fixture.exe'; [IO.File]::WriteAllText($target,'previous cache')
$pin=@{{FileName='fixture.exe';Uri='https://example.invalid/fixture';Algorithm='SHA256';Hash='{digest}'}}
$failed=$false
try {{ Get-DeskCueBootstrapDownload -Root $context.ToolRoot -Pin $pin -DownloadOperation {{param($Uri,$Destination,$Proxy); [IO.File]::WriteAllText($Destination,'truncated')}} | Out-Null }} catch {{ $failed=$_.Exception.Message -match 'checksum' }}
@{{failed=$failed;bytes=[IO.File]::ReadAllText($target);partial=@(Get-ChildItem -LiteralPath $cache -Filter '*.partial').Count}} | ConvertTo-Json -Compress
""")
        self.assertEqual(value, {"failed": True, "bytes": "previous cache", "partial": 0})

    def test_validate_only_missing_toolchain_creates_nothing(self):
        value = self.invoke("""
$called=$false; $failed=$false
try { Invoke-DeskCueBootstrapInitialization -Environment $context -ValidateOnly -DownloadOperation { $script:called=$true } | Out-Null } catch { $failed=$_.Exception.Message -match 'missing|not initialized|not installed' }
@{failed=$failed;download=$called;toolRootExists=(Test-Path -LiteralPath $context.ToolRoot)} | ConvertTo-Json -Compress
""")
        self.assertEqual(value, {"failed": True, "download": False, "toolRootExists": False})

    def test_failed_initialization_restores_environment_and_never_executes_bad_bytes(self):
        value = self.invoke("""
$names=@('PATH','TEMP','TMP','DOTNET_ROOT','DOTNET_CLI_HOME','DOTNET_ADD_GLOBAL_TOOLS_TO_PATH','CARGO_HOME','RUSTUP_HOME','RUSTUP_DIST_SERVER','RUSTUP_UPDATE_ROOT','NUGET_PACKAGES','MSBUILDUSEREXTENSIONSPATH')
$before=@{}; foreach($name in $names){$before[$name]=[Environment]::GetEnvironmentVariable($name,'Process')}
$script:downloadCalls=0; $script:executed=0; $script:observed=$false; $failed=$false
$download={param($Uri,$Destination,$Proxy); $script:downloadCalls++; $script:observed=($env:DOTNET_ADD_GLOBAL_TOOLS_TO_PATH -eq '0' -and $env:RUSTUP_DIST_SERVER -eq 'https://static.rust-lang.org' -and $env:RUSTUP_UPDATE_ROOT -eq 'https://static.rust-lang.org/rustup' -and $env:CARGO_HOME.StartsWith($context.CanonicalRoot) -and $env:TEMP.StartsWith($context.CanonicalRoot)); [IO.File]::WriteAllText($Destination,'incomplete SDK archive')}
try { Invoke-DeskCueBootstrapInitialization -Environment $context -DownloadOperation $download -ExecuteOperation { $script:executed++; @{ExitCode=0;Output='unexpected execution'} } | Out-Null } catch { $failed=$_.Exception.Message -match 'checksum' }
$restored=$true; foreach($name in $names){if([Environment]::GetEnvironmentVariable($name,'Process') -cne $before[$name]){$restored=$false}}
@{failed=$failed;download=$script:downloadCalls;executed=$script:executed;observed=$script:observed;restored=$restored} | ConvertTo-Json -Compress
""")
        self.assertEqual(value, {"failed": True, "download": 1, "executed": 0, "observed": True, "restored": True})

    def test_directory_promotion_failure_rolls_back_both_active_directories(self):
        value = self.invoke("""
$root=$context.ToolRoot; $dirs=[ordered]@{}
foreach($name in @('cargo','rustup')){
    $active=Join-Path $root $name; $candidate=Join-Path $root ('staging/'+$name)
    New-Item -ItemType Directory -Path $active,$candidate -Force | Out-Null
    [IO.File]::WriteAllText((Join-Path $active 'value.txt'),'old-'+$name)
    [IO.File]::WriteAllText((Join-Path $candidate 'value.txt'),'new-'+$name)
    $dirs[$active]=$candidate
}
$script:moves=0; $failed=$false
$move={param($From,$To); $script:moves++; if($script:moves -eq 4){throw 'fixture promotion failure'}; [IO.Directory]::Move($From,$To)}
try { Move-DeskCueBootstrapDirectories -Root $root -Directories $dirs -MoveOperation $move } catch { $failed=$true }
@{failed=$failed;cargo=[IO.File]::ReadAllText((Join-Path $root 'cargo/value.txt'));rustup=[IO.File]::ReadAllText((Join-Path $root 'rustup/value.txt'))} | ConvertTo-Json -Compress
""")
        self.assertEqual(value, {"failed": True, "cargo": "old-cargo", "rustup": "old-rustup"})

    def test_dotnet_probe_disables_global_path_before_execution_and_restores_on_failure(self):
        value = self.invoke("""
New-Item -ItemType Directory -Path $context.Paths.DotNetRoot -Force | Out-Null
$exe=Join-Path $context.Paths.DotNetRoot 'dotnet.exe'; [IO.File]::WriteAllText($exe,'never executed fixture')
$env:DOTNET_ADD_GLOBAL_TOOLS_TO_PATH='original'; $script:saw=$false; $failed=$false
try { Invoke-DeskCueBootstrapCommand -Environment $context -Executable $exe -Arguments @('--version') -ExecuteOperation {param($Executable,$Arguments); $script:saw=($env:DOTNET_ADD_GLOBAL_TOOLS_TO_PATH -eq '0' -and $env:DOTNET_CLI_TELEMETRY_OPTOUT -eq '1' -and $env:DOTNET_GENERATE_ASPNET_CERTIFICATE -eq 'false'); @{ExitCode=7;Output='fixture failure'}} | Out-Null } catch { $failed=$true }
@{failed=$failed;saw=$script:saw;restored=($env:DOTNET_ADD_GLOBAL_TOOLS_TO_PATH -eq 'original')} | ConvertTo-Json -Compress
""")
        self.assertEqual(value, {"failed": True, "saw": True, "restored": True})

    def test_download_name_cannot_escape_local_cache(self):
        value = self.invoke("""
$failed=$false; $script:called=$false
$pin=@{FileName='../escape.exe';Uri='https://example.invalid/fixture';Algorithm='SHA256';Hash=('0'*64)}
try { Get-DeskCueBootstrapDownload -Root $context.ToolRoot -Pin $pin -DownloadOperation {$script:called=$true} | Out-Null } catch {$failed=$true}
@{failed=$failed;called=$script:called;escaped=(Test-Path -LiteralPath (Join-Path $context.ToolRoot 'escape.exe'))} | ConvertTo-Json -Compress
""")
        self.assertEqual(value, {"failed": True, "called": False, "escaped": False})

    def test_contained_file_links_are_only_accepted_for_rust_bin_shims(self):
        value = self.invoke("""
$script:executed=0; $blocked=0
foreach($item in @(@('dotnet','dotnet.exe'),@('inno','ISCC.exe'))){
    $directory=Join-Path $context.ToolRoot $item[0]; New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $target=Join-Path $directory 'target.exe'; [IO.File]::WriteAllText($target,'fixture')
    $link=Join-Path $directory $item[1]; New-Item -ItemType SymbolicLink -Path $link -Target $target | Out-Null
    try { Invoke-DeskCueBootstrapCommand -Environment $context -Executable $link -ExecuteOperation {$script:executed++; @{ExitCode=0;Output='unexpected'}} | Out-Null } catch {$blocked++}
    try { Get-DeskCueBootstrapFileManifest -Root $context.ToolRoot -Directories @($directory) | Out-Null } catch {$blocked++}
}
$allowed=0
foreach($relative in @('cargo/bin',('tmp/bootstrap-rust-'+('a'*32)+'/cargo/bin'))){
    $directory=Join-Path $context.ToolRoot $relative; New-Item -ItemType Directory -Path $directory -Force | Out-Null
    $target=Join-Path $directory 'rustup.exe'; [IO.File]::WriteAllText($target,'fixture')
    $link=Join-Path $directory 'cargo.exe'; New-Item -ItemType SymbolicLink -Path $link -Target $target | Out-Null
    Invoke-DeskCueBootstrapCommand -Environment $context -Executable $link -ExecuteOperation {@{ExitCode=0;Output='rust shim'}} | Out-Null
    $manifest=Get-DeskCueBootstrapFileManifest -Root $context.ToolRoot -Directories @($directory)
    if($manifest.Count -eq 2){$allowed++}
}
@{blocked=$blocked;unexpectedExecution=$script:executed;allowedRustDirectories=$allowed} | ConvertTo-Json -Compress
""")
        self.assertEqual(value, {"blocked": 4, "unexpectedExecution": 0, "allowedRustDirectories": 2})


if __name__ == '__main__':
    unittest.main()
