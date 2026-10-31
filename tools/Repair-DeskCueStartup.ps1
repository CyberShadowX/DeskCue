#Requires -Version 7.0
<#
.SYNOPSIS
Preview (default) or explicitly repair the current installation's owned startup task.
.DESCRIPTION
Queries only two exact root task names. Apply creates the production contract before
removing the legacy task. No app is started/stopped, no settings/UAC are changed.
Task Scheduler has no conditional delete: compare-before-delete narrows that race,
but cannot eliminate it. Failed transactions retain their private journal/backups.
Operations and identity overrides are a complete synthetic-test seam; never combine
partial test operations with native Task Scheduler operations.
#>
[CmdletBinding()]
param([switch]$Apply, [hashtable]$Operations,
      [string]$CurrentUserSid = '', [string]$CurrentUserName = '',
      [string]$EvidenceRoot = '')

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$source = Split-Path -Parent $PSScriptRoot
. (Join-Path $source 'deskcue/LocalEnvironment.ps1')
$local = Get-DeskCueLocalEnvironment -SourceRoot $source
$executable = Join-Path $local.CanonicalRoot '发布版/DeskCue.exe'
Assert-DeskCueLocalPath -Root $local.CanonicalRoot -Path $executable
if (-not $EvidenceRoot) { $EvidenceRoot = Join-Path $local.CanonicalRoot '.artifacts/startup-repair' }
Assert-DeskCueLocalPath -Root (Join-Path $local.CanonicalRoot '.artifacts') -Path $EvidenceRoot
$injected = $null -ne $Operations
if ($injected) {
    foreach ($key in @('TaskQuery', 'TaskRegister', 'TaskDelete', 'ContractFactory', 'Validator', 'ProcessProbe')) {
        if (-not $Operations.ContainsKey($key) -or $Operations[$key] -isnot [scriptblock]) {
            throw "Synthetic operation set is incomplete: $key"
        }
    }
    if (-not $CurrentUserSid -or -not $CurrentUserName) { throw 'Synthetic identity is required.' }
}
else {
    if ($CurrentUserSid -or $CurrentUserName) { throw 'Identity overrides require complete synthetic operations.' }
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    try { $CurrentUserSid = $identity.User.Value; $CurrentUserName = $identity.Name }
    finally { $identity.Dispose() }
}
if ($CurrentUserSid -notmatch '^S-1-5-21-\d+-\d+-\d+-\d+$') { throw 'Expected a local/domain user SID.' }
$legacyName = 'DeskCue-Logon-' + $CurrentUserSid
$canonicalName = 'DeskCue User Startup-' + $CurrentUserSid
$utf8 = [Text.UTF8Encoding]::new($false)
$journalPath = ''
$journal = $null

