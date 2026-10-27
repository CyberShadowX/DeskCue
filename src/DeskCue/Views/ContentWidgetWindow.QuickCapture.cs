using DeskCue.Controls;
using DeskCue.Controls.WidgetContents;

namespace DeskCue.Views;

public sealed partial class ContentWidgetWindow
{
    private WidgetCompactPresentation CreateQuickCaptureCompactPresentation(
        QuickCaptureWidgetContentAdapter quickCapture,
        string contentMode)
    {
        bool hidesSensitiveContent =
            SettingsService.Settings.WidgetCompactHideSensitiveContent;
        var latestItem = quickCapture.ViewModel.Items.FirstOrDefault();
        string summary = contentMode switch
        {
            DeskCue.Services.SettingsService.WidgetCompactContentModeMinimal => string.Empty,
            DeskCue.Services.SettingsService.WidgetCompactContentModeSmart
                when !hidesSensitiveContent =>
                latestItem?.DisplayText?.ReplaceLineEndings(" ").Trim() ??
                App.Current.LocalizationService.Format(
                    "Widget.Compact.QuickCaptureCount",
                    quickCapture.ViewModel.RecordCount),
            _ => App.Current.LocalizationService.Format(
                "Widget.Compact.QuickCaptureCount",
                quickCapture.ViewModel.RecordCount)
        };

        return new WidgetCompactPresentation(
            quickCapture.ViewModel.DisplayName,
            summary,
            "\uE70F",
            App.Current.LocalizationService.T(
                "Widget.Compact.QuickCaptureDropHint"),
            UseStackedText:
                contentMode == DeskCue.Services.SettingsService.WidgetCompactContentModeSmart &&
                !hidesSensitiveContent,
            // Note bodies can be arbitrarily long; the capsule stays static
            // instead of marqueeing (same policy as Todo).
            LiveStateKey: string.Join(
                "|",
                quickCapture.ViewModel.RecordCount,
                summary));
    }
}
