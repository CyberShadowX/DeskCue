using DeskBox.Services;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;

namespace DeskBox.Controls;

/// <summary>
/// Two-stage menu material: the MenuFlyoutPresenter paints the opaque
/// fallback brush for the first frame (no bare text while the acrylic
/// backdrop lands), then the brush fades out to reveal the
/// DesktopAcrylicBackdrop set by the implicit presenter style; the next
/// menu round starts solid again. All theme-dictionary instances fade
/// together so a per-window theme override never leaves a stale solid
/// brush behind. High contrast keeps the solid fallback — the acrylic mix
/// must not thin system contrast colors. Opacity is stepped by a
/// dispatcher timer instead of a storyboard: string-path animation
/// metadata is not rooted under NativeAOT, and a manual step is
/// deterministic there. Timing constants come from the retired icon-strip
/// reveal rhythm (artifacts/context-menu-enhancement-20261015 债项).
/// </summary>
internal static class MenuFlyoutMaterial
{
    private const int RevealDelayMs = 150;
    private const int RevealDurationMs = 280;
    private const int StepMs = 16;

    private static SolidColorBrush[]? s_fallbackBrushes;
    private static DispatcherQueueTimer? s_activeTimer;

    public static void Attach(MenuFlyout flyout)
    {
        if (WindowsCompatibilityService.IsHighContrast)
        {
            return;
        }

        flyout.Opened += (_, _) => BeginReveal(flyout.DispatcherQueue);
        flyout.Closed += (_, _) => SetFallbackOpacity(1);
    }

    private static void BeginReveal(DispatcherQueue queue)
    {
        s_activeTimer?.Stop();
        SetFallbackOpacity(1);

        var timer = queue.CreateTimer();
        timer.Interval = TimeSpan.FromMilliseconds(StepMs);
        int elapsed = -RevealDelayMs;
        timer.Tick += (_, _) =>
        {
            elapsed += StepMs;
            if (elapsed < 0)
            {
                return;
            }

            double progress = Math.Min(
                1d,
                elapsed / (double)RevealDurationMs);
            // Cubic ease-out matches the retired icon-strip reveal rhythm.
            double eased = 1 - Math.Pow(1 - progress, 3);
            SetFallbackOpacity(1 - eased);
            if (progress >= 1)
            {
                timer.Stop();
            }
        };

        s_activeTimer = timer;
        timer.Start();
    }

    private static void SetFallbackOpacity(double opacity)
    {
        foreach (SolidColorBrush brush in ResolveFallbackBrushes())
        {
            brush.Opacity = opacity;
        }
    }

    private static SolidColorBrush[] ResolveFallbackBrushes()
    {
        if (s_fallbackBrushes is not null)
        {
            return s_fallbackBrushes;
        }

        var brushes = new List<SolidColorBrush>();
        if (Application.Current?.Resources is { } resources)
        {
            foreach (KeyValuePair<object, object> pair in
                         resources.ThemeDictionaries)
            {
                if (pair.Value is ResourceDictionary dictionary &&
                    dictionary.TryGetValue(
                        "DeskBoxMenuFallbackBackgroundBrush",
                        out object? value) &&
                    value is SolidColorBrush brush)
                {
                    brushes.Add(brush);
                }
            }
        }

        return s_fallbackBrushes = brushes.ToArray();
    }
}
