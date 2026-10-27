using System.Reflection;
using System.Text.Json;
using System.Text.RegularExpressions;
using DeskCue.Models;
using DeskCue.Services;

namespace DeskCue.Tests;

/// <summary>
/// Ownership contract for the 2A settings slice refactor. AppSettings is a
/// serialization facade: every public settable property must delegate to
/// exactly one *SettingsSlice object, and the wire shape must stay identical.
/// </summary>
public sealed class SettingsSliceOwnershipContractTests
{
    private static readonly PropertyInfo[] SliceProperties =
        typeof(AppSettings).GetProperties(BindingFlags.Instance | BindingFlags.Public)
            .Where(p => p.PropertyType.Name.EndsWith("SettingsSlice", StringComparison.Ordinal))
            .ToArray();

    private static readonly PropertyInfo[] FacadeProperties =
        typeof(AppSettings).GetProperties(BindingFlags.Instance | BindingFlags.Public)
            .Where(p => p is { CanRead: true, CanWrite: true }
                        && p.Name != nameof(AppSettings.SchemaVersion)
                        && !p.PropertyType.Name.EndsWith("SettingsSlice", StringComparison.Ordinal))
            .ToArray();

    [Fact]
    public void EverySlice_IsExposedAsGetOnlyAndJsonIgnored()
    {
        Assert.Equal(13, SliceProperties.Length);
        Assert.All(SliceProperties, p =>
        {
            Assert.False(p.CanWrite, $"{p.Name} must be get-only");
            Assert.NotNull(p.GetCustomAttribute<System.Text.Json.Serialization.JsonIgnoreAttribute>());
        });
    }

    [Fact]
    public void EveryFacadeProperty_MapsToExactlyOneSliceProperty()
    {
        // 241 = batch-51 level (236) plus widgetGroupSwitchAnimationStyle
        // (group member-switch transition style) plus
        // musicHideTimelineWhenUnavailable (music timeline-row hiding) plus
        // fullyElevatedNoticeAcknowledgedUtcTicks (one-time
        // fully-elevated-desktop notice ack; nullable long, schema v15)
        // plus the parallel update-UX batch's showReleaseNotesAfterUpdate
        // and lastRunVersion.
        // +2 = autoDownloadUpdates + showUpdateToastNotification (background
        // auto-download and update toasts).
        Assert.Equal(243, FacadeProperties.Length);

        foreach (PropertyInfo facade in FacadeProperties)
        {
            var matches = SliceProperties
                .Select(s => s.PropertyType.GetProperty(facade.Name))
                .Where(candidate => candidate is { CanRead: true, CanWrite: true }
                                    && candidate.PropertyType == facade.PropertyType)
                .ToArray();
            Assert.Single(matches);
        }
    }

    [Fact]
    public void EverySliceProperty_IsReachableThroughTheFacade()
    {
        var facadeNames = FacadeProperties.Select(p => p.Name).ToHashSet(StringComparer.Ordinal);
        foreach (PropertyInfo slice in SliceProperties)
        {
            foreach (PropertyInfo prop in slice.PropertyType.GetProperties(
                         BindingFlags.Instance | BindingFlags.Public))
            {
                Assert.Contains(prop.Name, facadeNames);
            }
        }
    }

    [Fact]
    public void FacadePassthroughs_ReadAndWriteSliceState()
    {
        var settings = new AppSettings();

        foreach (PropertyInfo facade in FacadeProperties)
        {
            object? sentinel = NonDefaultValue(facade.PropertyType);
            facade.SetValue(settings, sentinel);

            PropertyInfo? sliceProp = SliceProperties
                .Select(s => s.PropertyType.GetProperty(facade.Name))
                .Single(candidate => candidate is { CanRead: true, CanWrite: true }
                                     && candidate.PropertyType == facade.PropertyType);
            Assert.NotNull(sliceProp);
            PropertyInfo slice = SliceProperties
                .Single(s => s.PropertyType == sliceProp.DeclaringType);

            Assert.Equal(
                SerializeSettingValue(sentinel, facade.PropertyType),
                SerializeSettingValue(sliceProp.GetValue(slice.GetValue(settings)), facade.PropertyType));
        }
    }

