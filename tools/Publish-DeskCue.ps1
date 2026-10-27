#Requires -Version 7.0
<#
.SYNOPSIS
Build, validate, and safely replace the local DeskCue retail directory.
.DESCRIPTION
The previous release is preserved in the ignored evidence directory. A running
DeskCue under 发布版 blocks replacement; exit it from its tray menu and retry.
The complete offline runtime and installer are copied only after the shared
build has produced a validated successful receipt. Nothing is installed/launched.
#>
[CmdletBinding()]
param(
    [ValidateSet('x64', 'ARM64')][string]$Platform = 'x64',
    [string]$DotNetPath = '',
    [string]$IsccPath = '',
    [string]$SourceRoot = '',
    # Dependency seams keep orchestration independently verifiable. The ordinary
    # path always invokes the shared builder and the filesystem directory move.
    [scriptblock]$BuildOperation,
    [scriptblock]$MoveDirectoryOperation
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest

$python = (Get-Command python -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
$pathValidator = Join-Path (Split-Path -Parent $PSScriptRoot) 'deskcue\release_contract.py'
function Assert-SafeDeskCuePath {
    param([string]$Root, [string]$Path)
    & $script:python $script:pathValidator guard-path --root $Root --path $Path
    if ($LASTEXITCODE -ne 0) { throw 'Unsafe release path: containment/link/reparse validation failed.' }
}
$inputRoot = if ($SourceRoot) { $SourceRoot } else { Split-Path -Parent $PSScriptRoot }
Assert-SafeDeskCuePath $inputRoot $inputRoot
Assert-SafeDeskCuePath (Split-Path -Parent $PSScriptRoot) $pathValidator
$repoRoot = [IO.Path]::GetFullPath($inputRoot)
$target = Join-Path $repoRoot '发布版'
Assert-SafeDeskCuePath $repoRoot $target
Assert-SafeDeskCuePath $repoRoot (Join-Path $repoRoot '.artifacts\deskcue-release')
if ($null -eq $BuildOperation) { $BuildOperation = { param($Wrapper, $Parameters) & $Wrapper @Parameters } }
if ($null -eq $MoveDirectoryOperation) { $MoveDirectoryOperation = { param($From, $To) [IO.Directory]::Move($From, $To) } }

function Invoke-SafeDeskCueMove {
    param([string]$From, [string]$To)
    Assert-SafeDeskCuePath $repoRoot $From
    Assert-SafeDeskCuePath $repoRoot $To
    & $MoveDirectoryOperation $From $To
    Assert-SafeDeskCuePath $repoRoot $To
}

function Assert-TargetStopped {
    Assert-SafeDeskCuePath $repoRoot $target
    if (Test-Path -LiteralPath $target) {
        $attributes = (Get-Item -LiteralPath $target -Force).Attributes
        if ($attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'The release target must not be a link or reparse point.' }
    }
    foreach ($process in @(Get-Process -Name 'DeskCue', 'DeskCue.Updater', 'DeskCue.ThumbnailProxy' -ErrorAction SilentlyContinue)) {
        try { $image = $process.Path }
        catch { throw '无法确认 DeskCue 的运行路径。请从系统托盘“退出 DeskCue”后重试。' }
        if (-not $image) { throw '无法确认 DeskCue 的运行路径。请从系统托盘“退出 DeskCue”后重试。' }
        if ([IO.Path]::GetFullPath($image).StartsWith($target.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar,
                [StringComparison]::OrdinalIgnoreCase)) {
            throw '发布版中的 DeskCue 正在运行，已阻止替换。请从系统托盘“退出 DeskCue”后重试。'
        }
    }
}

# Verify the repository and branch before creating or replacing files.
$actualRoot = (& git -C $repoRoot rev-parse --show-toplevel 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0 -or -not [IO.Path]::GetFullPath($actualRoot.Trim()).Equals($repoRoot.TrimEnd('\', '/'), [StringComparison]::OrdinalIgnoreCase)) {
    throw 'SourceRoot must identify the repository root.'
}
$branch = (& git -C $repoRoot branch --show-current 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0) { throw 'Unable to inspect the source branch.' }
Write-Host "DeskCue local publish: $repoRoot; branch: $($branch.Trim())"
Assert-TargetStopped

$parameters = @{ Platform = $Platform; SourceRoot = $repoRoot }
if ($DotNetPath) { $parameters['DotNetPath'] = $DotNetPath }
if ($IsccPath) { $parameters['IsccPath'] = $IsccPath }
$builder = Join-Path $repoRoot 'deskcue\Build-DeskCue.ps1'
Assert-SafeDeskCuePath $repoRoot $builder
$result = & $BuildOperation $builder $parameters
if ($null -eq $result -or -not $result.RunResult) {
    throw 'The shared build did not return verified run evidence.'
}

$rid = $result.RuntimeIdentifier
$expectedRid = if ($Platform -eq 'ARM64') { 'win-arm64' } else { 'win-x64' }
if ($rid -cne $expectedRid) { throw 'The shared build returned an unexpected platform.' }
$releaseRoot = Join-Path $repoRoot ".artifacts\deskcue-release\$rid"
Assert-SafeDeskCuePath $repoRoot $releaseRoot
Assert-SafeDeskCuePath $releaseRoot $result.RunResult
Assert-SafeDeskCuePath $releaseRoot $result.Installer
if (-not (Test-Path -LiteralPath $result.RunResult -PathType Leaf)) { throw 'The shared build run evidence is missing.' }
$lockPath = Join-Path $repoRoot '.artifacts\deskcue-release\local-publish.lock'
Assert-SafeDeskCuePath $repoRoot $lockPath
$publishLock = [IO.File]::Open($lockPath,
    [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
try {
    $runRoot = Split-Path -Parent $result.RunResult
    $staging = [IO.Path]::GetFullPath((Join-Path $runRoot 'local-release-staging'))
    $backup = [IO.Path]::GetFullPath((Join-Path $runRoot 'previous-local-release'))
    foreach ($candidate in @($staging, $backup)) {
        Assert-SafeDeskCuePath $releaseRoot $candidate
    }
    Assert-SafeDeskCuePath $repoRoot (Join-Path $repoRoot 'deskcue\release_contract.py')
    & $python (Join-Path $repoRoot 'deskcue\release_contract.py') stage-local --result $result.RunResult --destination $staging
    if ($LASTEXITCODE -ne 0) { throw "Local release staging failed with exit $LASTEXITCODE; the previous release is unchanged." }
    Assert-TargetStopped
    $movedPrevious = $false
    try {
        if (Test-Path -LiteralPath $target) {
            if (-not (Test-Path -LiteralPath $target -PathType Container)) { throw 'The local release target is not a directory.' }
            Invoke-SafeDeskCueMove $target $backup
            $movedPrevious = $true
        }
        Invoke-SafeDeskCueMove $staging $target
    }
    catch {
        Assert-SafeDeskCuePath $repoRoot $target
        Assert-SafeDeskCuePath $releaseRoot $backup
        if ($movedPrevious -and -not (Test-Path -LiteralPath $target)) { Invoke-SafeDeskCueMove $backup $target }
        throw
    }
    [pscustomobject]@{
        ReleaseDirectory = $target; Executable = Join-Path $target 'DeskCue.exe'
        Installer = Join-Path $target (Split-Path -Leaf $result.Installer)
        Receipt = Join-Path $target 'receipt.json'
        PreviousRelease = if ($movedPrevious) { $backup } else { $null }
    }
}
finally { $publishLock.Dispose() }
