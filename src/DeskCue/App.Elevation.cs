using DeskCue.Platform;
using DeskCue.Services;

namespace DeskCue;

public partial class App
{
    private async Task RefreshStartupElevationAsync()
    {
        if (IsShuttingDown || UiDispatch.Phase != UiDispatch.PhaseKind.Ready)
        {
            return;
        }

        MarkStartupProgress();
        try
        {
            StartupElevationAssessment assessment = await StartupElevationPolicy.AssessWhenShellReadyAsync(
                DragDropPermissionService.AssessStartupElevation, Task.Delay, _startupElevationCancellation.Token);
            await UiDispatch.RunAsync(() =>
            {
                if (!IsShuttingDown)
                {
                    _startupElevationAssessment = assessment;
                    LogStartupElevationAssessment();
                    MarkStartupProgress();
                }
                return Task.CompletedTask;
            });
        }
        catch (OperationCanceledException) when (IsShuttingDown || UiDispatch.Phase != UiDispatch.PhaseKind.Ready)
        {
            // Normal shutdown also cancels the bounded shell-readiness wait.
        }
    }

    private async Task HandleStartupElevationAsync()
    {
        if (IsShuttingDown || UiDispatch.Phase != UiDispatch.PhaseKind.Ready)
        {
            return;
        }

        try
        {
            await UiDispatch.RunAsync(async () =>
            {
                if (IsShuttingDown)
                {
                    return;
                }

                // The tray/lifeline await may have outlived Explorer. Unknown
                // after a restart suppresses action rather than reusing a stale
                // known token or starting another unbounded reassessment.
                _startupElevationAssessment = DragDropPermissionService.AssessStartupElevation();
                LogStartupElevationAssessment();
                bool alreadyRelaunched = TryGetAwaitParentExitProcessId(Environment.GetCommandLineArgs()) is not null;
                if (IsStartupMode && StartupElevationPolicy.ShouldRelaunch(
                        _startupElevationAssessment, alreadyRelaunched,
                        DeskCueDataPathService.Current.IsDevelopmentRoot))
                {
                    _ = DragDropPermissionService.ClearElevationCompatibilityFlags();
                    string arguments = $"{AwaitParentExitArgument} {Environment.ProcessId} --startup";
                    if (DragDropPermissionService.TryRelaunchAsExplorerUser(arguments))
                    {
                        Log("[Elevation] Verified unattended relaunch started; shutting down current instance");
                        await ShutdownForRestartAsync();
                        return;
                    }
                    Log("[Elevation] Verified unattended relaunch failed; continuing current instance");
                }

                ShowElevationNoticeIfNeeded();
            });
        }
        catch (OperationCanceledException) when (IsShuttingDown || UiDispatch.Phase != UiDispatch.PhaseKind.Ready)
        {
            // A rejected or shutting-down dispatcher must never create UI.
        }
    }

    private void LogStartupElevationAssessment() => Log(
        $"[Elevation] Startup assessment appElevated={_startupElevationAssessment.IsCurrentProcessElevated} " +
        $"explorerElevated={_startupElevationAssessment.IsExplorerElevated?.ToString() ?? "Unknown"} " +
        $"uacDisabled={_startupElevationAssessment.IsUacDisabled} " +
        $"canRelaunch={_startupElevationAssessment.CanRelaunchUnelevated} " +
        $"mismatch={_startupElevationAssessment.Mismatch}");
}
