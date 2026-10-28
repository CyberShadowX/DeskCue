using DeskCue;
using DrawingPoint = System.Drawing.Point;

namespace DeskCue.Tests;

public sealed class TrayContextMenuPlacementPolicyTests
{
    private static readonly Win32Helper.RECT Primary = Rect(0, 0, 2560, 1440);

    [Fact]
    public void FinderTopClick_DoesNotUseTheRetainedBottomWindowsTrayRect()
    {
        Assert.False(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            Rect(2200, 1400, 2232, 1432), new DrawingPoint(1158, 12), Primary, 1));
    }

    [Fact]
    public void WindowsTrayClickInsideIcon_KeepsTheShellAnchor()
    {
        Assert.True(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            Rect(2200, 1400, 2232, 1432), new DrawingPoint(2216, 1416), Primary, 1));
    }

    [Fact]
    public void NegativeOriginMonitor_RejectsAnIconOnThePrimaryMonitor()
    {
        Assert.False(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            Rect(2200, 1400, 2232, 1432), new DrawingPoint(-1200, 12),
            Rect(-1920, -120, 0, 1080), 1.5));
        Assert.True(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            Rect(-1224, 0, -1176, 36), new DrawingPoint(-1200, 12),
            Rect(-1920, -120, 0, 1080), 1.5));
    }

    [Fact]
    public void SmallPointerTolerance_IsScaledOnceUsingTheOriginatingMonitorDpi()
    {
        var rect = Rect(2000, 1400, 2032, 1432);
        Assert.False(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            rect, new DrawingPoint(2048, 1416), Primary, 1));
        Assert.True(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            rect, new DrawingPoint(2048, 1416), Primary, 1.5));
        Assert.False(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            rect, new DrawingPoint(2085, 1416), Primary, 4));
    }

    [Fact]
    public void OverflowTrayAwayFromTaskbar_CanStillUseItsNearbyShellIconRect()
    {
        Assert.True(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            Rect(2210, 1100, 2242, 1132), new DrawingPoint(2226, 1116), Primary, 1));
    }

    [Theory]
    [InlineData(10, 10, 10, 42)]
    [InlineData(10, 10, 42, 10)]
    [InlineData(-2147483648, 0, 2147483647, 32)]
    [InlineData(0, -2147483648, 32, 2147483647)]
    [InlineData(0, 0, 2560, 1440)]
    public void MalformedOrUnboundedShellRect_CannotOverrideCapturedPointer(
        int left, int top, int right, int bottom)
    {
        Assert.False(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            Rect(left, top, right, bottom), new DrawingPoint(16, 16), Primary, 1));
    }

    [Theory]
    [InlineData(double.NaN)]
    [InlineData(double.PositiveInfinity)]
    [InlineData(-1)]
    [InlineData(100000)]
    public void InvalidOrExtremeDpi_DoesNotCreateAnUnboundedAgreementArea(double dpi)
    {
        Assert.False(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            Rect(1200, 0, 1232, 32), new DrawingPoint(1000, 12), Primary, dpi));
    }

    [Fact]
    public void IntegerLimitMonitor_UsesWideArithmeticForSmallValidIcon()
    {
        Assert.True(TrayContextMenuPlacementPolicy.CanUseShellIconRect(
            Rect(int.MinValue, int.MinValue, int.MinValue + 32, int.MinValue + 32),
            new DrawingPoint(int.MinValue + 16, int.MinValue + 16),
            Rect(int.MinValue, int.MinValue, int.MinValue + 2560, int.MinValue + 1440), 1));
    }

    private static Win32Helper.RECT Rect(int left, int top, int right, int bottom) =>
        new() { Left = left, Top = top, Right = right, Bottom = bottom };
}