    [Fact]
    public void Serialization_PopulatedRoundTrip_IsStable()
    {
        var settings = new AppSettings { LegacyWidgetCapsuleModeEnabled = true };
        foreach (PropertyInfo facade in FacadeProperties)
        {
            facade.SetValue(settings, NonDefaultValue(facade.PropertyType));
        }

        string first = JsonSerializer.Serialize(
            settings, SettingsJsonContext.Default.AppSettings);
        AppSettings? restored = JsonSerializer.Deserialize(
            first, SettingsJsonContext.Default.AppSettings);
        Assert.NotNull(restored);
        string second = JsonSerializer.Serialize(
            restored, SettingsJsonContext.Default.AppSettings);

        Assert.Equal(first, second);
    }

    [Fact]
    public void Serialization_DisabledFeatureSections_RoundTripUnchanged()
    {
        // Simulate a profile where feature widgets are disabled but their
        // section data must still round-trip (disable→save→enable must not
        // reset the section).
        var settings = new AppSettings
        {
            QuickCaptureEnabled = false,
            TodoEnabled = false,
            FeatureWidgetEnabledStates = new Dictionary<string, bool>
            {
                ["Music"] = false,
                ["Weather"] = false,
            },
        };
        settings.QuickCapture.QuickCaptureRecentLimit = 87;
        settings.Todo.TodoDefaultReminderOffsetMinutes = 42;
        settings.Weather.WeatherCityName = "Hanoi";
        settings.Search.SearchDefaultTab = "file";

        string json = JsonSerializer.Serialize(
            settings, SettingsJsonContext.Default.AppSettings);
        AppSettings? restored = JsonSerializer.Deserialize(
            json, SettingsJsonContext.Default.AppSettings);

        Assert.NotNull(restored);
        Assert.Equal(87, restored.QuickCapture.QuickCaptureRecentLimit);
        Assert.Equal(42, restored.Todo.TodoDefaultReminderOffsetMinutes);
        Assert.Equal("Hanoi", restored.Weather.WeatherCityName);
        Assert.Equal("file", restored.Search.SearchDefaultTab);
        Assert.Equal(
            json,
            JsonSerializer.Serialize(restored, SettingsJsonContext.Default.AppSettings));
    }

