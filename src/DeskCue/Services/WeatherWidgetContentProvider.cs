using DeskCue.Contracts;
using DeskCue.Controls.WidgetContents;
using DeskCue.Models;

namespace DeskCue.Services;

internal sealed class WeatherWidgetContentProvider : IWidgetContentProvider
{
    public WidgetKind WidgetKind => WidgetKind.Weather;

    public bool CanCreateDetachedContent => true;

    public IWidgetContent CreateDetachedContent(WidgetConfig config, WidgetContentProviderContext context)
    {
        if (config.WidgetKind != WidgetKind)
        {
            throw new ArgumentException("Weather content requires a Weather widget config.", nameof(config));
        }

        WeatherService? weatherService = null;
#if DESKCUE_NATIVE_AOT && DESKCUE_AOT_SMOKE_HARNESS
        weatherService = AotWeatherSurfaceFixture.TryCreateService(config);
#endif
        return new WeatherWidgetContentAdapter(
            config,
            context.LocalizationService,
            context.SettingsService,
            weatherService);
    }
}
