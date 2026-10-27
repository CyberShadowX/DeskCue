#Requires -Version 7.0
<#
.SYNOPSIS
Build and verify a complete DeskCue retail installer from a clean, exact Git HEAD.
.DESCRIPTION
Cloud and local callers use this entry. All writes are confined to a unique
ignored run directory until every child command and byte-level contract passes.
This script never starts the product, runs an installer, or registers startup.
#>
[CmdletBinding()]
param(
    [ValidateSet('x64', 'ARM64')][string]$Platform = 'x64',
    [string]$DotNetPath = '',
    [string]$IsccPath = '',
    [string]$SourceRoot = ''
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest

function Assert-SafeDeskCuePath {
    param([string]$Root, [string]$Path)
    & $script:python $script:pathValidator guard-path --root $Root --path $Path
    if ($LASTEXITCODE -ne 0) { throw 'Unsafe release path: containment/link/reparse validation failed.' }
}

function Read-Git {
    param([string]$Root, [string[]]$Arguments)
    $output = & git -C $Root @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw "Git inspection failed (exit $LASTEXITCODE)." }
    return ($output -join "`n").Trim()
}

function Assert-CleanSource {
    param([string]$Root, [string]$ExpectedCommit = '')
    Assert-SafeDeskCuePath $Root $Root
    $actualRoot = [IO.Path]::GetFullPath((Read-Git $Root @('rev-parse', '--show-toplevel'))).TrimEnd('\', '/')
    if (-not $actualRoot.Equals($Root.TrimEnd('\', '/'), [StringComparison]::OrdinalIgnoreCase)) {
        throw 'SourceRoot must identify the repository root.'
    }
    $commit = Read-Git $Root @('rev-parse', 'HEAD')
    if ($commit -cnotmatch '^[a-f0-9]{40}$') { throw 'Invalid Git HEAD.' }
    if ($ExpectedCommit -and $commit -cne $ExpectedCommit) { throw 'Source commit changed during build.' }
    if (Read-Git $Root @('status', '--porcelain=v1', '--untracked-files=all')) {
        throw 'Retail builds require a clean source tree. Commit reviewed changes first.'
    }
    return $commit
}

function Resolve-Tool {
    param([string]$ExplicitPath, [string[]]$Candidates, [string]$CommandName)
    if ($ExplicitPath) {
        Assert-SafeDeskCuePath (Split-Path -Parent ([IO.Path]::GetFullPath($ExplicitPath))) $ExplicitPath
        $selected = [IO.Path]::GetFullPath($ExplicitPath)
        if (-not (Test-Path -LiteralPath $selected -PathType Leaf)) { throw "$CommandName tool was not found: $selected" }
        return $selected
    }
    foreach ($candidate in $Candidates) {
        if ($candidate) { Assert-SafeDeskCuePath (Split-Path -Parent $candidate) $candidate }
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return [IO.Path]::GetFullPath($candidate)
        }
    }
    $command = Get-Command $CommandName -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $command) { throw "$CommandName is required. Supply its explicit path or add the installed tool to this process PATH." }
    Assert-SafeDeskCuePath (Split-Path -Parent $command.Source) $command.Source
    return $command.Source
}

function Invoke-CheckedCommand {
    param([string]$Name, [string]$Command, [string[]]$Arguments, [string]$WorkingDirectory)
    $log = Join-Path $script:runRoot ("logs\$Name.log")
    Assert-SafeDeskCuePath $repoRoot $WorkingDirectory
    Assert-SafeDeskCuePath $script:runRoot $log
    Write-Host "DeskCue $Name"
    $started = [DateTime]::UtcNow
    Push-Location -LiteralPath $WorkingDirectory
    try {
        & $Command @Arguments 2>&1 | Tee-Object -FilePath $log | Out-Host
        $code = $LASTEXITCODE
    }
    finally { Pop-Location }
    $script:steps.Add([ordered]@{
        name = $Name; exitCode = $code; startedUtc = $started.ToString('O'); completedUtc = [DateTime]::UtcNow.ToString('O')
    })
    $stepsPath = Join-Path $script:runRoot 'steps.json'
    Assert-SafeDeskCuePath $script:runRoot $stepsPath
    [IO.File]::WriteAllText($stepsPath, ($script:steps | ConvertTo-Json -Depth 5))
    if ($code -ne 0) { throw "DeskCue $Name failed with exit $code. Evidence: $log" }
}

$python = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$pathValidator = Join-Path $PSScriptRoot 'release_contract.py'
$inputRoot = if ($SourceRoot) { $SourceRoot } else { Split-Path -Parent $PSScriptRoot }
Assert-SafeDeskCuePath $inputRoot $inputRoot
Assert-SafeDeskCuePath (Split-Path -Parent $PSScriptRoot) $pathValidator
$repoRoot = [IO.Path]::GetFullPath($inputRoot)
$head = Assert-CleanSource $repoRoot
$branch = Read-Git $repoRoot @('branch', '--show-current')
Write-Host "DeskCue source: $repoRoot; branch: $branch; commit: $head"
$rid = if ($Platform -eq 'ARM64') { 'win-arm64' } else { 'win-x64' }
$releaseRoot = Join-Path $repoRoot ".artifacts\deskcue-release\$rid"
Assert-SafeDeskCuePath $repoRoot $releaseRoot
if ((Read-Git $repoRoot @('check-ignore', '--no-index', '--', '.artifacts/deskcue-release/ignore-probe')) -eq '') {
    throw 'The release artifact directory must be ignored by Git.'
}
$shortSourceParent = Join-Path $repoRoot '.artifacts\b'
Assert-SafeDeskCuePath $repoRoot $shortSourceParent
if ((Read-Git $repoRoot @('check-ignore', '--no-index', '--', '.artifacts/b/ignore-probe')) -eq '') {
    throw 'The short source checkout directory must be ignored by Git.'
}
New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
Assert-SafeDeskCuePath $repoRoot $releaseRoot
# This lock is held throughout preparation and receipt promotion, separately per architecture.
$lockPath = Join-Path $releaseRoot 'build.lock'
Assert-SafeDeskCuePath $releaseRoot $lockPath
$releaseLock = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
$environmentBefore = @{}
$steps = [Collections.Generic.List[object]]::new()
try {
    $runId = 'r-' + [Guid]::NewGuid().ToString('N').Substring(0, 16)
    $runRoot = Join-Path $releaseRoot "runs\$runId"
    Assert-SafeDeskCuePath $releaseRoot $runRoot
    Assert-SafeDeskCuePath $runRoot (Join-Path $runRoot 'logs')
    Assert-SafeDeskCuePath $runRoot (Join-Path $runRoot 'tmp')
    New-Item -ItemType Directory -Path (Join-Path $runRoot 'logs'), (Join-Path $runRoot 'tmp') -Force | Out-Null
    $toolRoot = Join-Path (Split-Path -Parent $repoRoot) '.deskcue-tools'
    Assert-SafeDeskCuePath (Split-Path -Parent $repoRoot) $toolRoot
    $dotnet = Resolve-Tool $DotNetPath @((Join-Path $toolRoot 'dotnet\dotnet.exe')) 'dotnet'
    $isccCandidates = @((Join-Path $toolRoot 'inno\ISCC.exe'))
    foreach ($programRoot in @(${env:ProgramFiles(x86)}, $env:ProgramFiles)) {
        if ($programRoot) { $isccCandidates += Join-Path $programRoot 'Inno Setup 6\ISCC.exe' }
    }
    $iscc = Resolve-Tool $IsccPath $isccCandidates 'ISCC.exe'
    $pwsh = (Get-Process -Id $PID).Path
    Assert-SafeDeskCuePath (Split-Path -Parent $pwsh) $pwsh
    $processValues = @{
        DOTNET_ROOT = Split-Path -Parent $dotnet
        DOTNET_NOLOGO = '1'; DOTNET_CLI_TELEMETRY_OPTOUT = '1'
        DOTNET_GENERATE_ASPNET_CERTIFICATE = 'false'; MSBUILDDISABLENODEREUSE = '1'
        RestoreLockedMode = 'true'; PYTHONUTF8 = '1'
        TEMP = Join-Path $runRoot 'tmp'; TMP = Join-Path $runRoot 'tmp'
        DESKCUE_TEST_TEMP_ROOT = Join-Path $runRoot 'tmp\release-tests'
    }
    # Existing portable caches are optional. Hosted builders retain their own configured caches.
    if (Test-Path -LiteralPath (Join-Path $toolRoot 'dotnet') -PathType Container) {
        $processValues['DOTNET_CLI_HOME'] = Join-Path $toolRoot 'dotnet-home'
        $processValues['NUGET_PACKAGES'] = Join-Path $toolRoot 'nuget\packages'
        $processValues['NUGET_HTTP_CACHE_PATH'] = Join-Path $toolRoot 'nuget\http-cache'
        $processValues['NUGET_PLUGINS_CACHE_PATH'] = Join-Path $toolRoot 'nuget\plugins-cache'
        foreach ($name in @('DOTNET_CLI_HOME', 'NUGET_PACKAGES', 'NUGET_HTTP_CACHE_PATH', 'NUGET_PLUGINS_CACHE_PATH')) {
            Assert-SafeDeskCuePath $toolRoot $processValues[$name]
        }
    }
    $pathParts = @((Split-Path -Parent $dotnet))
    if (Test-Path -LiteralPath (Join-Path $toolRoot 'cargo\bin\cargo.exe') -PathType Leaf) {
        $processValues['CARGO_HOME'] = Join-Path $toolRoot 'cargo'
        $processValues['RUSTUP_HOME'] = Join-Path $toolRoot 'rustup'
        $pathParts += Join-Path $toolRoot 'cargo\bin'
    }
    $processValues['PATH'] = ($pathParts + @($env:PATH)) -join [IO.Path]::PathSeparator
    foreach ($entry in $processValues.GetEnumerator()) {
        $environmentBefore[$entry.Key] = [Environment]::GetEnvironmentVariable($entry.Key, 'Process')
        [Environment]::SetEnvironmentVariable($entry.Key, $entry.Value, 'Process')
    }

    # MSVC/Rust output paths can exceed MAX_PATH when a checkout sits below the
    # full evidence hierarchy. Keep source shallow; retain logs/receipts in runRoot.
    $frozenRoot = Join-Path $shortSourceParent $runId
    Assert-SafeDeskCuePath $repoRoot $frozenRoot
    New-Item -ItemType Directory -Path $shortSourceParent -Force | Out-Null
    Assert-SafeDeskCuePath $repoRoot $frozenRoot
    Invoke-CheckedCommand 'freeze-source' 'git' @('-C', $repoRoot, 'worktree', 'add', '--detach', $frozenRoot, $head) $repoRoot
    $null = Assert-CleanSource $frozenRoot $head
    $validator = Join-Path $frozenRoot 'deskcue\release_contract.py'
    Assert-SafeDeskCuePath $frozenRoot $validator
    $pathValidator = $validator
    Invoke-CheckedCommand 'metadata' $python @($validator, 'metadata', '--source-root', $frozenRoot, '--commit', $head) $frozenRoot
    $configPath = Join-Path $frozenRoot 'deskcue\config.json'
    Assert-SafeDeskCuePath $frozenRoot $configPath
    $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    $common = @("-p:Platform=$Platform", "-p:RuntimeIdentifier=$rid", '-p:RestoreLockedMode=true')
    $solution = Join-Path $frozenRoot 'DeskCue.sln'
    Invoke-CheckedCommand 'restore' $dotnet (@('restore', $solution, '--locked-mode', '-v:minimal') + $common) $frozenRoot
    Invoke-CheckedCommand 'build' $dotnet (@('build', (Join-Path $frozenRoot 'src\DeskCue\DeskCue.csproj'),
        '--configuration', 'Release', '--no-restore', '-v:minimal') + $common) $frozenRoot

    $testProjects = @(
        foreach ($relative in ((Read-Git $frozenRoot @('ls-files', '--', 'tests/*.csproj')) -split "`n")) {
            if (-not $relative) { continue }
            $testProject = Join-Path $frozenRoot $relative
            Assert-SafeDeskCuePath $frozenRoot $testProject
            [xml]$projectXml = Get-Content -LiteralPath $testProject -Raw
            if (@($projectXml.SelectNodes("/*[local-name()='Project']/*[local-name()='PropertyGroup']/*[local-name()='IsTestProject']") |
                    Where-Object { $_.InnerText -eq 'true' }).Count -gt 0) { $testProject }
        }
    )
    if ($testProjects.Count -eq 0) { throw 'No tracked .NET test projects were discovered.' }
    $trxRoot = Join-Path $runRoot 'tests'
    foreach ($index in 0..($testProjects.Count - 1)) {
        $testOutput = Join-Path $trxRoot ([string]$index)
        Assert-SafeDeskCuePath $runRoot $testOutput
        Invoke-CheckedCommand "test-$index" $dotnet (@('test', $testProjects[$index], '--configuration', 'Release',
            '--no-restore', '-p:WindowsAppSdkBootstrapInitialize=false', '--blame-hang', '--blame-hang-timeout', '5m',
            '--logger', 'trx;LogFileName=results.trx', '--results-directory', $testOutput, '-v:minimal') + $common) $frozenRoot
        if (-not (Test-Path -LiteralPath (Join-Path $testOutput 'results.trx') -PathType Leaf)) { throw "Test project $index produced no TRX." }
    }
    $management = Join-Path $runRoot 'management-tests.json'
    Invoke-CheckedCommand 'management-tests' $python @($validator, 'management-tests', '--source-root', $frozenRoot, '--output', $management) $frozenRoot
    Invoke-CheckedCommand 'test-contract' $python @($validator, 'test-contract', '--trx-dir', $trxRoot,
        '--management-results', $management) $frozenRoot
    $null = Assert-CleanSource $repoRoot $head
    $null = Assert-CleanSource $frozenRoot $head
    Invoke-CheckedCommand 'retail-publish' $pwsh @('-NoProfile', '-File', (Join-Path $frozenRoot 'scripts\publish-aot-retail.ps1'),
        '-Platform', $Platform, '-DotNetPath', $dotnet) $frozenRoot
    $retailRoot = Join-Path $frozenRoot ".artifacts\aot-retail\$rid"
    $summary = Join-Path $retailRoot 'summary.json'
    $retailEvidence = Join-Path $runRoot 'retail-evidence.json'
    Invoke-CheckedCommand 'retail-contract' $python @($validator, 'retail', '--source-root', $frozenRoot,
        '--retail-summary', $summary, '--platform', $Platform, '--commit', $head, '--output', $retailEvidence) $frozenRoot
    Assert-SafeDeskCuePath $runRoot $retailEvidence
    $evidence = Get-Content -LiteralPath $retailEvidence -Raw | ConvertFrom-Json
    $architecture = if ($Platform -eq 'ARM64') { 'arm64' } else { 'x64' }
    $installerScript = if ($Platform -eq 'ARM64') { 'DeskCue.arm64.iss' } else { 'DeskCue.iss' }
    $packages = Join-Path $runRoot 'packages'
    Assert-SafeDeskCuePath $runRoot $packages
    New-Item -ItemType Directory -Path $packages -Force | Out-Null
    $installerName = "DeskCue_Setup_$($config.productVersion)_$architecture"
    Assert-SafeDeskCuePath $frozenRoot $evidence.payloadDirectory
    Assert-SafeDeskCuePath $frozenRoot (Join-Path $frozenRoot "installer\$installerScript")
    Invoke-CheckedCommand 'installer' $iscc @('/DDeskCueNativeAot=1', '/DDeskCueBundledRuntime=1',
        "/DMyAppReleaseDir=$($evidence.payloadDirectory)", "/F$installerName", "/O$packages", '/Qp',
        (Join-Path $frozenRoot "installer\$installerScript")) $frozenRoot
    $null = Assert-CleanSource $repoRoot $head
    $null = Assert-CleanSource $frozenRoot $head
    $resultPath = Join-Path $runRoot 'run-result.json'
    Invoke-CheckedCommand 'complete-contract' $python @($validator, 'complete', '--source-root', $frozenRoot,
        '--retail-summary', $summary, '--platform', $Platform, '--commit', $head,
        '--installer', (Join-Path $packages "$installerName.exe"), '--trx-dir', $trxRoot,
        '--management-results', $management, '--release-root', $releaseRoot,
        '--retail-evidence', $retailEvidence, '--output', $resultPath) $frozenRoot
    [pscustomobject]@{
        Receipt = Join-Path $releaseRoot 'receipt.json'; Installer = Join-Path $releaseRoot "$installerName.exe"
        PayloadDirectory = $evidence.payloadDirectory; RunResult = $resultPath; RuntimeIdentifier = $rid
    }
}
finally {
    foreach ($entry in $environmentBefore.GetEnumerator()) {
        [Environment]::SetEnvironmentVariable($entry.Key, $entry.Value, 'Process')
    }
    $releaseLock.Dispose()
}