    private static object? NonDefaultValue(Type type)
    {
        if (Nullable.GetUnderlyingType(type) is { IsEnum: true } enumType)
            return Enum.GetValues(enumType).Cast<object>().First();
        if (type == typeof(string))
            return "sentinel";
        if (type == typeof(bool))
            return true;
        if (type == typeof(bool?))
            return true;
        if (type == typeof(int))
            return 17;
        if (type == typeof(int?))
            return 17;
        if (type == typeof(double))
            return 0.137;
        if (type == typeof(double?))
            return 0.137;
        if (type == typeof(long))
            return 638000000000000000L;
        if (type == typeof(long?))
            return 638000000000000000L;
        if (type == typeof(DateTimeOffset?))
            return new DateTimeOffset(2030, 1, 2, 3, 4, 5, TimeSpan.Zero);
        if (type.IsEnum)
            return Enum.GetValues(type).Cast<object>().First();
        if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>))
        {
            var list = (System.Collections.IList)Activator.CreateInstance(type)!;
            Type itemType = type.GetGenericArguments()[0];
            list.Add(itemType == typeof(string)
                ? "sentinel"
                : Activator.CreateInstance(itemType)!);
            return list;
        }
        if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(Dictionary<,>))
        {
            var dict = (System.Collections.IDictionary)Activator.CreateInstance(type)!;
            Type[] args = type.GetGenericArguments();
            object key = args[0] == typeof(string)
                ? "sentinel"
                : Activator.CreateInstance(args[0])!;
            object value = args[1] == typeof(bool)
                ? true
                : Activator.CreateInstance(args[1])!;
            dict.Add(key, value);
            return dict;
        }
        throw new NotSupportedException($"No sentinel factory for {type}.");
    }

    // Facade-access ratchet: exact per-file counts of `X.settings.<passthrough>`
    // accesses measured on 2026-10-02 — case-insensitive on `settings` so
    // `settings.`/`_settings.` locals are counted too (letter-lookbehind keeps
    // `WidgetSettings.`/`appSettings.` out). Entries may only shrink or
    // disappear: a growing file or a new file means new facade coupling — new
    // code should read the slices (Settings.<Slice>.Prop). Deleting a
    // passthrough forces its call sites to migrate or stop compiling, so the
    // name set self-maintains as the facade collapses.
    // Batch 51 reconciliation: every budget was re-measured against the tree
    // after the batch 40-50 editor migrations and tightened to the exact
    // current counts (12 entries shrunk — 268 units of stale slack removed so
    // any new facade access fails immediately; 4 files hit zero and lost
    // their entries: QuickCaptureClipboardActivationHelper,
    // SettingsViewModel.DisplayNames, SettingsViewModel.PreferenceCommands,
    // SettingsViewModel.WidgetForeground).
    private static readonly IReadOnlyDictionary<string, int> FacadeAccessManifest =
        new Dictionary<string, int>(StringComparer.Ordinal)
    {
        ["src/DeskCue/App.AotHotkeySmoke.cs"] = 2,
        ["src/DeskCue/App.AotManagedUiSmoke.cs"] = 6,
        ["src/DeskCue/App.AotTodoNotificationActivationSmoke.cs"] = 5,
        ["src/DeskCue/App.AotTodoNotificationForwardingSmoke.cs"] = 4,
        ["src/DeskCue/App.AotTodoNotificationSurfaceSmoke.cs"] = 5,
        ["src/DeskCue/App.AotTodoNotificationUserClickSmoke.cs"] = 8,
        ["src/DeskCue/App.AotTodoRecurrenceReminderSmoke.cs"] = 6,
        ["src/DeskCue/App.AotWeatherSettingsPersistenceSmoke.cs"] = 17,
        ["src/DeskCue/App.AotWeatherSurfacePersistenceSmoke.cs"] = 17,
        ["src/DeskCue/App.DiagnosticsBundle.cs"] = 6,
        ["src/DeskCue/App.ImmediateHiddenWorkingSetTrim.cs"] = 2,
        ["src/DeskCue/App.Tray.cs"] = 3,
        ["src/DeskCue/App.xaml.cs"] = 36,
        ["src/DeskCue/Controls/DesktopOrganizationPreviewCard.xaml.cs"] = 11,
        ["src/DeskCue/Controls/DesktopOrganizationTaskView.Appearance.cs"] = 1,
        ["src/DeskCue/Controls/DesktopOrganizationTaskView.xaml.cs"] = 1,
        ["src/DeskCue/Controls/WidgetContents/FileSurfaceContent.IconSizing.cs"] = 1,
        ["src/DeskCue/Controls/WidgetContents/FileSurfaceContent.KeyboardNavigation.cs"] = 1,
        ["src/DeskCue/Controls/WidgetContents/FileSurfaceContent.SelectionAndMenus.cs"] = 1,
        ["src/DeskCue/Controls/WidgetContents/FileSurfaceContent.ShortcutDrop.cs"] = 1,
        ["src/DeskCue/Controls/WidgetContents/FileSurfaceContent.StackPopover.cs"] = 16,
        ["src/DeskCue/Controls/WidgetContents/FileSurfaceContent.xaml.cs"] = 5,
        ["src/DeskCue/Controls/WidgetContents/QuickCaptureSurfaceContent.xaml.cs"] = 6,
        ["src/DeskCue/Controls/WidgetContents/SearchWidgetContent.xaml.cs"] = 6,
        ["src/DeskCue/Controls/WidgetContents/TodoWidgetContent.Menus.cs"] = 1,
        ["src/DeskCue/Controls/WidgetContents/TodoWidgetContent.xaml.cs"] = 1,
        ["src/DeskCue/Controls/WidgetShell.xaml.cs"] = 2,
        ["src/DeskCue/Services/AutoStartDefaultPolicy.cs"] = 1,
        ["src/DeskCue/Services/DataBackupSettingsPolicy.cs"] = 15,
        ["src/DeskCue/Services/DesktopAutoOrganizationWatcher.cs"] = 13,
        // 5 = legacy 4 + DesktopDoubleClickEnabled read backing the hook
        // watchdog's HookProbeWanted gate (activation service line 122).
        ["src/DeskCue/Services/DesktopDoubleClickActivationService.cs"] = 5,
        // TodoSettingsCoordinator reads Settings.Widgets once in the
        // reminder-reconcile change guard: the Todo widget id set has no
        // slice projection, and watching it keeps external widget deletions
        // reconciled without reacting to unrelated debounced saves.
        ["src/DeskCue/Services/TodoSettingsCoordinator.cs"] = 1,
        ["src/DeskCue/Services/DesktopOrganizationCoordinator.cs"] = 13,
        // 4 = the target-availability advisor's read-only mirror of the rule
        // gate: master switch, rule list, widget list, and tombstone list.
        // It only classifies targets for a warning and never writes.
        ["src/DeskCue/Services/DesktopOrganizationTargetAvailability.cs"] = 4,
        ["src/DeskCue/Services/DesktopOrganizationTransaction.Restore.cs"] = 3,
        ["src/DeskCue/Services/DesktopOrganizationTransaction.cs"] = 9,
        ["src/DeskCue/Services/DirectStartupService.cs"] = 2,
        ["src/DeskCue/Services/DragDropPermissionService.cs"] = 3,
        ["src/DeskCue/Services/EverythingSearchService.cs"] = 12,
        ["src/DeskCue/Services/FeatureWidgetSettings.cs"] = 13,
        ["src/DeskCue/Services/FileWidgetFolderOpenBehaviorNames.cs"] = 1,
        ["src/DeskCue/Services/FileWidgetIconLayout.cs"] = 6,
        // +1 each: the watchdog chord heartbeat reads the enabled flag once
        // per cycle via RegistrationMaintenanceWanted (feedback 308/371 fix).
        ["src/DeskCue/Services/GlobalHotkeyService.cs"] = 18,
        ["src/DeskCue/Services/InitialFileWidgetSetupPolicy.cs"] = 2,
        ["src/DeskCue/Services/JumpListService.cs"] = 1,
        ["src/DeskCue/Services/LocalizationService.cs"] = 3,
        ["src/DeskCue/Services/ManagedStorageDesktopShortcutService.cs"] = 12,
        ["src/DeskCue/Services/PerformanceSettingsPolicy.cs"] = 78,
        ["src/DeskCue/Services/QuickCaptureClipboardService.cs"] = 6,
        ["src/DeskCue/Services/SearchEngineService.cs"] = 7,
        ["src/DeskCue/Services/SearchHotkeyService.cs"] = 13,
        ["src/DeskCue/Services/SearchResultActionService.cs"] = 2,
        ["src/DeskCue/Services/SettingsMigrationService.cs"] = 55,
        ["src/DeskCue/Services/SettingsSearchCatalog.cs"] = 25,
        ["src/DeskCue/Services/SettingsService.cs"] = 613,
        ["src/DeskCue/Services/ThemeService.cs"] = 11,
        ["src/DeskCue/Views/SettingsSections/DisplaySettingsSection.xaml.cs"] = 14,
        ["src/DeskCue/Services/TodoReminderService.cs"] = 8,
        ["src/DeskCue/Services/WeatherService.cs"] = 1,
        ["src/DeskCue/Services/WeatherSettingsPolicy.cs"] = 18,
        ["src/DeskCue/Services/WidgetAnimationSettings.cs"] = 4,
        ["src/DeskCue/Services/WidgetChromeMenuBuilder.cs"] = 5,
        ["src/DeskCue/Services/WidgetChromeModeResolver.cs"] = 2,
        ["src/DeskCue/Services/WidgetForegroundSettings.cs"] = 8,
        ["src/DeskCue/Services/WidgetGroupMenuBuilder.cs"] = 1,
        ["src/DeskCue/Services/WidgetGroupSettings.cs"] = 19,
        ["src/DeskCue/Services/WidgetManager.NewWidgetPlacement.cs"] = 4,
        ["src/DeskCue/Services/DisplayIdentityTokens.cs"] = 2,
        ["src/DeskCue/Services/WidgetManager.MoveAll.cs"] = 9,
        ["src/DeskCue/Services/WidgetManager.ScreenHome.cs"] = 2,
        ["src/DeskCue/Services/WidgetManager.CapsuleArrangement.cs"] = 45,
        ["src/DeskCue/Services/WidgetManager.FeatureWidgets.cs"] = 50,
        ["src/DeskCue/Services/WidgetManager.Groups.cs"] = 55,
        ["src/DeskCue/Services/WidgetManager.Storage.cs"] = 20,
        ["src/DeskCue/Services/WidgetManager.Surfaces.cs"] = 1,
        ["src/DeskCue/Services/WidgetManager.TrayAnimation.cs"] = 4,
        ["src/DeskCue/Services/WidgetManager.cs"] = 31,
        ["src/DeskCue/Services/WidgetStartupRestorePolicy.cs"] = 2,
        ["src/DeskCue/Services/WidgetTopologyLayoutService.cs"] = 23,
        ["src/DeskCue/ViewModels/GlanceWidgetViewModel.cs"] = 4,
        ["src/DeskCue/ViewModels/MusicWidgetViewModel.Lifecycle.cs"] = 1,
        ["src/DeskCue/ViewModels/MusicWidgetViewModel.cs"] = 5,
        ["src/DeskCue/ViewModels/QuickCaptureWidgetViewModel.ItemSync.cs"] = 2,
        ["src/DeskCue/ViewModels/QuickCaptureWidgetViewModel.Operations.cs"] = 3,
        ["src/DeskCue/ViewModels/QuickCaptureWidgetViewModel.SettingsAndRefresh.cs"] = 14,
        ["src/DeskCue/ViewModels/QuickCaptureWidgetViewModel.cs"] = 17,
        ["src/DeskCue/ViewModels/SearchPopupViewModel.cs"] = 13,
        // Batch 29 moved the appearance section writes into
        // AppearanceSettingsCoordinator; AppearanceCallbacks reached zero and
        // lost its entry. Batch 33 moved the capsule/compact section writes
        // into CapsuleSettingsCoordinator (CapsuleOptions 34->20, leaving only
        // widget/group override-list reads; AppearanceOptions 4->2). Batch 34
        // moved the interaction section writes into
        // InteractionSettingsCoordinator (PreferenceCallbacks 17->6, leaving
        // the file-display section for batch 35; HoverActions 1->0 and lost
        // its entry; AppearanceOptions 2->1, only the widget list read of the
        // chrome-override reset remains). Batch 35 moved the file-display
        // section writes into FileDisplaySettingsCoordinator
        // (PreferenceCallbacks 6->0 and lost its entry; the only remaining
        // facade-shaped access is the QuiescenceWorkingSetTrimEnabled write
        // through the Performance slice, which is not a passthrough). Batch 36
        // moved the file-stack section writes (master switch, auto-stacking,
        // grouping, threshold, ordering, open mode, popover layout/style,
        // unmatched behavior and the custom-rule collection) into
        // FileStackSettingsCoordinator (FileStackOptions 32->22, leaving only
        // the constructor/snapshot reads and the Widgets preview read).
        // Batch 38 moved the feature-section writes (music presentation,
        // weather options incl. the policy path, feature-card enable states,
        // attachment storage, managed-drop action, folder-open behavior, and
        // the music/weather feature-reset defaults) into
        // FeatureWidgetsSettingsCoordinator, and the Quick Capture editor
        // group into the existing QuickCaptureSettingsCoordinator
        // (FeatureCallbacks 25->0 and lost its entry; WeatherOptions 2->1,
        // only the city-name restore read remains; ContentEditorOptions
        // 24->10, only the constructor/snapshot reads remain; batch 47 then
        // deleted ContentEditorOptions/FeatureTextSize whole when the Todo
        // section moved to its editor, and both lost their entries; batch 48
        // deleted WeatherOptions whole when the Weather section moved to its
        // editor — the city-name restore read went with the editor's
        // coordinator read port).
        // FeatureOptions
        // 68->2: both remaining matches are localization-key string literals
        // ("Settings.AttachmentStorageMode.Copy"/".Link"), not facade
        // accesses. Batch 39 moved the storage/diagnostics tail writes into
        // ManagedStorageSettingsCoordinator and MaintenanceSettingsCoordinator
        // (AboutAndUpdates 1->0 and lost its entry; PreferenceCommands 2->1,
        // only the ResizeSnapEnabled read of the restore-defaults
        // guide-overlay sync remains).
        ["src/DeskCue/ViewModels/SettingsViewModel.AppearanceOptions.cs"] = 1,
        ["src/DeskCue/ViewModels/SettingsViewModel.CapsuleOptions.cs"] = 20,
        ["src/DeskCue/ViewModels/SettingsViewModel.DesktopOrganization.cs"] = 1,
        ["src/DeskCue/ViewModels/SettingsViewModel.FileStackOptions.cs"] = 1,
        // Batch 37 moved the group-navigation default writes (wheel switch,
        // hover switch, default title display mode, default navigation style)
        // into GroupNavigationSettingsCoordinator (GroupNavigation 28->20,
        // leaving only the property/summary/projection reads; the four
        // setters no longer compare or write through the facade).
        ["src/DeskCue/ViewModels/SettingsViewModel.GroupNavigation.cs"] = 15,
        ["src/DeskCue/ViewModels/SettingsViewModel.HotkeyAndStorage.cs"] = 6,
        ["src/DeskCue/ViewModels/SettingsViewModel.RuntimeDiagnostics.cs"] = 1,
        ["src/DeskCue/ViewModels/SettingsViewModel.SettingsSync.cs"] = 7,
        ["src/DeskCue/ViewModels/SettingsViewModel.cs"] = 19,
        ["src/DeskCue/ViewModels/TodoWidgetViewModel.DetailAndAttachments.cs"] = 1,
        ["src/DeskCue/ViewModels/TodoWidgetViewModel.FilteringAndAppearance.cs"] = 21,
        ["src/DeskCue/ViewModels/TodoWidgetViewModel.cs"] = 12,
        ["src/DeskCue/ViewModels/WeatherWidgetViewModel.DataProcessing.cs"] = 21,
        ["src/DeskCue/ViewModels/WeatherWidgetViewModel.RefreshAndLayout.cs"] = 1,
        ["src/DeskCue/ViewModels/WeatherWidgetViewModel.cs"] = 24,
        ["src/DeskCue/ViewModels/WidgetViewModel.ItemHydration.cs"] = 3,
        ["src/DeskCue/ViewModels/WidgetViewModel.LayoutAndSettings.cs"] = 17,
        ["src/DeskCue/ViewModels/WidgetViewModel.Operations.cs"] = 2,
        ["src/DeskCue/ViewModels/WidgetViewModel.Stacks.cs"] = 13,
        ["src/DeskCue/ViewModels/WidgetViewModel.cs"] = 7,
        ["src/DeskCue/Views/ContentWidgetWindow.Commands.cs"] = 4,
        ["src/DeskCue/Views/ContentWidgetWindow.File.cs"] = 1,
        ["src/DeskCue/Views/ContentWidgetWindow.NativeDragDrop.cs"] = 3,
        ["src/DeskCue/Views/ContentWidgetWindow.QuickCapture.cs"] = 1,
        ["src/DeskCue/Views/ContentWidgetWindow.TrayAnimations.cs"] = 4,
        ["src/DeskCue/Views/ContentWidgetWindow.xaml.cs"] = 16,
        ["src/DeskCue/Views/OnboardingWindow.Steps.cs"] = 3,
        ["src/DeskCue/Views/OnboardingWindow.xaml.cs"] = 4,
        ["src/DeskCue/Views/QuickCaptureWidgetWindow.Appearance.cs"] = 3,
        ["src/DeskCue/Views/QuickCaptureWidgetWindow.Detail.cs"] = 2,
        ["src/DeskCue/Views/QuickCaptureWidgetWindow.Editing.cs"] = 1,
        ["src/DeskCue/Views/QuickCaptureWidgetWindow.Menus.cs"] = 2,
        ["src/DeskCue/Views/QuickCaptureWidgetWindow.ResponsiveDetail.cs"] = 2,
        ["src/DeskCue/Views/QuickCaptureWidgetWindow.xaml.cs"] = 12,
        ["src/DeskCue/Views/SearchPopupWindow.xaml.cs"] = 22,
        ["src/DeskCue/Views/SettingsSections/DesktopOrganizationSettingsSection.xaml.cs"] = 22,
        ["src/DeskCue/Views/SettingsWindow.HotkeyAndAppearance.cs"] = 4,
        ["src/DeskCue/Views/SettingsWindow.Maintenance.cs"] = 3,
        ["src/DeskCue/Views/SettingsWindow.Navigation.cs"] = 3,
        // The three hits are the Settings.WidgetGroups.DissolveDialog.*
        // localization key literals reused by the group-picker dissolve
        // confirmation (same keys the settings page dialog uses), not slice
        // property reads.
        ["src/DeskCue/Controls/WidgetGroupTitleSwitcher.xaml.cs"] = 3,
        ["src/DeskCue/Views/WidgetWindowBase.Backdrop.cs"] = 10,
        ["src/DeskCue/Views/WidgetWindowBase.Bounds.cs"] = 3,
        ["src/DeskCue/Views/WidgetWindowBase.Collapse.cs"] = 28,
    };

    private static readonly Regex FacadePassthroughAccess = new(
        @"(?<![A-Za-z])settings\.(?:" +
        string.Join('|', FacadeProperties.Select(p => p.Name).OrderByDescending(n => n.Length)) +
        @")\b",
        RegexOptions.Compiled | RegexOptions.IgnoreCase);

    [Fact]
    public void FacadePassthroughAccess_OnlyShrinks()
    {
        List<string> violations = new();
        foreach ((string path, string source) in ProductionSource())
        {
            int count = FacadePassthroughAccess.Matches(source).Count;
            if (count == 0)
            {
                continue;
            }

            if (!FacadeAccessManifest.TryGetValue(path, out int budget))
            {
                violations.Add($"  NEW {path}: {count}");
            }
            else if (count > budget)
            {
                violations.Add($"  GREW {path}: {count} (manifest {budget})");
            }
        }

        Assert.True(
            violations.Count == 0,
            "New facade passthrough accesses appeared. New settings code reads " +
            "the slices (Settings.<Slice>.Prop); extend the manifest only " +
            "consciously:\n" + string.Join('\n', violations));
    }

    private static IEnumerable<(string Path, string Source)> ProductionSource()
    {
        string projectDirectory = TestPaths.FromRepository("src/DeskCue");
        return Directory.EnumerateFiles(projectDirectory, "*.cs", SearchOption.AllDirectories)
            .Where(path =>
            {
                string relative = Path.GetRelativePath(projectDirectory, path)
                    .Replace(Path.DirectorySeparatorChar, '/');
                return !relative.StartsWith("bin/", StringComparison.OrdinalIgnoreCase) &&
                       !relative.StartsWith("obj/", StringComparison.OrdinalIgnoreCase) &&
                       !relative.StartsWith("AppPackages/", StringComparison.OrdinalIgnoreCase);
            })
            .Select(path => (RepositoryRelativePath(path), File.ReadAllText(path)));
    }

    private static string RepositoryRelativePath(string path) =>
        Path.GetRelativePath(TestPaths.FromRepository("."), path)
            .Replace(Path.DirectorySeparatorChar, '/');

    private static readonly JsonSerializerOptions s_jsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
    };

    private static string SerializeSettingValue(object? value, Type type) =>
        JsonSerializer.Serialize(value, type, s_jsonOptions);
}
