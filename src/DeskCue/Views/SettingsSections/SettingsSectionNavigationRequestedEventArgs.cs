namespace DeskCue.Views.SettingsSections;

public sealed class SettingsSectionNavigationRequestedEventArgs(string sectionTag) : EventArgs
{
    public string SectionTag { get; } = sectionTag;
}
