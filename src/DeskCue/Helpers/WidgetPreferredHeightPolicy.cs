using Windows.Graphics;

namespace DeskCue.Helpers;

/// <summary>Converts measured DIP content into work-area bounded physical geometry.</summary>
internal static class WidgetPreferredHeightPolicy
{
    internal static RectInt32 Resolve(RectInt32 current, RectInt32 workArea,
        double contentHeight, double chromeHeight, double scale, int minimumHeight)
    {
        if (!double.IsFinite(contentHeight) || !double.IsFinite(chromeHeight) ||
            !double.IsFinite(scale) || scale <= 0 || contentHeight < 0 || chromeHeight < 0 ||
            workArea.Height < minimumHeight || workArea.Width < current.Width || workArea.Height <= 0)
            return current;

        int height = (int)Math.Clamp(Math.Ceiling((contentHeight + chromeHeight) * scale),
            Math.Max(1, minimumHeight), workArea.Height);
        return new RectInt32(
            Math.Clamp(current.X, workArea.X, workArea.X + workArea.Width - current.Width),
            Math.Clamp(current.Y, workArea.Y, workArea.Y + workArea.Height - height),
            current.Width, height);
    }
}
