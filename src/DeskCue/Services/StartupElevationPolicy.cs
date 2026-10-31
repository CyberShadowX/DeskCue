namespace DeskCue.Services;

/// <summary>Startup shell availability policy, independent of windows and real waits.</summary>
internal static class StartupElevationPolicy
{
    internal static bool ShouldRepairCompatibilityFlags(StartupElevationAssessment assessment, bool isIsolatedProfile) =>
        !isIsolatedProfile && !assessment.IsUacDisabled && assessment.CanRelaunchUnelevated &&
        assessment.Mismatch == ShellIntegrityMismatch.AppAboveShell;

    internal static bool ShouldRelaunch(StartupElevationAssessment assessment, bool alreadyRelaunched, bool isIsolatedProfile = false) =>
        !alreadyRelaunched && ShouldRepairCompatibilityFlags(assessment, isIsolatedProfile);

    internal static async Task<StartupElevationAssessment> AssessWhenShellReadyAsync(
        Func<StartupElevationAssessment> assess,
        Func<TimeSpan, CancellationToken, Task> delay,
        CancellationToken cancellationToken)
    {
        // Twenty asynchronous waits give Explorer a bounded five seconds at
        // logon. No UI thread sleep, guessed token, or indefinite retry loop.
        for (int attempt = 0; ; attempt++)
        {
            cancellationToken.ThrowIfCancellationRequested();
            StartupElevationAssessment assessment = assess();
            if (assessment.Mismatch != ShellIntegrityMismatch.Unknown || attempt >= 20)
            {
                return assessment;
            }

            await delay(TimeSpan.FromMilliseconds(250), cancellationToken).ConfigureAwait(false);
        }
    }
}
