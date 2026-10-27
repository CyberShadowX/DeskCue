[Code]
const
  DeskCueAppCompatLayersKey = 'Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers';

function PrepareDeskCueDependencies(var NeedsRestart: Boolean): string; forward;

#if DeskCueBundledRuntime
function QuoteDeskCueCleanupArgument(Value: string): string;
begin
  Result := '"' + Value + '"';
end;

procedure CleanupDeskCueInstall;
var
  PowerShellPath: string;
  CleanupScriptPath: string;
  CurrentManifestPath: string;
  LegacyManifestPath: string;
  PreviousManifestPath: string;
  Parameters: string;
  ResultCode: Integer;
begin
  if not DirectInstallUpgrade then
  begin
    Log('DeskCue first-install path detected; stale install cleanup skipped.');
    Exit;
  end;

  ExtractTemporaryFile('cleanup-deskcue-install.ps1');
  ExtractTemporaryFile('DeskCue.LegacyBundledRuntimeFiles.txt');

  PowerShellPath := ExpandConstant('{sys}\WindowsPowerShell\v1.0\powershell.exe');
  CleanupScriptPath := ExpandConstant('{tmp}\cleanup-deskcue-install.ps1');
  CurrentManifestPath := ExpandConstant('{tmp}\DeskCue.InstallManifest.current.txt');
  LegacyManifestPath := ExpandConstant('{tmp}\DeskCue.LegacyBundledRuntimeFiles.txt');
  PreviousManifestPath := AddBackslash(WizardDirValue) + 'DeskCue.InstallManifest.txt';
  Parameters :=
    '-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File ' +
    QuoteDeskCueCleanupArgument(CleanupScriptPath) +
    ' -InstallRoot ' + QuoteDeskCueCleanupArgument(WizardDirValue) +
    ' -CurrentManifestPath ' + QuoteDeskCueCleanupArgument(CurrentManifestPath) +
    ' -LegacyManifestPath ' + QuoteDeskCueCleanupArgument(LegacyManifestPath) +
    ' -PreviousManifestPath ' + QuoteDeskCueCleanupArgument(PreviousManifestPath);

  if not Exec(PowerShellPath, Parameters, '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    RaiseException('DeskCue could not start the install cleanup process.');

  if ResultCode <> 0 then
    RaiseException(Format('DeskCue install cleanup failed with exit code %d.', [ResultCode]));

  Log('DeskCue stale install-file cleanup completed successfully.');
end;
#endif

procedure DeleteAppCompatLayerValue(RootKey: Integer; ExePath: string);
var
  Value: string;
begin
  if ExePath = '' then
    Exit;

  if RegQueryStringValue(RootKey, DeskCueAppCompatLayersKey, ExePath, Value) and
     (Pos('RUNASADMIN', Uppercase(Value)) > 0) then
  begin
    if RegDeleteValue(RootKey, DeskCueAppCompatLayersKey, ExePath) then
      Log('DeskCue installer removed AppCompat RUNASADMIN value: ' + ExePath)
    else
      Log('DeskCue installer could not remove AppCompat value: ' + ExePath);
  end;
end;

procedure CleanupInstallAppCompatFlags(InstallPath: string);
var
  ExePath: string;
begin
  ExePath := AddBackslash(NormalizeDirPath(InstallPath)) + DeskCueLegacyExeName;
  DeleteAppCompatLayerValue(HKEY_CURRENT_USER, ExePath);

  if IsAdminInstallMode then
    DeleteAppCompatLayerValue(HKEY_LOCAL_MACHINE, ExePath);
end;

function InitializeSetup: Boolean;
begin
  // Program Files is now the supported all-users location. Older installations
  // found there are upgraded in place instead of being treated as disposable
  // legacy copies.
  Result := PrepareDirectInstallPlan;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := DirectInstallUpgrade and (PageID = wpSelectDir);
end;

function PrepareToInstall(var NeedsRestart: Boolean): string;
var
  DependencyError: string;
begin
  Result := '';

  // Close only the DeskCue process that belongs to the install being updated.
  // Restart Manager remains the final file-lock fallback for Setup itself.
  if not StopDeskCueProcessesAtPath(WizardDirValue) then
    Log('DeskCue path-scoped process shutdown failed; Setup will continue with Restart Manager handling file locks.');

  // Give the process time to fully exit before Restart Manager runs.
  Sleep(2000);
  Log('DeskCue process termination completed.');

  // DeskCue must continue to run at normal user integrity so Explorer drag and
  // drop remains available after an upgrade from older Program Files builds.
  CleanupInstallAppCompatFlags(WizardDirValue);

  DependencyError := PrepareDeskCueDependencies(NeedsRestart);
  if DependencyError <> '' then
    Result := DependencyError;
end;
