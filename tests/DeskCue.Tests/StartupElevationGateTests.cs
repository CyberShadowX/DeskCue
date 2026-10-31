using DeskCue.Services;

namespace DeskCue.Tests;

public sealed class StartupElevationGateTests
{
    [Fact]
    public void InitialAssessment_IsAwaitedBeforeAnyStartupWidgetConstruction()
    {
        // FileSurfaceContent initializes its empty-state warning only once in
        // its constructor. A late assessment can get the final notice right
        // while every restored/default widget retains the initial Unknown.
        // Inspect the real App integration: invoking that WinUI lifecycle in
        // a headless unit host would create windows and use machine state.
        string source = File.ReadAllText(TestPaths.FromRepository("src/DeskCue/App.xaml.cs"));
        int launchStart = source.IndexOf("protected override async void OnLaunched", StringComparison.Ordinal);
        int launchEnd = source.IndexOf("FailStartup(\"exception during startup\", ex);", launchStart, StringComparison.Ordinal);
        string launch = source[launchStart..launchEnd];
        var awaitedAssessment = System.Text.RegularExpressions.Regex.Match(launch,
            @"await\s+RunOptionalStartupStepAsync\s*\(\s*""elevation-assessment""\s*,\s*RefreshStartupElevationAsync\s*\)");

        Assert.True(awaitedAssessment.Success, "Initial elevation publication must complete before constructing widget consumers.");
        foreach (string consumer in new[] { "WidgetManager = new WidgetManager", "widgetManager.RestoreWidgetsAsync", "EnsureInitialFileWidgetSetupAsync" })
        {
            int consumerPosition = launch.IndexOf(consumer, StringComparison.Ordinal);
            Assert.True(consumerPosition > awaitedAssessment.Index + awaitedAssessment.Length,
                $"{consumer} must not capture startup elevation before the initial assessment completes.");
        }
    }

    [Fact]
    public void UnknownShell_DoesNotBecomeAnAppAboveShellMismatch()
    {
        var assessment = new StartupElevationAssessment(true, null, false, false);

        Assert.NotEqual(ShellIntegrityMismatch.AppAboveShell, assessment.Mismatch);
        Assert.Equal(FullyElevatedSessionAttribution.None, assessment.FullyElevatedAttribution);
    }

    [Fact]
    public void UnknownShell_CannotPromiseAnUnelevatedRelaunch()
    {
        Assert.False(DragDropPermissionService.ComputeCanRelaunchUnelevated(false, null));
        Assert.False(DragDropPermissionService.ComputeNeedsRelaunchDiagnostic(true, false, null));
    }

    [Theory]
    [InlineData(null)]
    [InlineData(true)]
    public void Relaunch_UnknownOrElevatedShellNeverStartsAReplacement(bool? shellElevated)
    {
        var assessment = new StartupElevationAssessment(true, shellElevated, false, true);
        Assert.False(DragDropPermissionService.TryRelaunchAsExplorerUser(
            assessment, @"F:\fixture\DeskCue.exe", "--startup --await-parent-exit 1234",
            (_, _) => throw new InvalidOperationException("Must not start without a known standard-user shell.")));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void Relaunch_PreservesStartupAndParentWaitArgumentsAndReturnsTheVerifiedLauncherResult(bool started)
    {
        string? observedExecutable = null;
        string? observedArguments = null;
        var assessment = new StartupElevationAssessment(true, false, false, true);
        bool result = DragDropPermissionService.TryRelaunchAsExplorerUser(
            assessment, @"F:\fixture\DeskCue.exe", "--await-parent-exit 1234 --startup",
            (executable, arguments) => { observedExecutable = executable; observedArguments = arguments; return started; });

        Assert.Equal(started, result);
        Assert.Equal(@"F:\fixture\DeskCue.exe", observedExecutable);
        Assert.Equal("--await-parent-exit 1234 --startup", observedArguments);
    }

    [Theory]
    [InlineData(false, false, true)]   // UAC on, Explorer standard: relaunch works
    [InlineData(false, true, false)]   // UAC on but Explorer elevated: parent handover would stay elevated
    [InlineData(true, false, false)]   // UAC off: no reliable standard-user context to promise
    [InlineData(true, true, false)]    // UAC off and Explorer elevated (the typical UAC-off machine)
    public void ComputeCanRelaunchUnelevated_OnlyPromisesARelaunchIntoAStandardUserContext(
        bool isUacDisabled,
        bool isExplorerElevated,
        bool expected)
    {
        Assert.Equal(
            expected,
            DragDropPermissionService.ComputeCanRelaunchUnelevated(isUacDisabled, isExplorerElevated));
    }

    [Fact]
    public void StartupElevationAssessment_UnrelaunchableWhenExplorerIsElevated()
    {
        // Guards against regressing to Diagnose's looser NeedsRelaunch gate
        // (which would offer a restart that lands on an elevated instance
        // again whenever Explorer itself runs elevated).
        bool uacOffWithElevatedExplorer = DragDropPermissionService.ComputeCanRelaunchUnelevated(
            isUacDisabled: true,
            isExplorerElevated: true);
        bool uacOnWithElevatedExplorer = DragDropPermissionService.ComputeCanRelaunchUnelevated(
            isUacDisabled: false,
            isExplorerElevated: true);

        Assert.False(uacOffWithElevatedExplorer);
        Assert.False(uacOnWithElevatedExplorer);
    }
}
