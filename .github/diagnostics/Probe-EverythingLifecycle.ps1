[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$OutputDirectory,
    [ValidateRange(3,15)][int]$PerProbeSeconds=8,
    [ValidateSet('', 'cleanup-once','cleanup-twice','reset-cleanup-reset','reset-twice','reset-repeat')][string]$ChildMode=''
)
$ErrorActionPreference='Stop'
$architecture=[Runtime.InteropServices.RuntimeInformation]::ProcessArchitecture.ToString()
if($architecture -notin @('Arm64','X64')){throw 'An actual supported native architecture is required.'}
$sdkName=if($architecture -eq 'Arm64'){'EverythingARM64.dll'}else{'Everything64.dll'}
$sdk=[IO.Path]::GetFullPath((Join-Path $SourceRoot ('src\DeskCue\ThirdParty\Everything\'+$sdkName)))
if(-not (Test-Path -LiteralPath $sdk -PathType Leaf)){throw 'The source SDK DLL is missing.'}
if($ChildMode){
    Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class EverythingLifecycleProbeNative {
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] public delegate void VoidCall();
 [UnmanagedFunctionPointer(CallingConvention.StdCall)] public delegate uint UIntCall();
}
'@
    $handle=[Runtime.InteropServices.NativeLibrary]::Load($sdk)
    $cleanup=[Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer([Runtime.InteropServices.NativeLibrary]::GetExport($handle,'Everything_CleanUp'),[EverythingLifecycleProbeNative+VoidCall])
    $reset=[Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer([Runtime.InteropServices.NativeLibrary]::GetExport($handle,'Everything_Reset'),[EverythingLifecycleProbeNative+VoidCall])
    $count=[Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer([Runtime.InteropServices.NativeLibrary]::GetExport($handle,'Everything_GetNumResults'),[EverythingLifecycleProbeNative+UIntCall])
    function Mark([string]$step){
        [Console]::Out.WriteLine((@{mode=$ChildMode;step=$step;pid=$PID;architecture=$architecture;utc=[DateTime]::UtcNow.ToString('O')}|ConvertTo-Json -Compress))
        [Console]::Out.Flush()
    }
    function Cleanup([string]$step){Mark($step+'-before');$cleanup.Invoke();Mark($step+'-after')}
    function Reset([string]$step){Mark($step+'-before');$reset.Invoke();[void]$count.Invoke();Mark($step+'-after')}
    Mark 'loaded'
    switch($ChildMode){
        'cleanup-once'{Cleanup 'cleanup-1'}
        'cleanup-twice'{Cleanup 'cleanup-1';Cleanup 'cleanup-2'}
        'reset-cleanup-reset'{Reset 'reset-1';Cleanup 'cleanup-1';Reset 'reset-2'}
        'reset-twice'{Reset 'reset-1';Reset 'reset-2'}
        'reset-repeat'{for($iteration=0;$iteration -lt 1000;$iteration++){$reset.Invoke();[void]$count.Invoke()};Mark 'reset-1000-after'}
    }
    Mark 'complete'
    # Do not manually unload the process-global SDK during this lifecycle probe.
    # The owned child exits normally on successful modes; a parent deadline is
    # solely for this disposable PowerShell probe, never for DeskCue/DeskBox.
    exit 0
}
[IO.Directory]::CreateDirectory([IO.Path]::GetFullPath($OutputDirectory))|Out-Null
$pwsh=(Get-Process -Id $PID).Path
$results=@()
foreach($mode in @('cleanup-once','cleanup-twice','reset-cleanup-reset','reset-twice','reset-repeat')){
    $info=[Diagnostics.ProcessStartInfo]::new()
    $info.FileName=$pwsh
    $info.UseShellExecute=$false
    $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true
    $info.RedirectStandardError=$true
    foreach($argument in @('-NoProfile','-File',$PSCommandPath,'-SourceRoot',[IO.Path]::GetFullPath($SourceRoot),'-OutputDirectory',[IO.Path]::GetFullPath($OutputDirectory),'-ChildMode',$mode)){$info.ArgumentList.Add($argument)}
    $child=[Diagnostics.Process]::new();$child.StartInfo=$info
    if(-not $child.Start()){throw 'Unable to start the disposable SDK probe.'}
    $stdout=$child.StandardOutput.ReadToEndAsync();$stderr=$child.StandardError.ReadToEndAsync()
    $timedOut=-not $child.WaitForExit($PerProbeSeconds*1000)
    if($timedOut){$child.Kill($true);$child.WaitForExit()}
    $out=$stdout.GetAwaiter().GetResult();$err=$stderr.GetAwaiter().GetResult()
    [IO.File]::WriteAllText((Join-Path $OutputDirectory ($mode+'.stdout.log')),$out)
    [IO.File]::WriteAllText((Join-Path $OutputDirectory ($mode+'.stderr.log')),$err)
    $results+=@{mode=$mode;pid=$child.Id;timedOut=$timedOut;exitCode=$child.ExitCode;completedMarker=$out.Contains('"step":"complete"')}
    $child.Dispose()
}
$record=@{architecture=$architecture;sdk=$sdk;sdkSha256=(Get-FileHash -LiteralPath $sdk -Algorithm SHA256).Hash;perProbeSeconds=$PerProbeSeconds;results=$results;scope='isolated disposable SDK children; no Everything IPC, filesystem organization, installer or application shutdown'}
$record|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $OutputDirectory 'result.json') -Encoding utf8
$record|ConvertTo-Json -Depth 6
exit 0
