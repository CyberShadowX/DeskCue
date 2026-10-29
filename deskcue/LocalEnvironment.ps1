#Requires -Version 7.0
<#
Project-owned build tools and caches belong to the main Git checkout. Linked
worktrees inside that checkout share its toolchain. This file has no setup or
environment side effects when dot-sourced.
#>

function Assert-DeskCueLocalPath {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][string]$Path,
          [switch]$AllowInternalFileLink)

    foreach ($value in @($Root, $Path)) {
        if ($value -match '^[\\/]{2}[?.][\\/]' -or ($value -split '[\\/]') -contains '..') {
            throw 'Device aliases and parent traversal are not safe local environment paths.'
        }
    }
    $boundary = [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $candidate = [IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
    $prefix = $boundary + [IO.Path]::DirectorySeparatorChar
    if (-not $candidate.Equals($boundary, [StringComparison]::OrdinalIgnoreCase) -and
        -not $candidate.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Local environment path escaped its intended project root.'
    }
    $part = $candidate
    while ($part) {
        $entry = Get-Item -LiteralPath $part -Force -ErrorAction SilentlyContinue
        if ($null -ne $entry) {
            if (($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                if (-not $AllowInternalFileLink -or $entry.PSIsContainer -or
                    -not $part.Equals($candidate, [StringComparison]::OrdinalIgnoreCase) -or
                    $entry.LinkType -cne 'SymbolicLink' -or [string]::IsNullOrWhiteSpace($entry.LinkTarget)) {
                    throw 'Local environment path contains a symlink, junction or reparse point.'
                }
                # This opt-in is only for reading rustup's executable shims.
                # Write destinations continue to reject every file link.
                $linkTarget = if ([IO.Path]::IsPathRooted($entry.LinkTarget)) { $entry.LinkTarget }
                    else { Join-Path $entry.DirectoryName $entry.LinkTarget }
                Assert-DeskCueLocalPath -Root $Root -Path $linkTarget
                if (-not (Test-Path -LiteralPath $linkTarget -PathType Leaf)) {
                    throw 'Internal file link must target an existing ordinary file.'
                }
            }
            if (-not $part.Equals($candidate, [StringComparison]::OrdinalIgnoreCase) -and -not $entry.PSIsContainer) {
                throw 'A local environment parent must be an ordinary directory.'
            }
        }
        $parent = [IO.Directory]::GetParent($part)
        $part = if ($null -eq $parent) { $null } else { $parent.FullName }
    }
}

function Get-DeskCueLocalEnvironment {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$SourceRoot, [string]$RunRoot = '')

    Assert-DeskCueLocalPath -Root $SourceRoot -Path $SourceRoot
    $source = [IO.Path]::GetFullPath($SourceRoot).TrimEnd('\', '/')
    if (-not (Test-Path -LiteralPath $source -PathType Container)) { throw 'SourceRoot must be a Git checkout directory.' }
    $actualRoot = & git -C $source rev-parse --show-toplevel 2>&1
    if ($LASTEXITCODE -ne 0 -or -not [IO.Path]::GetFullPath(($actualRoot -join "`n").Trim()).TrimEnd('\', '/').Equals(
            $source, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'SourceRoot must identify the exact Git checkout root.'
    }
    $common = & git -C $source rev-parse --path-format=absolute --git-common-dir 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'Unable to resolve the main Git checkout.' }
    $common = [IO.Path]::GetFullPath(($common -join "`n").Trim()).TrimEnd('\', '/')
    if ([IO.Path]::GetFileName($common) -cne '.git' -or -not (Test-Path -LiteralPath $common -PathType Container)) {
        throw 'The project must use an ordinary main .git directory.'
    }
    $canonical = [IO.Directory]::GetParent($common).FullName
    Assert-DeskCueLocalPath -Root $canonical -Path $common
    Assert-DeskCueLocalPath -Root $canonical -Path $source
    $toolRoot = Join-Path $canonical '.deskcue-tools'
    $paths = [ordered]@{
        DotNetRoot = Join-Path $toolRoot 'dotnet'
        DotNetHome = Join-Path $toolRoot 'dotnet-home'
        NuGetPackages = Join-Path $toolRoot 'nuget/packages'
        NuGetHttpCache = Join-Path $toolRoot 'nuget/http-cache'
        NuGetPluginsCache = Join-Path $toolRoot 'nuget/plugins-cache'
        CargoHome = Join-Path $toolRoot 'cargo'
        CargoBin = Join-Path $toolRoot 'cargo/bin'
        RustupHome = Join-Path $toolRoot 'rustup'
        MSBuildUserExtensions = Join-Path $toolRoot 'msbuild'
        Downloads = Join-Path $toolRoot 'downloads'
        Temp = Join-Path $toolRoot 'tmp'
    }
    if ($RunRoot) {
        Assert-DeskCueLocalPath -Root $canonical -Path $RunRoot
        $paths.Temp = Join-Path ([IO.Path]::GetFullPath($RunRoot)) 'tmp'
    }
    Assert-DeskCueLocalPath -Root $canonical -Path $toolRoot
    foreach ($path in $paths.Values) {
        Assert-DeskCueLocalPath -Root $canonical -Path $path
        if ((Test-Path -LiteralPath $path) -and -not (Test-Path -LiteralPath $path -PathType Container)) {
            throw 'A local environment directory is occupied by a file.'
        }
    }
    # Validate the PATH directory and its executable links before exposing it.
    # rustup creates ordinary files or file shims to rustup.exe, never a reason
    # to accept a directory junction or a shim pointing outside this toolchain.
    if (Test-Path -LiteralPath $paths.CargoBin -PathType Container) {
        foreach ($entry in Get-ChildItem -LiteralPath $paths.CargoBin -Force -ErrorAction Stop) {
            Assert-DeskCueLocalPath -Root $toolRoot -Path $entry.FullName -AllowInternalFileLink
        }
    }
    $processValues = [ordered]@{
        DOTNET_ROOT = $paths.DotNetRoot
        DOTNET_CLI_HOME = $paths.DotNetHome
        DOTNET_ADD_GLOBAL_TOOLS_TO_PATH = '0'
        DOTNET_CLI_TELEMETRY_OPTOUT = '1'
        DOTNET_GENERATE_ASPNET_CERTIFICATE = 'false'
        DOTNET_NOLOGO = '1'
        NUGET_PACKAGES = $paths.NuGetPackages
        NUGET_HTTP_CACHE_PATH = $paths.NuGetHttpCache
        NUGET_PLUGINS_CACHE_PATH = $paths.NuGetPluginsCache
        CARGO_HOME = $paths.CargoHome
        RUSTUP_HOME = $paths.RustupHome
        MSBUILDUSEREXTENSIONSPATH = $paths.MSBuildUserExtensions
        TEMP = $paths.Temp
        TMP = $paths.Temp
        DESKCUE_TEST_TEMP_ROOT = Join-Path $paths.Temp 'release-tests'
        PATH = (@($paths.DotNetRoot, $paths.CargoBin, $env:PATH) -join [IO.Path]::PathSeparator)
    }
    [pscustomobject]@{
        SourceRoot = $source; CanonicalRoot = $canonical; ToolRoot = $toolRoot
        Paths = $paths; ProcessValues = $processValues
    }
}

function Restore-DeskCueProcessEnvironment {
    [CmdletBinding()]
    param([Parameter(Mandatory)][Collections.IDictionary]$Snapshot)
    foreach ($entry in $Snapshot.GetEnumerator()) {
        $value = if ($null -eq $entry.Value) { [NullString]::Value } else { [string]$entry.Value }
        [Environment]::SetEnvironmentVariable([string]$entry.Key, $value, 'Process')
    }
}

function Push-DeskCueProcessEnvironment {
    [CmdletBinding()]
    param([Parameter(Mandatory)][Collections.IDictionary]$Values)
    $snapshot = @{}
    foreach ($key in $Values.Keys) {
        if ([string]::IsNullOrWhiteSpace([string]$key) -or [string]$key -match '[=\x00]') {
            throw 'Invalid process environment variable name.'
        }
        $snapshot[$key] = [Environment]::GetEnvironmentVariable([string]$key, 'Process')
    }
    try {
        foreach ($entry in $Values.GetEnumerator()) {
            $value = if ($null -eq $entry.Value) { [NullString]::Value } else { [string]$entry.Value }
            [Environment]::SetEnvironmentVariable([string]$entry.Key, $value, 'Process')
        }
    }
    catch {
        Restore-DeskCueProcessEnvironment -Snapshot $snapshot
        throw
    }
    return $snapshot
}

function Invoke-WithDeskCueEnvironment {
    [CmdletBinding()]
    param([Parameter(Mandatory)][Collections.IDictionary]$Values,
          [Parameter(Mandatory)][scriptblock]$Operation)
    $snapshot = Push-DeskCueProcessEnvironment -Values $Values
    try { & $Operation }
    finally { Restore-DeskCueProcessEnvironment -Snapshot $snapshot }
}
