using DeskCue.Services;

namespace DeskCue.Tests;

public sealed class StartupElevationPolicyTests
{
    private static StartupElevationAssessment Snapshot(bool? shellElevated) =>
        new(true, shellElevated, false,
            DragDropPermissionService.ComputeCanRelaunchUnelevated(false, shellElevated), true);

    [Theory]
    [InlineData(null, false, false)]
    [InlineData(true, false, false)]
    [InlineData(false, false, true)]
    [InlineData(false, true, false)]
    public void UnattendedRelaunch_RequiresAKnownMismatchAndNeverRepeats(
        bool? shellElevated, bool alreadyRelaunched, bool expected)
    {
        Assert.Equal(expected, StartupElevationPolicy.ShouldRelaunch(Snapshot(shellElevated), alreadyRelaunched));
    }

    [Fact]
    public void IsolatedProfile_NeverAutomaticallyRepairsCompatibilityOrRelaunches()
    {
        Assert.False(StartupElevationPolicy.ShouldRepairCompatibilityFlags(Snapshot(false), isIsolatedProfile: true));
        Assert.False(StartupElevationPolicy.ShouldRelaunch(Snapshot(false), alreadyRelaunched: false, isIsolatedProfile: true));
    }

    [Theory]
    [InlineData(null, false)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    public void CompatibilityRepair_RequiresAKnownAppAboveShellMismatch(bool? shellElevated, bool repair)
    {
        Assert.Equal(repair, StartupElevationPolicy.ShouldRepairCompatibilityFlags(Snapshot(shellElevated), isIsolatedProfile: false));
    }

    [Theory]
    [InlineData(false, null, true)]
    [InlineData(false, true, true)]
    [InlineData(true, null, false)]
    [InlineData(true, true, false)]
    [InlineData(true, false, true)]
    public void VerifiedRelaunch_RequiresTheOpenedParentTokenToBeKnownUnelevated(
        bool requireUnelevatedShell, bool? openedParentElevated, bool allowed)
    {
        Assert.Equal(allowed, ShellUnelevatedLaunch.CanUseShellParent(requireUnelevatedShell, openedParentElevated));
    }

    [Theory]
    [InlineData(true, ShellIntegrityMismatch.None, false, FullyElevatedSessionAttribution.BuiltInAdminAccount)]
    [InlineData(false, ShellIntegrityMismatch.AppAboveShell, true, FullyElevatedSessionAttribution.None)]
    public async Task UnknownThenKnown_UsesTheAvailableShellInsteadOfTheInitialSnapshot(
        bool shellElevated, ShellIntegrityMismatch mismatch, bool relaunch,
        FullyElevatedSessionAttribution attribution)
    {
        var snapshots = new Queue<StartupElevationAssessment>([Snapshot(null), Snapshot(null), Snapshot(shellElevated)]);
        int waits = 0;
        var result = await StartupElevationPolicy.AssessWhenShellReadyAsync(
            () => snapshots.Dequeue(), (_, _) => { waits++; return Task.CompletedTask; }, CancellationToken.None);

        Assert.Equal(mismatch, result.Mismatch);
        Assert.Equal(relaunch, result.CanRelaunchUnelevated);
        Assert.Equal(attribution, result.FullyElevatedAttribution);
        Assert.Equal(2, waits);
    }

    [Fact]
    public async Task PersistentUnknown_StopsRetryingWithoutClaimingMismatchOrRelaunch()
    {
        int probes = 0;
        var waits = new List<TimeSpan>();
        var result = await StartupElevationPolicy.AssessWhenShellReadyAsync(
            () => { probes++; return Snapshot(null); },
            (interval, _) => { waits.Add(interval); return Task.CompletedTask; }, CancellationToken.None);

        Assert.Equal(ShellIntegrityMismatch.Unknown, result.Mismatch);
        Assert.False(result.CanRelaunchUnelevated);
        Assert.Equal(FullyElevatedSessionAttribution.None, result.FullyElevatedAttribution);
        Assert.InRange(probes, 2, 32);
        Assert.Equal(probes - 1, waits.Count);
        Assert.InRange(waits.Sum(interval => interval.TotalSeconds), 1, 10);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task KnownShell_DoesNotWaitOrRelaunchInALoop(bool shellElevated)
    {
        int probes = 0;
        var result = await StartupElevationPolicy.AssessWhenShellReadyAsync(
            () => { probes++; return Snapshot(shellElevated); },
            (_, _) => throw new InvalidOperationException("A known shell must not be retried."), CancellationToken.None);

        Assert.Equal(shellElevated, result.IsExplorerElevated);
        Assert.Equal(1, probes);
    }

    [Fact]
    public async Task ShutdownDuringWait_CancelsWithoutAnotherProbeOrUiDecision()
    {
        using var shutdown = new CancellationTokenSource();
        int probes = 0;
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() =>
            StartupElevationPolicy.AssessWhenShellReadyAsync(
                () => { probes++; return Snapshot(null); },
                (_, token) => { shutdown.Cancel(); return Task.FromCanceled(token); }, shutdown.Token));
        Assert.Equal(1, probes);
    }

    [Fact]
    public async Task ShutdownBeforeAssessment_DoesNotProbe()
    {
        using var shutdown = new CancellationTokenSource();
        shutdown.Cancel();
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() =>
            StartupElevationPolicy.AssessWhenShellReadyAsync(
                () => throw new InvalidOperationException("Must not probe after shutdown."),
                (_, _) => Task.CompletedTask, shutdown.Token));
    }
}
