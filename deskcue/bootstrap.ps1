#Requires -Version 7.0
<#
Bootstrap implementation. Dot-sourcing has no setup, network or environment side
effects. Dependency seams are for offline behavioral checks; the CLI uses the
fixed pins below and the ordinary HTTP, archive and executable implementations.
#>

function Get-DeskCueBootstrapPins {
    [ordered]@{
        DotNet = [ordered]@{
            Version = '10.0.402'; FileName = 'dotnet-sdk-10.0.402-win-x64.zip'; Algorithm = 'SHA512'
            Uri = 'https://builds.dotnet.microsoft.com/dotnet/Sdk/10.0.402/dotnet-sdk-10.0.402-win-x64.zip'
            Hash = 'AE4FD528CB7E9F6AF6AAF7DE36715A69F761F183744F1BB3025D19F5A92447090EC561410E46266C1D10A63781ED6F3DE771760BC76C876D87DAABC367B898CD'
            Source = 'https://builds.dotnet.microsoft.com/dotnet/release-metadata/10.0/releases.json'
        }
        Rustup = [ordered]@{
            Version = '1.29.2'; FileName = 'rustup-init-1.29.2-x86_64-pc-windows-msvc.exe'; Algorithm = 'SHA256'
            Uri = 'https://static.rust-lang.org/rustup/archive/1.29.2/x86_64-pc-windows-msvc/rustup-init.exe'
            Hash = '00F139DA614DCED87D3C3D4121C43EEBDAC3C1BF8A5EE86B9D80DFD71C8D70FD'
            Source = 'https://static.rust-lang.org/rustup/archive/1.29.2/x86_64-pc-windows-msvc/rustup-init.exe.sha256'
        }
        RustVersion = '1.96.0'
        RustHost = 'x86_64-pc-windows-msvc'
        RustComponents = @('clippy', 'rustfmt')
        RustTargets = @('x86_64-pc-windows-msvc', 'aarch64-pc-windows-msvc')
        Inno = [ordered]@{
            Version = '6.7.3'; FileName = 'innosetup-6.7.3.exe'; Algorithm = 'SHA256'
            Uri = 'https://github.com/jrsoftware/issrc/releases/download/is-6_7_3/innosetup-6.7.3.exe'
            Hash = '9C73C3BAE7ED48D44112A0F48E66742C00090BDB5BEF71D9D3C056C66E97B732'
            Source = 'https://github.com/jrsoftware/issrc/releases/tag/is-6_7_3'
        }
    }
}

function Assert-DeskCueBootstrapSourcePins {
    param([string]$SourceRoot, [Collections.IDictionary]$Pins)
    $sdk = Get-Content -LiteralPath (Join-Path $SourceRoot 'global.json') -Raw | ConvertFrom-Json
    if ($sdk.sdk.version -cne $Pins.DotNet.Version -or $sdk.sdk.rollForward -cne 'disable' -or
            $sdk.sdk.allowPrerelease -ne $false) {
        throw 'Bootstrap SDK pins differ from global.json; review the bootstrap pins before setup.'
    }
    $rust = Get-Content -LiteralPath (Join-Path $SourceRoot 'rust-toolchain.toml') -Raw
    foreach ($pair in @(@('channel', $Pins.RustVersion), @('profile', 'minimal'))) {
        if ($rust -notmatch ('(?m)^\s*' + $pair[0] + '\s*=\s*"' + [regex]::Escape($pair[1]) + '"\s*$')) {
            throw 'Bootstrap Rust pins differ from rust-toolchain.toml.'
        }
    }
    foreach ($pair in @(@('components', $Pins.RustComponents), @('targets', $Pins.RustTargets))) {
        $match = [regex]::Match($rust, '(?ms)^\s*' + $pair[0] + '\s*=\s*\[(?<values>[^\]]*)\]')
        $actual = @([regex]::Matches($match.Groups['values'].Value, '"([^"]+)"') | ForEach-Object { $_.Groups[1].Value } | Sort-Object)
        $expected = @($pair[1] | Sort-Object)
        if (-not $match.Success -or ($actual -join '|') -cne ($expected -join '|')) {
            throw 'Bootstrap Rust components or targets differ from rust-toolchain.toml.'
        }
    }
}

