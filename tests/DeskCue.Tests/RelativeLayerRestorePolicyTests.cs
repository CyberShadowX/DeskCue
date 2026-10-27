using DeskCue.Services;

namespace DeskCue.Tests;

public sealed class RelativeLayerRestorePolicyTests
{
    [Theory]
    [InlineData(false, false, false)]
    [InlineData(false, true, true)]
    [InlineData(true, false, true)]
    [InlineData(true, true, true)]
    public void DesktopAttachment_RespectsDynamicPreferenceButAlwaysPinsPinnedMode(
        bool usesDesktopPinnedMode,
        bool keepVisibleOnShowDesktop,
        bool expected)
    {
        Assert.Equal(
            expected,
            RelativeLayerRestorePolicy.ShouldAttachToDesktop(
                usesDesktopPinnedMode,
                keepVisibleOnShowDesktop));
    }

    [Fact]
    public void RegularForegroundPage_PlacesWidgetDirectlyBehindIt()
    {
        RelativeLayerRestoreDisposition disposition = RelativeLayerRestorePolicy.Decide(
            hasForeground: true,
            foregroundIsDesktopShell: false,
            foregroundIsSelf: false,
            foregroundIsDeskCue: false);

        Assert.Equal(RelativeLayerRestoreDisposition.BehindForeground, disposition);
    }

    [Theory]
    [InlineData(false, false)]
    [InlineData(true, true)]
    public void MissingOrDesktopForeground_ReturnsWidgetToDesktopBottom(
        bool hasForeground,
        bool foregroundIsDesktopShell)
    {
        RelativeLayerRestoreDisposition disposition = RelativeLayerRestorePolicy.Decide(
            hasForeground,
            foregroundIsDesktopShell,
            foregroundIsSelf: false,
            foregroundIsDeskCue: false);

        Assert.Equal(RelativeLayerRestoreDisposition.DesktopBottom, disposition);
    }

    [Theory]
    [InlineData(true, false)]
    [InlineData(false, true)]
    public void DeskCueForeground_PreservesPeerOrder(
        bool foregroundIsSelf,
        bool foregroundIsDeskCue)
    {
        RelativeLayerRestoreDisposition disposition = RelativeLayerRestorePolicy.Decide(
            hasForeground: true,
            foregroundIsDesktopShell: false,
            foregroundIsSelf,
            foregroundIsDeskCue);

        Assert.Equal(RelativeLayerRestoreDisposition.PreservePeerOrder, disposition);
    }
}
