using DeskBox.Models;
using DeskBox.Services;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace DeskBox.Controls;

/// <summary>
/// The Open With app list handed to the menu builder. The entries ride in a
/// dedicated MenuFlyout opened beside the row; Dispose releases the live
/// Shell association handlers once the submenu round is over.
/// </summary>
public sealed record OpenWithMenuPayload(
    IReadOnlyList<MenuFlyoutItemBase> Items,
    Action Dispose);

/// <summary>
/// Host operations used by the shared file-item context menus.
/// The menu shape lives here; each surface only supplies its host-specific
/// actions and selection state.
/// </summary>
public sealed record FileItemMenuActions(
    Func<string, string, MenuFlyoutItem> CreateMenuItem,
    Func<string, string> Localize,
    Func<WidgetItem, Task> OpenItemAsync,
    Func<bool, Task> CopySelectionToClipboardAsync,
    Func<WidgetItem, Task> RenameItemAsync,
    Action CopySelectedPathsToClipboard,
    Action<WidgetItem> ShowInExplorer,
    Action<WidgetItem> ShowProperties,
    Func<bool> CanMoveItemsBackToDesktop,
    Func<IReadOnlyList<WidgetItem>, Task> MoveItemsBackToDesktopAsync,
    Func<IReadOnlyList<WidgetItem>, Task> DeleteItemsAsync,
    Func<IReadOnlyList<WidgetItem>> GetSelectedItems,
    bool CanCreateManualStack,
    Action<IReadOnlyList<WidgetItem>> CreateManualStack,
    Func<WidgetItem, bool> CanRemoveFromStack,
    Action<WidgetItem> RemoveFromStack,
    Action ClearSelection,
    Func<WidgetItem, Task>? ShowSystemContextMenuAsync = null,
    Func<WidgetItem, bool>? CanRunAsAdministrator = null,
    Func<WidgetItem, Task>? RunAsAdministratorAsync = null,
    Func<WidgetItem, OpenWithMenuPayload?>? GetOpenWithMenuItems = null,
    Func<WidgetItem, bool>? CanExtractArchive = null,
    Func<WidgetItem, Task>? ExtractArchiveAsync = null,
    Func<IReadOnlyList<WidgetItem>, bool>? CanCompressSelection = null,
    Func<IReadOnlyList<WidgetItem>, ArchiveCompressionFormat, Task>? CompressSelectionAsync = null);

/// <summary>
/// Builds the item context menus as a single-column MenuFlyout — one popup
/// window with the platform backdrop. The retired strip-plus-rows flyout
/// shape opened as two separate HWNDs and the row window had
/// no backdrop to show a material through (five failed rounds, see
/// artifacts/context-menu-enhancement-20261015); MenuFlyout restores the
/// material and the native submenu/hover/entrance behaviors, matching the
/// Windows 11 classic column (cut / copy / rename / delete ride as icon
/// rows in the Windows 11 command order).
/// </summary>
public static class FileItemMenuBuilder
{
    public static MenuFlyout CreateItemFlyout(
        WidgetItem item,
        FileItemMenuActions actions)
    {
        var flyout = CreateMenu();

        AddOpenRow(flyout, item, actions);
        AddOpenWithRow(flyout, item, actions);

        if (actions.CanRunAsAdministrator?.Invoke(item) == true &&
            actions.RunAsAdministratorAsync is not null)
        {
            flyout.Items.Add(CreateRow(
                actions,
                "Widget.RunAsAdministrator",
                "\uE7EF",
                null,
                async () => await actions.RunAsAdministratorAsync!(item)));
        }

        if (actions.CanExtractArchive?.Invoke(item) == true &&
            actions.ExtractArchiveAsync is not null)
        {
            flyout.Items.Add(CreateRow(
                actions,
                "Widget.ExtractAll",
                "\uE7F8",
                null,
                async () => await actions.ExtractArchiveAsync!(item)));
        }

        flyout.Items.Add(new MenuFlyoutSeparator());

        AddClipboardRows(flyout, actions, item, includeRename: true);
        AddDeleteRow(flyout, actions);

        flyout.Items.Add(new MenuFlyoutSeparator());

        AddCompressToZipRow(flyout, actions);

        flyout.Items.Add(CreateRow(
            actions,
            "Widget.CopyPath",
            "\uE8C8",
            "Ctrl+Shift+C",
            () =>
            {
                actions.CopySelectedPathsToClipboard();
                return Task.CompletedTask;
            }));

        if (actions.CanRemoveFromStack(item))
        {
            flyout.Items.Add(new MenuFlyoutSeparator());
            flyout.Items.Add(CreateRow(
                actions,
                "Widget.Stack.RemoveItem",
                "\uE8FB",
                null,
                () =>
                {
                    actions.RemoveFromStack(item);
                    return Task.CompletedTask;
                }));
        }

        if (actions.CanMoveItemsBackToDesktop())
        {
            flyout.Items.Add(CreateRow(
                actions,
                "Widget.MoveBackToDesktop",
                "\uE74A",
                null,
                async () => await actions.MoveItemsBackToDesktopAsync(
                    actions.GetSelectedItems())));
        }

        flyout.Items.Add(new MenuFlyoutSeparator());

        flyout.Items.Add(CreateRow(
            actions,
            "Widget.ShowInExplorer",
            "\uE838",
            null,
            () =>
            {
                actions.ShowInExplorer(item);
                return Task.CompletedTask;
            }));

        flyout.Items.Add(CreateRow(
            actions,
            "Common.Properties",
            "\uE946",
            "Alt+Enter",
            () =>
            {
                actions.ShowProperties(item);
                return Task.CompletedTask;
            }));

        AddShowMoreOptionsRow(flyout, item, actions);

        return flyout;
    }