function Get-DeskCueBootstrapDownload {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][Collections.IDictionary]$Pin,
          [uri]$Proxy, [switch]$ValidateOnly, [scriptblock]$DownloadOperation)
    if ($Pin.FileName -cnotmatch '^[A-Za-z0-9][A-Za-z0-9._-]+$' -or $Pin.Algorithm -notin @('SHA256', 'SHA512')) {
        throw 'Invalid bootstrap download filename or digest algorithm.'
    }
    $hashLength = if ($Pin.Algorithm -eq 'SHA512') { 128 } else { 64 }
    if ($Pin.Hash -notmatch ('^[a-fA-F0-9]{' + $hashLength + '}$') -or
            ([uri]$Pin.Uri).Scheme -ne 'https' -or ([uri]$Pin.Uri).UserInfo) {
        throw 'Invalid bootstrap HTTPS source or checksum.'
    }
    $downloads = Join-Path $Root 'downloads'
    $destination = Join-Path $downloads $Pin.FileName
    Assert-DeskCueLocalPath -Root $Root -Path $destination
    if (Test-Path -LiteralPath $destination -PathType Leaf) {
        if ((Get-FileHash -LiteralPath $destination -Algorithm $Pin.Algorithm).Hash -ieq $Pin.Hash) { return $destination }
    }
    if ($ValidateOnly) { throw "A verified bootstrap download is missing: $($Pin.FileName)" }
    New-Item -ItemType Directory -Path $downloads -Force | Out-Null
    $partial = Join-Path $downloads ($Pin.FileName + '.' + [Guid]::NewGuid().ToString('N') + '.partial')
    Assert-DeskCueLocalPath -Root $Root -Path $partial
    try {
        if ($null -ne $DownloadOperation) { & $DownloadOperation $Pin.Uri $partial $Proxy | Out-Null }
        else {
            $parameters = @{ Uri = $Pin.Uri; OutFile = $partial; ErrorAction = 'Stop'; MaximumRedirection = 5 }
            if ($null -ne $Proxy) { $parameters.Proxy = $Proxy }
            Invoke-WebRequest @parameters | Out-Null
        }
        Assert-DeskCueLocalPath -Root $Root -Path $partial
        if (-not (Test-Path -LiteralPath $partial -PathType Leaf) -or
                (Get-FileHash -LiteralPath $partial -Algorithm $Pin.Algorithm).Hash -ine $Pin.Hash) {
            throw "Bootstrap download checksum mismatch: $($Pin.FileName)"
        }
        Assert-DeskCueLocalPath -Root $Root -Path $destination
        [IO.File]::Move($partial, $destination, $true)
        return $destination
    }
    finally {
        if (Test-Path -LiteralPath $partial) {
            Assert-DeskCueLocalPath -Root $Root -Path $partial
            Remove-Item -LiteralPath $partial -Force
        }
    }
}

function Write-DeskCueBootstrapJson {
    param([string]$Root, [string]$Path, [object]$Value)
    Assert-DeskCueLocalPath -Root $Root -Path $Path
    New-Item -ItemType Directory -Path (Split-Path -Parent $Path) -Force | Out-Null
    $partial = $Path + '.' + [Guid]::NewGuid().ToString('N') + '.partial'
    Assert-DeskCueLocalPath -Root $Root -Path $partial
    try {
        [IO.File]::WriteAllText($partial, ($Value | ConvertTo-Json -Depth 8), [Text.UTF8Encoding]::new($false))
        Assert-DeskCueLocalPath -Root $Root -Path $Path
        [IO.File]::Move($partial, $Path, $true)
    }
    finally {
        if (Test-Path -LiteralPath $partial) {
            Assert-DeskCueLocalPath -Root $Root -Path $partial
            Remove-Item -LiteralPath $partial -Force
        }
    }
}

