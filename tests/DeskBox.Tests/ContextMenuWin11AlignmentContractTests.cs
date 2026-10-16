namespace DeskBox.Tests;

/// <summary>
/// Pins the Windows 11-aligned context menu shape: naming keys, item
/// ordering, the split View / Sort by submenus, and the process-isolation
/// boundary (Open With and New go through association/registry data only;
/// the classic IContextMenu path stays with the out-of-process proxy).
/// </summary>
public sealed class ContextMenuWin11AlignmentContractTests
{
    [Fact]
    public void ItemMenu_UsesWin11NamingKeys()
    {
        string builder = ReadRepositoryFile(
            "src/DeskBox/Controls/FileItemMenuBuilder.cs");

        foreach (string key in new[]
                 {
                     "Widget.Open",
                     "Widget.RunAsAdministrator",
                     "Widget.ExtractAll",
                     "Common.Cut",
                     "Common.Copy",
                     "Common.Rename",
                     "Widget.CompressToZip",
                     "Widget.CopyPath",
                     "Widget.MoveToRecycleBin",
                     "Widget.ShowInExplorer",
                     "Common.Properties",
                     "Widget.MoreSystemOperations",
                 })
        {
            Assert.Contains(key, builder, StringComparison.Ordinal);
        }
    }

    [Fact]
    public void ItemMenu_OpenFamilyLeads_PropertiesStayVisible_EscapeHatchLast()
    {
        string builder = ReadRepositoryFile(
            "src/DeskBox/Controls/FileItemMenuBuilder.cs");

        // Scope to the single-item flyout: shared helpers live at the end
        // of the file, so raw IndexOf on key literals would compare across
        // methods.
        int singleStart = builder.IndexOf(
            "public static MenuFlyout CreateItemFlyout(",
            StringComparison.Ordinal);
        int singleEnd = builder.IndexOf(
            "public static MenuFlyout CreateMultiSelectionFlyout(",
            StringComparison.Ordinal);
        Assert.True(singleStart >= 0 && singleEnd > singleStart);
        string single = builder[singleStart..singleEnd];

        int openWith = single.IndexOf(
            "AddOpenWithSubmenu(flyout, item, actions);",
            StringComparison.Ordinal);
        int cut = single.IndexOf(
            "\"Common.Cut\"",
            StringComparison.Ordinal);
        int compress = single.IndexOf(
            "AddCompressToZipItem(flyout, actions);",
            StringComparison.Ordinal);
        int copyPath = single.IndexOf(
            "\"Widget.CopyPath\"",
            StringComparison.Ordinal);
        int delete = single.IndexOf(
            "\"Widget.MoveToRecycleBin\"",
            StringComparison.Ordinal);
        int properties = single.IndexOf(
            "\"Common.Properties\"",
            StringComparison.Ordinal);
        int moreOptions = single.IndexOf(
            "AddShowMoreOptionsItem(flyout, item, actions);",
            StringComparison.Ordinal);

        Assert.True(openWith >= 0 && cut > openWith, "Open with leads");
        Assert.True(compress > cut && compress < copyPath,
            "Compress sits between the clipboard family and Copy as path");
        Assert.True(delete > copyPath, "Delete follows Copy as path");
        Assert.True(properties > delete,
            "Properties stays visible after Delete");
        Assert.True(moreOptions > properties,
            "Show more options is the last item");
    }

    [Fact]
    public void MultiSelectionMenu_AddsOpenAndCompress()
    {
        string builder = ReadRepositoryFile(
            "src/DeskBox/Controls/FileItemMenuBuilder.cs");

        string multiStart = builder.Substring(builder.IndexOf(
            "CreateMultiSelectionFlyout",
            StringComparison.Ordinal));
        Assert.Contains("Widget.Open", multiStart, StringComparison.Ordinal);
        Assert.Contains(
            "Widget.CompressToZip",
            multiStart,
            StringComparison.Ordinal);
        Assert.Contains(
            "await actions.OpenItemAsync(item);",
            multiStart,
            StringComparison.Ordinal);
    }