    public static MenuFlyout CreateMultiSelectionFlyout(
        FileItemMenuActions actions)
    {
        var flyout = CreateMenu();

        flyout.Items.Add(CreateRow(
            actions,
            "Widget.Open",
            "\uE8E5",
            null,
            async () =>
            {
                foreach (WidgetItem item in actions.GetSelectedItems())
                {
                    await actions.OpenItemAsync(item);
                }
            }));

        flyout.Items.Add(new MenuFlyoutSeparator());

        AddClipboardRows(flyout, actions, null, includeRename: false);
        AddDeleteRow(flyout, actions);

        flyout.Items.Add(new MenuFlyoutSeparator());

        AddCompressToZipRow(flyout, actions);

        flyout.Items.Add(CreateRow(
            actions,
            "Widget.CopyPath",
            "\uE8C8",
            "Ctrl+Shift+C",
            () =>
            {
                actions.CopySelectedPathsToClipboard();
                return Task.CompletedTask;
            }));

        if (actions.CanCreateManualStack)
        {
            flyout.Items.Add(CreateRow(
                actions,
                "Widget.Stack.Start",
                "\uE8B7",
                null,
                () =>
                {
                    actions.CreateManualStack(actions.GetSelectedItems());
                    actions.ClearSelection();
                    return Task.CompletedTask;
                }));
        }

        if (actions.CanMoveItemsBackToDesktop())
        {
            flyout.Items.Add(CreateRow(
                actions,
                "Widget.MoveBackToDesktop",
                "\uE74A",
                null,
                async () => await actions.MoveItemsBackToDesktopAsync(
                    actions.GetSelectedItems())));
        }

        return flyout;
    }

    /// <summary>
    /// Cut / copy / rename as icon rows, matching the Windows 11 command
    /// order (cut, copy, rename, delete). Rename is single-selection only.
    /// </summary>
    private static void AddClipboardRows(
        MenuFlyout flyout,
        FileItemMenuActions actions,
        WidgetItem? renameTarget,
        bool includeRename)
    {
        flyout.Items.Add(CreateRow(
            actions,
            "Common.Cut",
            "\uE8C6",
            "Ctrl+X",
            async () => await actions.CopySelectionToClipboardAsync(true)));

        flyout.Items.Add(CreateRow(
            actions,
            "Common.Copy",
            "\uE8C8",
            "Ctrl+C",
            async () => await actions.CopySelectionToClipboardAsync(false)));

        if (includeRename && renameTarget is not null)
        {
            flyout.Items.Add(CreateRow(
                actions,
                "Common.Rename",
                "\uE8AC",
                "F2",
                async () => await actions.RenameItemAsync(renameTarget)));
        }
    }

    private static void AddDeleteRow(
        MenuFlyout flyout,
        FileItemMenuActions actions)
    {
        flyout.Items.Add(CreateRow(
            actions,
            "Widget.MoveToRecycleBin",
            "\uE74D",
            "Delete",
            async () => await actions.DeleteItemsAsync(
                actions.GetSelectedItems())));
    }

    private static void AddOpenRow(
        MenuFlyout flyout,
        WidgetItem item,
        FileItemMenuActions actions)
    {
        flyout.Items.Add(CreateRow(
            actions,
            "Widget.Open",
            "\uE8E5",
            "Enter",
            async () => await actions.OpenItemAsync(item)));
    }

