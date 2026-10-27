using DeskCue.Services;

namespace DeskCue.ViewModels;

public sealed partial class SettingsViewModel
{
    public void RefreshManagedStorageState()
    {
        ManagedStorageRootPath = SettingsService.NormalizeManagedStorageRootPath(
            _settingsService.Settings.DefaultManagedStorageRootPath);
    }
}