function Move-DeskCueBootstrapDirectories {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$Root,
          [Parameter(Mandatory)][Collections.IDictionary]$Directories, [scriptblock]$MoveOperation)
    if ($null -eq $MoveOperation) { $MoveOperation = { param($From, $To) [IO.Directory]::Move($From, $To) } }
    foreach ($entry in $Directories.GetEnumerator()) {
        foreach ($path in @([string]$entry.Key, [string]$entry.Value)) {
            Assert-DeskCueLocalPath -Root $Root -Path $path
            if ([IO.Path]::GetFullPath($path).TrimEnd('\', '/') -ieq [IO.Path]::GetFullPath($Root).TrimEnd('\', '/')) {
                throw 'A bootstrap directory cannot replace its tool root.'
            }
        }
        if (-not (Test-Path -LiteralPath $entry.Value -PathType Container) -or
                (Test-Path -LiteralPath $entry.Key -PathType Leaf)) { throw 'Invalid bootstrap promotion directories.' }
    }
    $previousRoot = Join-Path $Root ('bootstrap/previous/' + [Guid]::NewGuid().ToString('N'))
    Assert-DeskCueLocalPath -Root $Root -Path $previousRoot
    New-Item -ItemType Directory -Path $previousRoot -Force | Out-Null
    $states = [Collections.Generic.List[object]]::new()
    try {
        foreach ($entry in $Directories.GetEnumerator()) {
            $state = [pscustomobject]@{
                Active = [string]$entry.Key; Candidate = [string]$entry.Value
                Previous = Join-Path $previousRoot ([IO.Path]::GetFileName([string]$entry.Key)); Promoted = $false; Saved = $false
            }
            $states.Add($state)
            Assert-DeskCueLocalPath -Root $Root -Path $state.Active
            Assert-DeskCueLocalPath -Root $Root -Path $state.Previous
            if (Test-Path -LiteralPath $state.Active -PathType Container) {
                & $MoveOperation $state.Active $state.Previous
                $state.Saved = $true
            }
            Assert-DeskCueLocalPath -Root $Root -Path $state.Candidate
            & $MoveOperation $state.Candidate $state.Active
            $state.Promoted = $true
        }
    }
    catch {
        $failure = $_
        for ($index = $states.Count - 1; $index -ge 0; $index--) {
            $state = $states[$index]
            if ($state.Promoted) {
                Assert-DeskCueLocalPath -Root $Root -Path $state.Active
                Assert-DeskCueLocalPath -Root $Root -Path $state.Candidate
                & $MoveOperation $state.Active $state.Candidate
            }
            if ($state.Saved) {
                Assert-DeskCueLocalPath -Root $Root -Path $state.Previous
                Assert-DeskCueLocalPath -Root $Root -Path $state.Active
                & $MoveOperation $state.Previous $state.Active
            }
        }
        throw $failure
    }
    # Previous versions remain inside the project for recovery; never delete an
    # existing tool installation merely because a new candidate was promoted.
}

