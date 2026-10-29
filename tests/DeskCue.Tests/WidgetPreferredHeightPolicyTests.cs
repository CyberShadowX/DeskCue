using DeskCue.Helpers;
using Windows.Graphics;

namespace DeskCue.Tests;

public class WidgetPreferredHeightPolicyTests
{
    [Theory]
    [InlineData(100, 200)]
    [InlineData(480, 500)]
    [InlineData(2000, 900)]
    public void Height_GrowsShrinksAndCaps(double content, int expected)
    {
        var result = WidgetPreferredHeightPolicy.Resolve(new RectInt32(10, 10, 320, 400), new RectInt32(0, 0, 1200, 900), content, 20, 1, 200);
        Assert.Equal(expected, result.Height);
        Assert.Equal(320, result.Width);
    }

    [Theory]
    [InlineData(1.0, 421)]
    [InlineData(1.25, 526)]
    [InlineData(1.5, 631)]
    public void Dpi_RoundsUpAndMovesOnlyEnoughToFit(double scale, int expected)
    {
        var result = WidgetPreferredHeightPolicy.Resolve(new RectInt32(-1000, 800, 333, 200), new RectInt32(-1200, 0, 1200, 1000), 400.1, 20, scale, 100);
        Assert.Equal(expected, result.Height);
        Assert.Equal(1000 - expected, result.Y);
        Assert.Equal(-1000, result.X);
        Assert.Equal(333, result.Width);
    }

    [Fact]
    public void MeasurementKey_WorkAreaChangeInvalidatesUnchangedWindow()
    {
        var bounds = new RectInt32(20, 20, 300, 600);
        var original = new DeskCue.Views.WidgetPreferredHeightMeasurementKey(bounds, 280, 1.25, new RectInt32(0, 0, 1200, 900));
        Assert.Equal(original, new DeskCue.Views.WidgetPreferredHeightMeasurementKey(bounds, 280, 1.25, new RectInt32(0, 0, 1200, 900)));
        Assert.NotEqual(original, new DeskCue.Views.WidgetPreferredHeightMeasurementKey(bounds, 280, 1.25, new RectInt32(0, 0, 1200, 700)));
        Assert.NotEqual(original, new DeskCue.Views.WidgetPreferredHeightMeasurementKey(bounds, 280, 1.25, new RectInt32(0, 40, 1200, 900)));
    }

    [Fact]
    public void SamePhysicalResult_IsNoOp()
    {
        var current = new RectInt32(20, 20, 300, 421);
        Assert.Equal(current, WidgetPreferredHeightPolicy.Resolve(current, new RectInt32(0, 0, 1000, 900), 400.2, 20, 1, 200));
    }

    [Fact]
    public void ImpossibleMinimumOrWidth_PreservesExistingBounds()
    {
        var current = new RectInt32(0, 0, 1200, 400);
        Assert.Equal(current, WidgetPreferredHeightPolicy.Resolve(current, new RectInt32(0, 0, 1000, 900), 100, 20, 1, 200));
        Assert.Equal(current, WidgetPreferredHeightPolicy.Resolve(current, new RectInt32(0, 0, 1400, 100), 100, 20, 1, 200));
    }
}