function Read-Xml([string]$Text) {
    $settings = [Xml.XmlReaderSettings]::new()
    $settings.DtdProcessing = [Xml.DtdProcessing]::Prohibit
    $settings.XmlResolver = $null
    $reader = [Xml.XmlReader]::Create([IO.StringReader]::new($Text), $settings)
    try {
        $doc = [Xml.XmlDocument]::new()
        $doc.XmlResolver = $null
        $doc.Load($reader)
        return ,$doc
    }
    finally { $reader.Dispose() }
}
function Snapshot([string]$Text) { (Read-Xml $Text).DocumentElement.OuterXml }
function Hash([string]$Text) { [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($utf8.GetBytes($Text))) }
function Save-Journal {
    if ($journalPath) { [IO.File]::WriteAllText($journalPath, ($journal | ConvertTo-Json -Depth 15), $utf8) }
}
function Record([string]$Event) {
    $journal.events.Add([ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); event = $Event })
    Save-Journal
}
function Query([string]$Name) {
    if ($Name -cne $legacyName -and $Name -cne $canonicalName) { throw 'Out-of-scope task query.' }
    $result = & $Operations.TaskQuery $Name
    if ($null -eq $result -or $result.Status -notin @('Found', 'Missing')) {
        throw "Task query uncertain: $Name"
    }
    if ($result.Status -eq 'Found' -and [string]::IsNullOrWhiteSpace($result.Xml)) {
        throw "Task query returned empty XML: $Name"
    }
    return $result
}
function Assert-NormalPath([string]$Candidate, [string]$Expected) {
    if (-not [IO.Path]::IsPathFullyQualified($Candidate) -or $Candidate -match '["%~]' -or
        $Candidate -match '^[\\/]{2}' -or $Candidate.Contains('/') -or
        -not [IO.Path]::GetFullPath($Candidate).Equals($Candidate, [StringComparison]::OrdinalIgnoreCase) -or
        -not $Candidate.Equals($Expected, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Task executable/working directory is not the exact normalized published path.'
    }
    Assert-DeskCueLocalPath -Root $local.CanonicalRoot -Path $Candidate
    # GetLongPathName is unnecessary: any 8.3 alias differs from Expected.
}
function Assert-Shape([string]$Text, [bool]$Canonical) {
    $doc = Read-Xml $Text
    $ns = [Xml.XmlNamespaceManager]::new($doc.NameTable)
    $ns.AddNamespace('t', 'http://schemas.microsoft.com/windows/2004/02/mit/task')
    if ($doc.DocumentElement.LocalName -cne 'Task' -or
        $doc.DocumentElement.NamespaceURI -cne $ns.LookupNamespace('t')) { throw 'Unexpected task namespace/root.' }
    # Duplicate values and foreign namespaces can hide a second interpretation.
    foreach ($node in $doc.SelectNodes('//*')) {
        if ($node.NamespaceURI -cne $ns.LookupNamespace('t')) { throw 'Foreign XML namespace.' }
        $seen = @{}
        foreach ($child in $node.ChildNodes) {
            if ($child -is [Xml.XmlElement]) {
                if ($seen.ContainsKey($child.LocalName)) { throw "Duplicate task element: $($child.LocalName)" }
                $seen[$child.LocalName] = $true
            }
        }
    }
    foreach ($path in @('/t:Task/t:RegistrationInfo', '/t:Task/t:Settings', '/t:Task/t:Principals',
                         '/t:Task/t:Principals/t:Principal', '/t:Task/t:Triggers',
                         '/t:Task/t:Triggers/t:LogonTrigger', '/t:Task/t:Actions', '/t:Task/t:Actions/t:Exec')) {
        if ($doc.SelectNodes($path, $ns).Count -ne 1) { throw "Expected exactly one $path" }
    }
    foreach ($path in @('/t:Task/t:Principals', '/t:Task/t:Triggers', '/t:Task/t:Actions')) {
        if ($doc.SelectNodes("$path/*", $ns).Count -ne 1) { throw 'Unexpected principal/trigger/action.' }
    }
    foreach ($tag in @('Principal', 'LogonTrigger', 'Exec')) {
        if ($doc.SelectNodes("//t:$tag", $ns).Count -ne 1) { throw 'Nested or extra principal/trigger/action.' }
    }
    function Value([string]$Path) {
        $node = $doc.SelectSingleNode($Path, $ns)
        if ($null -eq $node) { return '' }
        return $node.InnerText
    }
    function Check-User([string]$Value) {
        if (-not $Value.Equals($CurrentUserSid, [StringComparison]::OrdinalIgnoreCase) -and
            -not $Value.Equals($CurrentUserName, [StringComparison]::OrdinalIgnoreCase)) { throw 'Foreign task user.' }
    }
    $principal = '/t:Task/t:Principals/t:Principal'
    $trigger = '/t:Task/t:Triggers/t:LogonTrigger'
    if ($doc.SelectNodes('//t:GroupId', $ns).Count) { throw 'Group principal is not owned.' }
    Check-User (Value "$principal/t:UserId")
    Check-User (Value "$trigger/t:UserId")
    if ((Value "$principal/t:LogonType") -cne 'InteractiveToken') { throw 'Unexpected logon type.' }
    if ((Value "$principal/t:RunLevel") -cnotin @('', 'LeastPrivilege')) { throw 'Unexpected run level.' }
    foreach ($path in @('/t:Task/t:Settings/t:Enabled', "$trigger/t:Enabled")) {
        if ((Value $path) -cnotin @('', 'true', '1')) { throw 'Disabled or invalid task enabled state.' }
        # Only omission defaults to true, not a present empty element.
        if ($doc.SelectNodes($path, $ns).Count -and (Value $path) -eq '') { throw 'Empty enabled state.' }
    }
    if ((Value "$trigger/t:Delay") -cnotin @('', 'PT0S')) { throw 'Unexpected startup delay.' }
    foreach ($child in $doc.SelectNodes("$trigger/*", $ns)) {
        if ($child.LocalName -cnotin @('UserId', 'Enabled', 'Delay')) { throw 'Unexpected logon trigger constraint.' }
    }
    $sourceValue = if ($Canonical) { 'DeskCue' } else { 'DeskCue.LocalStartup.v1' }
    if ((Value '/t:Task/t:RegistrationInfo/t:Source') -cne $sourceValue) { throw 'Foreign task source.' }
    $name = if ($Canonical) { $canonicalName } else { $legacyName }
    $uri = Value '/t:Task/t:RegistrationInfo/t:URI'
    if ($uri -and $uri -cne "\$name") { throw 'Foreign task URI.' }
    $action = '/t:Task/t:Actions/t:Exec'
    foreach ($child in $doc.SelectNodes("$action/*", $ns)) {
        if ($child.LocalName -cnotin @('Command', 'Arguments', 'WorkingDirectory')) { throw 'Unexpected Exec element.' }
    }
    Assert-NormalPath (Value "$action/t:Command") $executable
    $arguments = if ($Canonical) { $contract.Arguments } else { '' }
    if ((Value "$action/t:Arguments") -cne $arguments) { throw 'Unexpected startup arguments.' }
    $workdir = Value "$action/t:WorkingDirectory"
    if ($workdir) { Assert-NormalPath $workdir ([IO.Path]::GetDirectoryName($executable)) }
}
function Assert-Canonical([string]$Text) {
    Assert-Shape $Text $true
    if ((& $Operations.Validator $canonicalName $Text $executable) -ne $true) { throw 'Production startup contract validation failed.' }
}

# This is used only after pure helper construction. No folder/task enumeration.
function Invoke-Scheduler([scriptblock]$Action) {
    $service = $folder = $null
    try {
        $service = New-Object -ComObject 'Schedule.Service'
        $service.Connect()
        $folder = $service.GetFolder('\')
        & $Action $folder
    }
    finally {
        foreach ($com in @($folder, $service)) {
            if ($null -ne $com) { $null = [Runtime.InteropServices.Marshal]::FinalReleaseComObject($com) }
        }
    }
}
function Initialize-PureHelper([string]$SharedDotnet = '') {
    $run = Join-Path $local.CanonicalRoot ('.artifacts/startup-repair-helper/' + [Guid]::NewGuid().ToString('N'))
    $helperEnv = Get-DeskCueLocalEnvironment -SourceRoot $source -RunRoot $run
    foreach ($path in $helperEnv.Paths.Values) { $null = New-Item -ItemType Directory -Force -Path $path }
    $null = New-Item -ItemType Directory -Force -Path $run
    $dotnet = Join-Path $helperEnv.Paths.DotNetRoot 'dotnet.exe'
    if ($SharedDotnet) {
        # Tests in cloud builds may reuse setup-dotnet's existing pinned host.
        # Live repair calls without this parameter and uses only portable tools.
        if (-not (Test-Path -LiteralPath $SharedDotnet -PathType Leaf)) { throw 'Shared SDK host is missing.' }
        $dotnet = $SharedDotnet
        $helperEnv.ProcessValues.DOTNET_ROOT = Split-Path -Parent $dotnet
    }
    $project = Join-Path $source 'tests/DeskCue.StartupUnicodeProbe/DeskCue.StartupUnicodeProbe.csproj'
    $arch = switch ([Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()) {
        'X64' { 'x64' }; 'Arm64' { 'ARM64' }; default { throw 'Only x64/ARM64 hosts are supported.' }
    }
    $rid = 'win-' + $arch.ToLowerInvariant()
    # The tracked neutral probe lock has no packages. Add only a selected empty
    # RID graph in private scratch; no dependency resolution or source lock edit.
    $lock = Get-Content -LiteralPath (Join-Path (Split-Path $project) 'packages.lock.json') -Raw | ConvertFrom-Json -AsHashtable
    if ($lock.dependencies.Count -ne 1 -or -not $lock.dependencies.ContainsKey('net10.0-windows7.0') -or
        $lock.dependencies['net10.0-windows7.0'].Count -ne 0) { throw 'Pure probe lock graph changed; review helper restore.' }
    $lock.dependencies['net10.0-windows7.0/' + $rid] = @{}
    $lockPath = Join-Path $run 'packages.lock.json'
    [IO.File]::WriteAllText($lockPath, ($lock | ConvertTo-Json -Depth 10), $utf8)
    $props = @("-p:Platform=$arch", "-p:RuntimeIdentifier=$rid",
               ('-p:BaseIntermediateOutputPath=' + (Join-Path $run 'obj/')), "-p:NuGetLockFilePath=$lockPath")
    Invoke-WithDeskCueEnvironment -Values $helperEnv.ProcessValues -Operation {
        $version = & $dotnet --version
        if ($LASTEXITCODE -ne 0 -or $version -cne '10.0.402') { throw 'Pinned SDK 10.0.402 is required.' }
        & $dotnet restore $project --locked-mode @props *> (Join-Path $run 'restore.log')
        if ($LASTEXITCODE -ne 0) { throw "Pure helper restore failed; see $run" }
        & $dotnet build $project --no-restore -c Release @props -o (Join-Path $run 'bin') *> (Join-Path $run 'build.log')
        if ($LASTEXITCODE -ne 0) { throw "Pure helper build failed; see $run" }
    }
    return @{ Dotnet = $dotnet; Dll = Join-Path $run 'bin/DeskCue.StartupUnicodeProbe.dll'; Environment = $helperEnv; Run = $run }
}

$old = $new = $contract = $null
$createAttempted = $false
$createdSnapshot = $null
try {
    if (-not $injected) {
        $helper = Initialize-PureHelper
        $Operations = @{
            ContractFactory = { param($exe, $sid)
                Invoke-WithDeskCueEnvironment -Values $helper.Environment.ProcessValues -Operation {
                    $output = & $helper.Dotnet $helper.Dll '--emit-startup-contract' $exe
                    if ($LASTEXITCODE -ne 0) { throw 'Pure contract emission failed.' }
                    ($output -join "`n") | ConvertFrom-Json
                }
            }
            Validator = { param($name, $xml, $exe)
                $path = Join-Path $helper.Run 'validate.xml'
                [IO.File]::WriteAllText($path, $xml, $utf8)
                Invoke-WithDeskCueEnvironment -Values $helper.Environment.ProcessValues -Operation {
                    $null = & $helper.Dotnet $helper.Dll '--validate-startup-contract' $exe $name $path
                    return $LASTEXITCODE -eq 0
                }
            }
            TaskQuery = { param($name)
                try {
                    Invoke-Scheduler { param($folder)
                        $task = $null
                        try { $task = $folder.GetTask($name); return @{ Status = 'Found'; Xml = [string]$task.Xml } }
                        finally { if ($task) { $null = [Runtime.InteropServices.Marshal]::FinalReleaseComObject($task) } }
                    }
                }
                catch {
                    $exception = $_.Exception
                    while ($exception.InnerException) { $exception = $exception.InnerException }
                    if ($exception.HResult -in @(-2147024894, -2147024893)) { return @{ Status = 'Missing' } }
                    return @{ Status = 'Error'; Error = $exception.Message }
                }
            }
            TaskRegister = { param($name, $xml)
                Invoke-Scheduler { param($folder)
                    # TASK_CREATE=2; TASK_LOGON_INTERACTIVE_TOKEN=3. Never update/Force.
                    $task = $folder.RegisterTask($name, $xml, 2, $null, $null, 3, $null)
                    if ($task) { $null = [Runtime.InteropServices.Marshal]::FinalReleaseComObject($task) }
                }
            }
            TaskDelete = { param($name) Invoke-Scheduler { param($folder) $folder.DeleteTask($name, 0) } }
            ProcessProbe = { param($exe)
                foreach ($process in @(Get-Process -Name 'DeskCue' -ErrorAction SilentlyContinue)) {
                    # An inaccessible path is uncertainty, never permission to proceed.
                    if (-not $process.Path) { throw 'Unable to identify a running DeskCue process.' }
                    if ($process.Path.Equals($exe, [StringComparison]::OrdinalIgnoreCase)) { return $true }
                }
                return $false
            }
        }
    }
    $contract = & $Operations.ContractFactory $executable $CurrentUserSid
    if ($contract.TaskName -cne $canonicalName -or -not $contract.Arguments) { throw 'Unexpected production task contract identity.' }
    Assert-Canonical $contract.Xml
    $old = Query $legacyName
    $new = Query $canonicalName
    if ($old.Status -eq 'Missing') {
        if ($new.Status -ne 'Found') { throw 'No enabled owned startup intent exists to repair.' }
        Assert-Canonical $new.Xml
        return [pscustomobject]@{ Status = 'AlreadyRepaired'; JournalPath = ''; Executable = $executable }
    }
    Assert-Shape $old.Xml $false
    if ($new.Status -ne 'Missing') { throw 'Canonical task collision: no task was overwritten.' }
    if (-not $Apply) { return [pscustomobject]@{ Status = 'Preview'; Executable = $executable; LegacyTask = $legacyName; CanonicalTask = $canonicalName } }
    if ((& $Operations.ProcessProbe $executable) -ne $false) { throw 'Exit the published DeskCue normally before Apply.' }
    $transaction = Join-Path $EvidenceRoot ([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfff') + '-' + [Guid]::NewGuid().ToString('N'))
    Assert-DeskCueLocalPath -Root $local.CanonicalRoot -Path $transaction
    $null = New-Item -ItemType Directory -Path $transaction
    [IO.File]::WriteAllText((Join-Path $transaction 'legacy.xml'), $old.Xml, $utf8)
    [IO.File]::WriteAllText((Join-Path $transaction 'intended-canonical.xml'), $contract.Xml, $utf8)
    $journalPath = Join-Path $transaction 'journal.json'
    $journal = [ordered]@{ schemaVersion = 1; status = 'Started'; legacyName = $legacyName; canonicalName = $canonicalName;
        executable = $executable; legacySha256 = Hash $old.Xml; intendedSha256 = Hash $contract.Xml;
        limitation = 'Task Scheduler has no atomic conditional delete; compare-before-delete cannot eliminate external editor races.';
        events = [Collections.Generic.List[object]]::new() }
    Record 'Original backup and intended contract saved before task mutations.'
    $oldSnapshot = Snapshot $old.Xml
    $checkOld = Query $legacyName
    $checkNew = Query $canonicalName
    if ($checkOld.Status -ne 'Found' -or (Snapshot $checkOld.Xml) -cne $oldSnapshot -or $checkNew.Status -ne 'Missing') {
        throw 'Task state changed before canonical creation.'
    }
    Record 'Both entries compared before create-only registration.'
    $createAttempted = $true
    $null = & $Operations.TaskRegister $canonicalName $contract.Xml
    Record 'Canonical task created without overwrite.'
    $readback = Query $canonicalName
    if ($readback.Status -ne 'Found') { throw 'Created canonical task is not readable.' }
    [IO.File]::WriteAllText((Join-Path $transaction 'canonical-readback.xml'), $readback.Xml, $utf8)
    Assert-Canonical $readback.Xml
    $createdSnapshot = Snapshot $readback.Xml
    $journal['createdSha256'] = Hash $readback.Xml
    Save-Journal
    $checkOld = Query $legacyName
    $checkNew = Query $canonicalName
    if ($checkOld.Status -ne 'Found' -or (Snapshot $checkOld.Xml) -cne $oldSnapshot -or
        $checkNew.Status -ne 'Found' -or (Snapshot $checkNew.Xml) -cne $createdSnapshot) {
        throw 'Task state changed before legacy deletion.'
    }
    Assert-Canonical $checkNew.Xml
    if ((& $Operations.ProcessProbe $executable) -ne $false) { throw 'Published DeskCue started during the transaction.' }
    Record 'Both snapshots compared; deleting exact legacy name.'
    $null = & $Operations.TaskDelete $legacyName
    if ((Query $legacyName).Status -ne 'Missing') { throw 'Legacy deletion did not verify.' }
    $final = Query $canonicalName
    if ($final.Status -ne 'Found' -or (Snapshot $final.Xml) -cne $createdSnapshot) { throw 'Canonical final snapshot changed.' }
    Assert-Canonical $final.Xml
    $journal.status = 'Repaired'
    Record 'Legacy absent and canonical production-preferred verified.'
    return [pscustomobject]@{ Status = 'Repaired'; JournalPath = $journalPath; Executable = $executable }
}
catch {
    $reason = $_.Exception.Message
    if ($journalPath) {
        # Preserve/restore old first; no deletion when its state is uncertain.
        try {
            if ($createAttempted) {
                $rollbackOld = Query $legacyName
                if ($rollbackOld.Status -eq 'Missing') {
                    Record 'Rollback: legacy proven absent; create-only original restore.'
                    $null = & $Operations.TaskRegister $legacyName $old.Xml
                    $rollbackOld = Query $legacyName
                }
                if ($rollbackOld.Status -ne 'Found' -or (Snapshot $rollbackOld.Xml) -cne (Snapshot $old.Xml)) {
                    throw 'Original legacy snapshot is not preserved; canonical retained.'
                }
                Record 'Rollback: original legacy snapshot verified before canonical cleanup.'
                if ($null -ne $createdSnapshot) {
                    $rollbackNew = Query $canonicalName
                    if ($rollbackNew.Status -eq 'Found') {
                        if ((Snapshot $rollbackNew.Xml) -cne $createdSnapshot) { throw 'Canonical externally changed; left untouched.' }
                        $null = & $Operations.TaskDelete $canonicalName
                        if ((Query $canonicalName).Status -ne 'Missing') { throw 'Canonical cleanup did not verify.' }
                        Record 'Rollback: unchanged transaction canonical removed.'
                    }
                }
                else { Record 'Rollback: canonical has no captured readback; retained for manual inspection.' }
            }
        }
        catch { $reason += ' Rollback: ' + $_.Exception.Message }
        $journal.status = 'Failed'
        $journal['reason'] = $reason
        Save-Journal
    }
    return [pscustomobject]@{ Status = 'Failed'; Reason = $reason; JournalPath = $journalPath }
}