function Test-DeskCueBootstrapRustShimPath {
    param([string]$Root, [string]$Path)
    $relative = [IO.Path]::GetRelativePath([IO.Path]::GetFullPath($Root), [IO.Path]::GetFullPath($Path)).Replace('\', '/')
    # Only rustup's direct executable shims may be contained file links. SDK,
    # Inno and Rust toolchain payload files retain the ordinary-file boundary.
    return $relative -match '^(?:cargo/bin|tmp/bootstrap-rust-[a-f0-9]{32}/cargo/bin)/[^/]+\.exe$'
}

function Invoke-DeskCueBootstrapCommand {
    [CmdletBinding()]
    param([Parameter(Mandatory)][object]$Environment, [Parameter(Mandatory)][string]$Executable,
          [string[]]$Arguments = @(), [string]$WorkingDirectory = '', [string]$LogPath = '',
          [scriptblock]$ExecuteOperation)
    $allowRustShim = Test-DeskCueBootstrapRustShimPath -Root $Environment.ToolRoot -Path $Executable
    Assert-DeskCueLocalPath -Root $Environment.ToolRoot -Path $Executable -AllowInternalFileLink:$allowRustShim
    if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { throw "A bootstrap executable is missing: $([IO.Path]::GetFileName($Executable))" }
    $working = if ($WorkingDirectory) { $WorkingDirectory } else { $Environment.SourceRoot }
    Assert-DeskCueLocalPath -Root $Environment.CanonicalRoot -Path $working
    if ($LogPath) { Assert-DeskCueLocalPath -Root $Environment.ToolRoot -Path $LogPath }
    if ($null -eq $ExecuteOperation) {
        $ExecuteOperation = {
            param($Command, $CommandArguments)
            $lines = @(& $Command @CommandArguments 2>&1 | ForEach-Object { $_.ToString() })
            [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = $lines -join "`n" }
        }
    }
    # These protections are applied before EVERY dotnet invocation, including
    # an installed-tool version probe and the staged SDK's first invocation.
    $protections = @{
        DOTNET_ADD_GLOBAL_TOOLS_TO_PATH = '0'; DOTNET_CLI_TELEMETRY_OPTOUT = '1'
        DOTNET_GENERATE_ASPNET_CERTIFICATE = 'false'; DOTNET_NOLOGO = '1'
    }
    $result = Invoke-WithDeskCueEnvironment -Values $protections -Operation {
        Push-Location -LiteralPath $working
        try { & $ExecuteOperation $Executable $Arguments }
        finally { Pop-Location }
    }
    if ($null -eq $result -or $null -eq $result.ExitCode -or $null -eq $result.Output) {
        throw 'A bootstrap command did not return an exit code and output.'
    }
    if ($LogPath) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $LogPath) -Force | Out-Null
        [IO.File]::WriteAllText($LogPath, ([string]$result.Output), [Text.UTF8Encoding]::new($false))
    }
    if ($result.ExitCode -ne 0) { throw "Bootstrap command failed with exit $($result.ExitCode): $([IO.Path]::GetFileName($Executable))" }
    return [string]$result.Output
}