    private static void AddOpenWithRow(
        MenuFlyout flyout,
        WidgetItem item,
        FileItemMenuActions actions)
    {
        if (actions.GetOpenWithMenuItems is null)
        {
            return;
        }

        OpenWithMenuPayload? payload;
        try
        {
            payload = actions.GetOpenWithMenuItems(item);
        }
        catch
        {
            payload = null;
        }

        if (payload is null || payload.Items.Count == 0)
        {
            return;
        }

        AddSubmenuRow(
            flyout,
            actions,
            "Widget.OpenWith",
            "\uE8AF",
            payload.Items,
            payload.Dispose);
    }

    /// <summary>
    /// A row with a native MenuFlyoutSubItem submenu: the platform draws the
    /// chevron, opens on hover with its own timing, and dismisses the whole
    /// menu round on selection. The retired two-window flyout shape needed
    /// a container-wrapper hack, a chevron resource hack, and a manual
    /// hover debounce here — all gone with the migration.
    /// </summary>
    private static void AddSubmenuRow(
        MenuFlyout flyout,
        FileItemMenuActions actions,
        string localizationKey,
        string glyph,
        IReadOnlyList<MenuFlyoutItemBase> submenuItems,
        Action? submenuClosed = null)
    {
        var row = new MenuFlyoutSubItem
        {
            Text = actions.Localize(localizationKey),
            Icon = new FontIcon { Glyph = glyph }
        };

        foreach (MenuFlyoutItemBase entry in submenuItems)
        {
            row.Items.Add(entry);
        }

        if (submenuClosed is not null)
        {
            flyout.Closed += (_, _) => submenuClosed();
        }

        flyout.Items.Add(row);
    }

    private static MenuFlyout CreateMenu() => new()
    {
        // Grid widgets are small windows; the default root-bounds
        // constraint shoves the menu far away when the item sits near the
        // widget edge. Like the native Shell menu, only the monitor bounds
        // should matter (flip at screen edges, glued to the click point).
        ShouldConstrainToRootBounds = false
    };

    private static void AddCompressToZipRow(
        MenuFlyout flyout,
        FileItemMenuActions actions)
    {
        if (actions.CanCompressSelection?.Invoke(
                actions.GetSelectedItems()) != true ||
            actions.CompressSelectionAsync is null)
        {
            return;
        }

        var zipItem = new MenuFlyoutItem
        {
            Text = actions.Localize("Widget.CompressTo.Zip"),
            Icon = new FontIcon { Glyph = "\uE7F8" }
        };
        zipItem.Click += async (_, _) =>
        {
            await actions.CompressSelectionAsync(
                actions.GetSelectedItems(),
                ArchiveCompressionFormat.Zip);
        };

        var tarItem = new MenuFlyoutItem
        {
            Text = actions.Localize("Widget.CompressTo.Tar"),
            Icon = new FontIcon { Glyph = "\uE7F8" }
        };
        tarItem.Click += async (_, _) =>
        {
            await actions.CompressSelectionAsync(
                actions.GetSelectedItems(),
                ArchiveCompressionFormat.Tar);
        };

        // 7z needs the LZMA SDK (no BCL writer) — registered as batch debt
        // pending a go; the native format dialog has no public API.
        AddSubmenuRow(
            flyout,
            actions,
            "Widget.CompressTo",
            "\uE7F8",
            [zipItem, tarItem]);
    }

    private static void AddShowMoreOptionsRow(
        MenuFlyout flyout,
        WidgetItem item,
        FileItemMenuActions actions)
    {
        if (actions.ShowSystemContextMenuAsync is null)
        {
            return;
        }

        flyout.Items.Add(CreateRow(
            actions,
            "Widget.MoreSystemOperations",
            "\uE712",
            null,
            async () => await actions.ShowSystemContextMenuAsync(item)));
    }

    private static MenuFlyoutItem CreateRow(
        FileItemMenuActions actions,
        string localizationKey,
        string glyph,
        string? acceleratorText,
        Func<Task> onClick)
    {
        var row = new MenuFlyoutItem
        {
            Text = actions.Localize(localizationKey),
            Icon = new FontIcon { Glyph = glyph }
        };
        if (!string.IsNullOrEmpty(acceleratorText))
        {
            row.KeyboardAcceleratorTextOverride = acceleratorText;
        }

        // MenuFlyout closes itself on selection; the retired strip-plus-rows
        // rows needed an explicit Hide on every command.
        row.Click += async (_, _) => await onClick();
        return row;
    }
}
