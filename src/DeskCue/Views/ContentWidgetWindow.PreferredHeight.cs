using DeskCue.Contracts;
using DeskCue.Helpers;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Windowing;
using Windows.Graphics;

namespace DeskCue.Views;

public sealed partial class ContentWidgetWindow
{
    private IWidgetPreferredHeightContent? _preferredHeightSource;
    private DispatcherQueueTimer? _preferredHeightTimer;
    private bool _preferredHeightPending;
    private bool _preferredHeightQueued;
    private (RectInt32 Bounds, double Width, double Scale)? _preferredHeightSignature;

    private void AttachPreferredHeightSource(IWidgetContent? content)
    {
        if (_preferredHeightSource is not null)
            _preferredHeightSource.PreferredHeightInvalidated -= PreferredHeight_Invalidated;
        _preferredHeightTimer?.Stop();
        _preferredHeightSource = content as IWidgetPreferredHeightContent;
        _preferredHeightSignature = null;
        _preferredHeightPending = _preferredHeightSource is not null;
        if (_preferredHeightSource is null) return;
        _preferredHeightSource.PreferredHeightInvalidated += PreferredHeight_Invalidated;
        if (_preferredHeightTimer is null)
        {
            _preferredHeightTimer = DispatcherQueue.CreateTimer();
            _preferredHeightTimer.Interval = TimeSpan.FromMilliseconds(500);
            _preferredHeightTimer.Tick += (_, _) => ApplyPreferredHeight();
        }
        // One cheap state poll handles unlock and transition completion, which have
        // several independent host paths. It never measures an inactive cached view.
        _preferredHeightTimer.Start();
        QueuePreferredHeight();
    }

    private void PreferredHeight_Invalidated(object? sender, EventArgs e)
    {
        if (!ReferenceEquals(sender, CurrentContent)) return;
        _preferredHeightPending = true;
        QueuePreferredHeight();
    }

    private void QueuePreferredHeight()
    {
        if (_preferredHeightQueued || IsClosing) return;
        _preferredHeightQueued = true;
        if (!DispatcherQueue.TryEnqueue(DispatcherQueuePriority.Low, () =>
        {
            _preferredHeightQueued = false;
            ApplyPreferredHeight();
        })) _preferredHeightQueued = false;
    }

    private void ApplyPreferredHeight()
    {
        if (_preferredHeightSource is null || !ReferenceEquals(_preferredHeightSource, CurrentContent) || IsClosing) return;
        if (!Visible || IsSizeLocked || IsDragging || IsResizing || IsHideAnimationRunning ||
            IsCompactBoundsStateActive || IsCompactTransitionActive || IsBoundsTransitionActive || !CanPersistBoundsChange(true))
        {
            _preferredHeightPending = true;
            return;
        }
        var view = CurrentContent!.View;
        double scale = view.XamlRoot?.RasterizationScale ?? 1;
        var current = new RectInt32(AppWindow.Position.X, AppWindow.Position.Y, AppWindow.Size.Width, AppWindow.Size.Height);
        var signature = (current, view.ActualWidth, scale);
        if (!_preferredHeightPending && _preferredHeightSignature?.Equals(signature) == true) return;
        _preferredHeightSignature = signature;
        if (view.ActualWidth <= 0 || view.ActualHeight <= 0) return;
        var area = DisplayArea.GetFromWindowId(AppWindow.Id, DisplayAreaFallback.Nearest)?.WorkArea;
        if (area is not { } workArea) return;
        double chrome = Math.Max(0, current.Height / scale - view.ActualHeight);
        if (!_preferredHeightSource.TryMeasurePreferredContentHeight(view.ActualWidth, workArea.Height / scale - chrome, out double height)) return;
        _preferredHeightPending = false;
        var minimum = GetPhysicalMinimumWindowSize(current.X, current.Y, current.Width, current.Height);
        if (current.Width < minimum.Width) return;
        var result = WidgetPreferredHeightPolicy.Resolve(current, workArea, height, chrome, scale, minimum.Height);
        if (result.Equals(current)) return;
        ApplyWindowBounds(result.X, result.Y, result.Width, result.Height, persist: true);
    }
}
