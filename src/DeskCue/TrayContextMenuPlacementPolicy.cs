using DeskCue.Platform;
using DrawingPoint = System.Drawing.Point;

namespace DeskCue;

/// <summary>Physical-pixel decisions for a pointer-originated tray menu.</summary>
internal static class TrayContextMenuPlacementPolicy
{
    internal static bool CanUseShellIconRect(
        Win32Helper.RECT iconRect,
        DrawingPoint capturedPoint,
        Win32Helper.RECT originatingMonitor,
        double dpiScale)
    {
        // Shell_NotifyIconGetRect can still describe Explorer's icon while a
        // replacement tray forwards this click from a different screen edge.
        // All inputs are physical pixels; only the small allowance uses DPI.
        double scale = double.IsFinite(dpiScale) && dpiScale > 0
            ? Math.Clamp(dpiScale, 0.5, 4)
            : 1;
        long tolerance = (long)Math.Ceiling(12 * scale);
        long maximumIconExtent = (long)Math.Ceiling(128 * scale);
        long width = (long)iconRect.Right - iconRect.Left;
        long height = (long)iconRect.Bottom - iconRect.Top;
        if (width <= 0 || height <= 0 ||
            width > maximumIconExtent || height > maximumIconExtent ||
            originatingMonitor.Right <= originatingMonitor.Left ||
            originatingMonitor.Bottom <= originatingMonitor.Top ||
            iconRect.Left < originatingMonitor.Left || iconRect.Right > originatingMonitor.Right ||
            iconRect.Top < originatingMonitor.Top || iconRect.Bottom > originatingMonitor.Bottom ||
            capturedPoint.X < originatingMonitor.Left || capturedPoint.X >= originatingMonitor.Right ||
            capturedPoint.Y < originatingMonitor.Top || capturedPoint.Y >= originatingMonitor.Bottom)
        {
            return false;
        }

        return capturedPoint.X >= (long)iconRect.Left - tolerance &&
            capturedPoint.X <= (long)iconRect.Right + tolerance &&
            capturedPoint.Y >= (long)iconRect.Top - tolerance &&
            capturedPoint.Y <= (long)iconRect.Bottom + tolerance;
    }
}

internal enum TrayContextMenuPresentation
{
    Unknown,
    Visible,
    Cloaked
}

/// <summary>One presentation decision for each actual menu-open attempt.</summary>
internal sealed class TrayContextMenuPresentationPolicy
{
    private long _attempt;
    private bool _completed;

    internal long BeginAttempt()
    {
        _completed = false;
        return ++_attempt;
    }

    internal bool IsCurrent(long attempt) => attempt == _attempt && !_completed;

    internal void Cancel(long attempt)
    {
        if (attempt == _attempt)
        {
            _completed = true;
        }
    }

    internal bool TryComplete(
        long attempt,
        TrayContextMenuPresentation presentation,
        Action recordSuccess,
        Action closeSecondWindow,
        Action switchToNative,
        Action showNative)
    {
        if (!IsCurrent(attempt))
        {
            return false;
        }

        // Missing public host/DWM evidence does not establish failure or
        // success. Allow another bounded probe without changing menu mode.
        if (presentation == TrayContextMenuPresentation.Unknown)
        {
            return false;
        }

        _completed = true;
        if (presentation == TrayContextMenuPresentation.Cloaked)
        {
            // H.NotifyIcon chooses which host to close using the current mode.
            // Closing after the switch would leave its SecondWindow alive.
            closeSecondWindow();
            switchToNative();
            showNative();
        }
        else
        {
            recordSuccess();
        }

        return true;
    }
}
