[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^v[0-9]+\.[0-9]+\.[0-9]+$')]
    [string] $UpstreamRef,

    [ValidatePattern('^[0-9a-f]{40}$')]
    [string] $UpstreamCommit,

    [ValidatePattern('^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$')]
    [string] $Version,

    [Parameter(Mandatory = $true)]
    [string] $Destination,

    [string] $OutputDirectory,
    [string] $SourceRoot = (Split-Path -Parent $PSScriptRoot),
    [string] $PythonPath = 'python'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$sourceDirectory = (Resolve-Path -LiteralPath $SourceRoot).Path
$branch = & git -C $sourceDirectory branch --show-current
if ($LASTEXITCODE -ne 0) { throw 'Cannot determine the source Git branch.' }
Write-Host "DeskCue source: $sourceDirectory; branch: $branch"
if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = "$Destination-delivery"
}
$arguments = @(
    (Join-Path $PSScriptRoot 'delivery.py'), 'sync', '--root', $sourceDirectory,
    '--upstream-ref', $UpstreamRef, '--destination', $Destination,
    '--output-dir', $OutputDirectory
)
if (-not [string]::IsNullOrWhiteSpace($UpstreamCommit)) { $arguments += @('--upstream-commit', $UpstreamCommit) }
if (-not [string]::IsNullOrWhiteSpace($Version)) { $arguments += @('--version', $Version) }
& $PythonPath @arguments
if ($LASTEXITCODE -ne 0) {
    throw 'DeskCue source candidate failed validation. The original branch was not promoted.'
}
Write-Host "Candidate ready in $Destination. Review and build it before explicit promotion; nothing was installed."