    [Fact]
    public void ContentAreaMenu_SplitsViewAndSort_AndAddsNewSubmenu()
    {
        string surface = ReadRepositoryFile(
            "src/DeskBox/Controls/WidgetContents/" +
            "FileSurfaceContent.SelectionAndMenus.cs");

        Assert.Contains(
            "T(\"Widget.View\")",
            surface,
            StringComparison.Ordinal);
        Assert.Contains(
            "T(\"Widget.SortBy\")",
            surface,
            StringComparison.Ordinal);
        Assert.Contains(
            "private MenuFlyoutSubItem CreateNewSubMenu",
            surface,
            StringComparison.Ordinal);
        Assert.Contains(
            "ShellNewMenuHelper.GetEntries()",
            surface,
            StringComparison.Ordinal);
        Assert.DoesNotContain(
            "T(\"Widget.ViewAndSort\")",
            surface,
            StringComparison.Ordinal);
    }

    [Fact]
    public void OpenWithAndNew_Paths_NeverHostClassicContextMenu()
    {
        string openWithInterop = ReadRepositoryFile(
            "src/DeskBox/Platform/ShellOpenWithInterop.cs");
        string openWithHelper = ReadRepositoryFile(
            "src/DeskBox/Helpers/ShellOpenWithHelper.cs");
        string shellNew = ReadRepositoryFile(
            "src/DeskBox/Helpers/ShellNewMenuHelper.cs");

        foreach (string source in new[] { openWithInterop, openWithHelper })
        {
            Assert.DoesNotContain(
                "IContextMenu",
                source,
                StringComparison.Ordinal);
            Assert.DoesNotContain(
                "QueryContextMenu",
                source,
                StringComparison.Ordinal);
            Assert.DoesNotContain(
                "TrackPopupMenuEx",
                source,
                StringComparison.Ordinal);
        }

        // The association API entry points stay pinned so the interop can
        // never silently drift onto the classic menu path.
        Assert.Contains(
            "SHAssocEnumHandlers",
            openWithInterop,
            StringComparison.Ordinal);
        Assert.Contains(
            "AssocFilterRecommended",
            openWithInterop,
            StringComparison.Ordinal);
        Assert.Contains(
            "Registry.ClassesRoot",
            shellNew,
            StringComparison.Ordinal);

        string surface = ReadRepositoryFile(
            "src/DeskBox/Controls/WidgetContents/" +
            "FileSurfaceContent.SelectionAndMenus.cs");
        Assert.Contains(
            "T(\"Widget.OpenWith\")",
            surface,
            StringComparison.Ordinal);
        Assert.Contains(
            "T(\"Widget.OpenWith.ChooseApp\")",
            surface,
            StringComparison.Ordinal);
    }

    [Fact]
    public void SearchResultsMenu_KeepsRunAsAdministratorEntry()
    {
        string searchWindow = ReadRepositoryFile(
            "src/DeskBox/Views/SearchPopupWindow.xaml.cs");

        Assert.Contains(
            "ElevatedFileLauncher.CanRunAsAdministrator(item.DetailPath",
            searchWindow,
            StringComparison.Ordinal);
        Assert.Contains(
            "Widget.RunAsAdministrator",
            searchWindow,
            StringComparison.Ordinal);
    }

    [Fact]
    public void Localization_NewKeysPresent_RetiredKeyGone_AllLanguages()
    {
        string stringsDir = TestPaths.FromRepository("src/DeskBox/Strings");
        string[] files = Directory.GetFiles(stringsDir, "*.json");
        Assert.True(files.Length >= 12, "expected the full language set");

        string[] newKeys =
        [
            "Widget.OpenWith",
            "Widget.OpenWith.ChooseApp",
            "Widget.ExtractAll",
            "Widget.CompressToZip",
            "Widget.New",
            "Widget.View",
            "Widget.SortBy",
            "Widget.NewFileName",
            "Widget.Zip.CompressFailed",
            "Widget.Zip.ExtractFailed",
        ];

        foreach (string file in files)
        {
            string text = File.ReadAllText(file);
            foreach (string key in newKeys)
            {
                Assert.Contains($"\"{key}\":", text, StringComparison.Ordinal);
            }

            Assert.DoesNotContain(
                "\"Widget.ViewAndSort\":",
                text,
                StringComparison.Ordinal);
        }
    }

    private static string ReadRepositoryFile(string relativePath) =>
        File.ReadAllText(TestPaths.FromRepository(relativePath));
}