function Get-DeskCueBootstrapFileManifest {
    param([string]$Root, [string[]]$Directories)
    $files = [ordered]@{}
    $pending = [Collections.Generic.Stack[string]]::new()
    foreach ($directory in $Directories) {
        Assert-DeskCueLocalPath -Root $Root -Path $directory
        if (-not (Test-Path -LiteralPath $directory -PathType Container)) { throw 'An installed bootstrap directory is missing.' }
        $pending.Push($directory)
    }
    while ($pending.Count -gt 0) {
        foreach ($entry in @(Get-ChildItem -LiteralPath $pending.Pop() -Force)) {
            $allowRustShim = Test-DeskCueBootstrapRustShimPath -Root $Root -Path $entry.FullName
            Assert-DeskCueLocalPath -Root $Root -Path $entry.FullName -AllowInternalFileLink:$allowRustShim
            if ($entry.PSIsContainer) { $pending.Push($entry.FullName) }
            else {
                $relative = [IO.Path]::GetRelativePath($Root, $entry.FullName).Replace('\', '/')
                $files[$relative] = (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash
            }
        }
    }
    return $files
}

function Test-DeskCueBootstrapInstallation {
    param([string]$Root, [string]$Name, [string]$Version, [string]$ArchiveHash, [string[]]$Directories)
    $receiptPath = Join-Path $Root "bootstrap/$Name.json"
    Assert-DeskCueLocalPath -Root $Root -Path $receiptPath
    if (-not (Test-Path -LiteralPath $receiptPath -PathType Leaf)) { return $false }
    try {
        $receipt = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json -AsHashtable
        if ($receipt.SchemaVersion -ne 1 -or $receipt.Version -cne $Version -or $receipt.ArchiveHash -ine $ArchiveHash -or
                $null -eq $receipt.Files -or $receipt.Files.Count -eq 0) { return $false }
        $actual = Get-DeskCueBootstrapFileManifest -Root $Root -Directories $Directories
        if ($actual.Count -ne $receipt.Files.Count) { return $false }
        foreach ($entry in $actual.GetEnumerator()) {
            if (-not $receipt.Files.Contains($entry.Key) -or $receipt.Files[$entry.Key] -ine $entry.Value) { return $false }
        }
        return $true
    }
    catch { return $false }
}

function Save-DeskCueBootstrapInstallation {
    param([string]$Root, [string]$Name, [string]$Version, [Collections.IDictionary]$Pin, [string[]]$Directories)
    $manifest = Get-DeskCueBootstrapFileManifest -Root $Root -Directories $Directories
    if ($manifest.Count -eq 0) { throw 'A bootstrap installation cannot have an empty file manifest.' }
    Write-DeskCueBootstrapJson -Root $Root -Path (Join-Path $Root "bootstrap/$Name.json") -Value ([ordered]@{
        SchemaVersion = 1; Version = $Version; ArchiveHash = $Pin.Hash; ArchiveAlgorithm = $Pin.Algorithm
        Source = $Pin.Uri; RecordedUtc = [DateTime]::UtcNow.ToString('O'); Files = $manifest
    })
}

function New-DeskCueBootstrapStage {
    param([object]$Environment, [string]$Name)
    $stage = Join-Path $Environment.Paths.Temp ('bootstrap-' + $Name + '-' + [Guid]::NewGuid().ToString('N'))
    Assert-DeskCueLocalPath -Root $Environment.ToolRoot -Path $stage
    New-Item -ItemType Directory -Path $stage -Force | Out-Null
    return $stage
}

function Test-DeskCueBootstrapVersions {
    param([object]$Environment, [string]$Tool, [Collections.IDictionary]$Pins,
          [string]$DotNetRoot = '', [string]$CargoHome = '', [string]$InnoRoot = '',
          [scriptblock]$ExecuteOperation)
    if ($Tool -eq 'dotnet') {
        $output = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable (Join-Path $DotNetRoot 'dotnet.exe') -Arguments @('--version') -ExecuteOperation $ExecuteOperation
        if ($output.Trim() -cne $Pins.DotNet.Version) { throw 'Installed SDK version differs from the bootstrap pin.' }
    }
    elseif ($Tool -eq 'rust') {
        $rustup = Join-Path $CargoHome 'bin/rustup.exe'
        $output = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable $rustup -Arguments @('--version') -ExecuteOperation $ExecuteOperation
        if ($output -notmatch ('(?m)^rustup ' + [regex]::Escape($Pins.Rustup.Version) + '\b')) { throw 'Installed rustup version differs from the bootstrap pin.' }
        foreach ($toolName in @('rustc', 'cargo')) {
            $output = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable (Join-Path $CargoHome "bin/$toolName.exe") -Arguments @("+$($Pins.RustVersion)", '--version') -ExecuteOperation $ExecuteOperation
            if ($output -notmatch ('(?m)^' + $toolName + ' ' + [regex]::Escape($Pins.RustVersion) + '\b')) { throw 'Installed Rust compiler or Cargo version differs from the bootstrap pin.' }
        }
        $components = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable $rustup -Arguments @('component', 'list', '--installed', '--toolchain', $Pins.RustVersion) -ExecuteOperation $ExecuteOperation
        foreach ($component in $Pins.RustComponents) {
            if (($components -split '\r?\n') -cnotcontains "$component-$($Pins.RustHost)") { throw 'A pinned Rust component is missing.' }
        }
        $targets = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable $rustup -Arguments @('target', 'list', '--installed', '--toolchain', $Pins.RustVersion) -ExecuteOperation $ExecuteOperation
        foreach ($target in $Pins.RustTargets) {
            if (($targets -split '\r?\n') -cnotcontains $target) { throw 'A pinned Rust standard library target is missing.' }
        }
    }
    elseif ($Tool -eq 'inno') {
        $probe = New-DeskCueBootstrapStage -Environment $Environment -Name 'inno-probe'
        $source = Join-Path $probe 'verify.iss'
        Assert-DeskCueLocalPath -Root $Environment.ToolRoot -Path $source
        [IO.File]::WriteAllText($source, "[Setup]`nAppName=DeskCue Toolchain Verification`nAppVersion=0.0.0`nDefaultDirName={tmp}\DeskCueToolchainVerification`nCreateAppDir=no`nUninstallable=no`nOutput=no`nPrivilegesRequired=lowest`n")
        $output = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable (Join-Path $InnoRoot 'ISCC.exe') -Arguments @($source) -WorkingDirectory $probe -ExecuteOperation $ExecuteOperation
        if ($output -notmatch ('Compiler engine version: Inno Setup ' + [regex]::Escape($Pins.Inno.Version) + '\b')) { throw 'Installed Inno compiler version differs from the bootstrap pin.' }
        if (@(Get-ChildItem -LiteralPath $probe -Recurse -File -Filter '*.exe').Count -ne 0) { throw 'The Inno version probe unexpectedly generated an installer.' }
        # Only the private probe script/empty Output directory are removed.
        Assert-DeskCueLocalPath -Root $Environment.ToolRoot -Path $probe
        Remove-Item -LiteralPath $probe -Recurse -Force
    }
}

function Invoke-DeskCueBootstrapInitialization {
    [CmdletBinding()]
    param([Parameter(Mandatory)][object]$Environment, [switch]$ValidateOnly, [uri]$Proxy,
          [scriptblock]$DownloadOperation, [scriptblock]$ExecuteOperation)
    $pins = Get-DeskCueBootstrapPins
    Assert-DeskCueBootstrapSourcePins -SourceRoot $Environment.SourceRoot -Pins $pins
    $root = $Environment.ToolRoot
    Assert-DeskCueLocalPath -Root $Environment.CanonicalRoot -Path $root
    if ($null -ne $Proxy -and ($Proxy.Scheme -notin @('http', 'https') -or $Proxy.UserInfo)) {
        throw 'A bootstrap proxy must be an HTTP(S) URI without embedded credentials.'
    }
    if ($ValidateOnly -and -not (Test-Path -LiteralPath $root -PathType Container)) { throw 'The project-local toolchain is not initialized.' }
    $receiptRoot = Join-Path $root 'bootstrap'
    $lockPath = Join-Path $receiptRoot 'bootstrap.lock'
    Assert-DeskCueLocalPath -Root $root -Path $lockPath
    if (-not $ValidateOnly) { New-Item -ItemType Directory -Path $receiptRoot -Force | Out-Null }
    $lock = $null
    $values = [ordered]@{}
    foreach ($entry in $Environment.ProcessValues.GetEnumerator()) { $values[$entry.Key] = $entry.Value }
    # Pin rustup's component/update origins as well as its installer. Ignore
    # inherited mirror settings for this operation and restore them in finally.
    $values.RUSTUP_DIST_SERVER = 'https://static.rust-lang.org'
    $values.RUSTUP_UPDATE_ROOT = 'https://static.rust-lang.org/rustup'
    if ($null -ne $Proxy) { $values.HTTPS_PROXY = $Proxy.AbsoluteUri; $values.HTTP_PROXY = $Proxy.AbsoluteUri }
    try {
        if (Test-Path -LiteralPath $lockPath -PathType Leaf) {
            $lock = [IO.File]::Open($lockPath, [IO.FileMode]::Open, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
        }
        elseif (-not $ValidateOnly) {
            $lock = [IO.File]::Open($lockPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
        }
        Invoke-WithDeskCueEnvironment -Values $values -Operation {
            if (-not $ValidateOnly) {
                foreach ($name in @('DotNetHome', 'NuGetPackages', 'NuGetHttpCache', 'NuGetPluginsCache', 'MSBuildUserExtensions', 'Downloads', 'Temp')) {
                    $path = $Environment.Paths[$name]
                    Assert-DeskCueLocalPath -Root $root -Path $path
                    New-Item -ItemType Directory -Path $path -Force | Out-Null
                }
            }
            $dotnetDirectories = @($Environment.Paths.DotNetRoot)
            $rustDirectories = @((Join-Path $Environment.Paths.CargoHome 'bin'),
                (Join-Path $Environment.Paths.RustupHome "toolchains/$($pins.RustVersion)-$($pins.RustHost)"))
            $innoRoot = Join-Path $root 'inno'
            if (-not (Test-DeskCueBootstrapInstallation -Root $root -Name 'dotnet' -Version $pins.DotNet.Version -ArchiveHash $pins.DotNet.Hash -Directories $dotnetDirectories)) {
                if ($ValidateOnly) { throw 'The pinned project-local SDK is missing or changed.' }
                $archive = Get-DeskCueBootstrapDownload -Root $root -Pin $pins.DotNet -Proxy $Proxy -DownloadOperation $DownloadOperation
                $stage = New-DeskCueBootstrapStage -Environment $Environment -Name 'dotnet'
                $candidate = Join-Path $stage 'dotnet'
                Assert-DeskCueLocalPath -Root $root -Path $candidate
                Expand-Archive -LiteralPath $archive -DestinationPath $candidate
                Test-DeskCueBootstrapVersions -Environment $Environment -Tool 'dotnet' -Pins $pins -DotNetRoot $candidate -ExecuteOperation $ExecuteOperation
                Move-DeskCueBootstrapDirectories -Root $root -Directories ([ordered]@{ $Environment.Paths.DotNetRoot = $candidate })
                Save-DeskCueBootstrapInstallation -Root $root -Name 'dotnet' -Version $pins.DotNet.Version -Pin $pins.DotNet -Directories $dotnetDirectories
            }
            Test-DeskCueBootstrapVersions -Environment $Environment -Tool 'dotnet' -Pins $pins -DotNetRoot $Environment.Paths.DotNetRoot -ExecuteOperation $ExecuteOperation
            if (-not (Test-DeskCueBootstrapInstallation -Root $root -Name 'rust' -Version $pins.RustVersion -ArchiveHash $pins.Rustup.Hash -Directories $rustDirectories)) {
                if ($ValidateOnly) { throw 'The pinned project-local Rust toolchain is missing or changed.' }
                $installer = Get-DeskCueBootstrapDownload -Root $root -Pin $pins.Rustup -Proxy $Proxy -DownloadOperation $DownloadOperation
                $stage = New-DeskCueBootstrapStage -Environment $Environment -Name 'rust'
                $cargo = Join-Path $stage 'cargo'; $rustupHome = Join-Path $stage 'rustup'
                Invoke-WithDeskCueEnvironment -Values @{
                    CARGO_HOME = $cargo; RUSTUP_HOME = $rustupHome
                    PATH = (@((Join-Path $cargo 'bin'), $env:PATH) -join [IO.Path]::PathSeparator)
                } -Operation {
                    $null = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable $installer -Arguments @('-y', '--no-modify-path', '--profile', 'minimal', '--default-host', $pins.RustHost, '--default-toolchain', $pins.RustVersion) -ExecuteOperation $ExecuteOperation
                    $rustup = Join-Path $cargo 'bin/rustup.exe'
                    $null = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable $rustup -Arguments @('set', 'auto-self-update', 'disable') -ExecuteOperation $ExecuteOperation
                    $null = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable $rustup -Arguments (@('component', 'add') + $pins.RustComponents + @('--toolchain', $pins.RustVersion)) -ExecuteOperation $ExecuteOperation
                    $null = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable $rustup -Arguments (@('target', 'add') + $pins.RustTargets + @('--toolchain', $pins.RustVersion)) -ExecuteOperation $ExecuteOperation
                    Test-DeskCueBootstrapVersions -Environment $Environment -Tool 'rust' -Pins $pins -CargoHome $cargo -ExecuteOperation $ExecuteOperation
                }
                Move-DeskCueBootstrapDirectories -Root $root -Directories ([ordered]@{
                    $Environment.Paths.CargoHome = $cargo; $Environment.Paths.RustupHome = $rustupHome
                })
                Save-DeskCueBootstrapInstallation -Root $root -Name 'rust' -Version $pins.RustVersion -Pin $pins.Rustup -Directories $rustDirectories
            }
            Test-DeskCueBootstrapVersions -Environment $Environment -Tool 'rust' -Pins $pins -CargoHome $Environment.Paths.CargoHome -ExecuteOperation $ExecuteOperation
            if (-not (Test-DeskCueBootstrapInstallation -Root $root -Name 'inno' -Version $pins.Inno.Version -ArchiveHash $pins.Inno.Hash -Directories @($innoRoot))) {
                if ($ValidateOnly) { throw 'The pinned project-local Inno compiler is missing or changed.' }
                $installer = Get-DeskCueBootstrapDownload -Root $root -Pin $pins.Inno -Proxy $Proxy -DownloadOperation $DownloadOperation
                $signature = Get-AuthenticodeSignature -LiteralPath $installer
                if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch '(^|,\s*)CN=Pyrsys B\.V\.(,|$)') {
                    throw 'The pinned Inno installer does not have the expected valid vendor signature.'
                }
                $stage = New-DeskCueBootstrapStage -Environment $Environment -Name 'inno'
                $candidate = Join-Path $stage 'inno'
                $log = Join-Path $receiptRoot ('inno-install-' + [Guid]::NewGuid().ToString('N') + '.log')
                Assert-DeskCueLocalPath -Root $root -Path $candidate
                Assert-DeskCueLocalPath -Root $root -Path $log
                $arguments = @('/PORTABLE=1', '/CURRENTUSER', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/SP-', '/NORESTART',
                    '/NOCLOSEAPPLICATIONS', '/NOFORCECLOSEAPPLICATIONS', '/NORESTARTAPPLICATIONS', '/NOICONS', "/DIR=$candidate", "/LOG=$log")
                $null = Invoke-DeskCueBootstrapCommand -Environment $Environment -Executable $installer -Arguments $arguments -ExecuteOperation $ExecuteOperation
                Test-DeskCueBootstrapVersions -Environment $Environment -Tool 'inno' -Pins $pins -InnoRoot $candidate -ExecuteOperation $ExecuteOperation
                Move-DeskCueBootstrapDirectories -Root $root -Directories ([ordered]@{ $innoRoot = $candidate })
                Save-DeskCueBootstrapInstallation -Root $root -Name 'inno' -Version $pins.Inno.Version -Pin $pins.Inno -Directories @($innoRoot)
            }
            Test-DeskCueBootstrapVersions -Environment $Environment -Tool 'inno' -Pins $pins -InnoRoot $innoRoot -ExecuteOperation $ExecuteOperation
            $receipt = [ordered]@{
                SchemaVersion = 1; Status = 'passed'; CanonicalRoot = $Environment.CanonicalRoot; ToolRoot = $root
                SdkVersion = $pins.DotNet.Version; RustVersion = $pins.RustVersion; RustupVersion = $pins.Rustup.Version
                InnoVersion = $pins.Inno.Version; ValidatedOnly = [bool]$ValidateOnly; VerifiedUtc = [DateTime]::UtcNow.ToString('O')
                DotNet = Join-Path $Environment.Paths.DotNetRoot 'dotnet.exe'
                Cargo = Join-Path $Environment.Paths.CargoHome 'bin/cargo.exe'; Iscc = Join-Path $innoRoot 'ISCC.exe'
            }
            if (-not $ValidateOnly) { Write-DeskCueBootstrapJson -Root $root -Path (Join-Path $root 'bootstrap-receipt.json') -Value $receipt }
            [pscustomobject]$receipt
        }
    }
    finally { if ($null -ne $lock) { $lock.Dispose() } }
}
