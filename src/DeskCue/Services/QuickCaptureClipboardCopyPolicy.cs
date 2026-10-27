using DeskCue.Models;
using DeskCue.ViewModels;

namespace DeskCue.Services;

internal static class QuickCaptureClipboardCopyPolicy
{
    public static bool ShouldCopyBitmap(QuickCaptureItemViewModel item) =>
        item.IsRecent && item.Type == QuickCaptureItemType.Image;
}
