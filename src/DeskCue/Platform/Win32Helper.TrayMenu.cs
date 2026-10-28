namespace DeskCue.Platform;

public static partial class Win32Helper
{
    /// <summary>
    /// A successful show call is insufficient when a shell extension cloaks
    /// the menu's real WinUI host. Only query a current, visible, owned host;
    /// an unavailable DWM attribute is unknown rather than a failure.
    /// </summary>
    internal static TrayContextMenuPresentation GetOwnedTrayMenuPresentation(IntPtr hwnd)
    {
        if (hwnd == IntPtr.Zero ||
            GetWindowThreadProcessId(hwnd, out uint processId) == 0 ||
            processId != (uint)Environment.ProcessId ||
            !IsWindowVisible(hwnd))
        {
            return TrayContextMenuPresentation.Unknown;
        }

        try
        {
            if (DwmGetWindowAttribute(hwnd, DWMWA_CLOAKED, out int cloaked, sizeof(int)) != 0)
            {
                return TrayContextMenuPresentation.Unknown;
            }

            return cloaked == 0
                ? TrayContextMenuPresentation.Visible
                : TrayContextMenuPresentation.Cloaked;
        }
        catch (Exception ex) when (
            ex is DllNotFoundException or EntryPointNotFoundException or BadImageFormatException)
        {
            return TrayContextMenuPresentation.Unknown;
        }
    }
}
