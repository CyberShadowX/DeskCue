#Requires -Version 7.0
<#
.SYNOPSIS
Initialize or verify the pinned project-local DeskCue build tools.
.DESCRIPTION
Uses the MAIN checkout's .deskcue-tools directory, including when called from a
nested linked worktree. Downloads are verified before extraction/execution.
All caches, staging and logs stay inside the main checkout. Environment changes
are process-only and restored on success or failure. No application is started.
.PARAMETER ValidateOnly
Verify existing installation manifests and CLI versions without downloads,
installers or receipt replacement. The Inno probe uses a private local temp
directory and disables installer output. Missing tools fail without setup.
.PARAMETER Proxy
Optional HTTP(S) proxy URI without embedded credentials; used only in this
process. For example: -Proxy http://127.0.0.1:10808
#>
[CmdletBinding()]
param([string]$SourceRoot = '', [switch]$ValidateOnly, [uri]$Proxy)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false
Set-StrictMode -Version Latest
if (-not $IsWindows -or [Runtime.InteropServices.RuntimeInformation]::OSArchitecture -ne 'X64') {
    throw 'This bootstrap installs Windows x64 host tools; use a Windows x64 machine.'
}
$implementationRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $implementationRoot 'deskcue/LocalEnvironment.ps1')
. (Join-Path $implementationRoot 'deskcue/bootstrap.ps1')
$source = if ($SourceRoot) { $SourceRoot } else { $implementationRoot }
$environment = Get-DeskCueLocalEnvironment -SourceRoot $source
$branch = (& git -C $environment.SourceRoot branch --show-current 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0) { throw 'Unable to confirm the source branch before initialization.' }
Write-Host "DeskCue source: $($environment.SourceRoot); branch: $($branch.Trim())"
Write-Host "DeskCue main checkout: $($environment.CanonicalRoot)"
Invoke-DeskCueBootstrapInitialization -Environment $environment -ValidateOnly:$ValidateOnly -Proxy $Proxy
