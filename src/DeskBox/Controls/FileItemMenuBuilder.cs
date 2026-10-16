using DeskBox.Models;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Controls.Primitives;
using Microsoft.UI.Xaml.Input;

namespace DeskBox.Controls;

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
    Func<WidgetItem, FlyoutBase, MenuFlyoutSubItem?>? CreateOpenWithSubmenu = null,
    Func<WidgetItem, bool>? CanExtractArchive = null,
    Func<WidgetItem, Task>? ExtractArchiveAsync = null,
    Func<IReadOnlyList<WidgetItem>, bool>? CanCompressSelection = null,
    Func<IReadOnlyList<WidgetItem>, Task>? CompressSelectionAsync = null);

/// <summary>
/// Builds the item context menus in the Windows 11 shape: a compact icon
/// strip on top (cut / copy / rename / delete) with the text rows below
/// (open family, archive actions, host-unique actions, properties, and the
/// full system menu escape hatch last). Implemented with CommandBarFlyout;
/// submenu rows ride in AppBarElementContainer, the documented way to host
/// MenuFlyoutItem-based submenus in the secondary command list.
/// </summary>
public static class FileItemMenuBuilder
{
    public static CommandBarFlyout CreateItemFlyout(
        WidgetItem item,
        FileItemMenuActions actions)
    {
        var flyout = new CommandBarFlyout();

        AddClipboardStrip(flyout, actions, item, includeRename: true);
        AddDeleteStripButton(flyout, actions);

        AddOpenRow(flyout, item, actions);
        AddOpenWithRow(flyout, item, actions);

        if (actions.CanRunAsAdministrator?.Invoke(item) == true &&
            actions.RunAsAdministratorAsync is not null)
        {
            flyout.SecondaryCommands.Add(CreateRowButton(
                flyout,
                actions,
                "Widget.RunAsAdministrator",
                "\uE7EF",
                null,
                async () => await actions.RunAsAdministratorAsync!(item)));
        }

        if (actions.CanExtractArchive?.Invoke(item) == true &&
            actions.ExtractArchiveAsync is not null)
        {
            flyout.SecondaryCommands.Add(CreateRowButton(
                flyout,
                actions,
                "Widget.ExtractAll",
                "\uE979",
                null,
                async () => await actions.ExtractArchiveAsync!(item)));
        }

        flyout.SecondaryCommands.Add(new AppBarSeparator());

        AddCompressToZipRow(flyout, actions);

        flyout.SecondaryCommands.Add(CreateRowButton(
            flyout,
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
            flyout.SecondaryCommands.Add(new AppBarSeparator());
            flyout.SecondaryCommands.Add(CreateRowButton(
                flyout,
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
            flyout.SecondaryCommands.Add(CreateRowButton(
                flyout,
                actions,
                "Widget.MoveBackToDesktop",
                "\uE74A",
                null,
                async () => await actions.MoveItemsBackToDesktopAsync(
                    actions.GetSelectedItems())));
        }

        flyout.SecondaryCommands.Add(new AppBarSeparator());

        flyout.SecondaryCommands.Add(CreateRowButton(
            flyout,
            actions,
            "Widget.ShowInExplorer",
            "\uE838",
            null,
            () =>
            {
                actions.ShowInExplorer(item);
                return Task.CompletedTask;
            }));

        flyout.SecondaryCommands.Add(CreateRowButton(
            flyout,
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

    public static CommandBarFlyout CreateMultiSelectionFlyout(
        FileItemMenuActions actions)
    {
        var flyout = new CommandBarFlyout();

        AddClipboardStrip(flyout, actions, null, includeRename: false);
        AddDeleteStripButton(flyout, actions);

        flyout.SecondaryCommands.Add(CreateRowButton(
            flyout,
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

        AddCompressToZipRow(flyout, actions);

        flyout.SecondaryCommands.Add(new AppBarSeparator());

        flyout.SecondaryCommands.Add(CreateRowButton(
            flyout,
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
            flyout.SecondaryCommands.Add(CreateRowButton(
                flyout,
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
            flyout.SecondaryCommands.Add(CreateRowButton(
                flyout,
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
    /// The icon strip: cut / copy / rename, matching the Windows 11 command
    /// order (cut, copy, rename, share, delete — share has no grid
    /// equivalent). Rename is single-selection only.
    /// </summary>
    private static void AddClipboardStrip(
        CommandBarFlyout flyout,
        FileItemMenuActions actions,
        WidgetItem? renameTarget,
        bool includeRename)
    {
        flyout.PrimaryCommands.Add(CreateStripButton(
            flyout,
            actions,
            "Common.Cut",
            "\uE8C6",
            "Ctrl+X",
            async () => await actions.CopySelectionToClipboardAsync(true)));

        flyout.PrimaryCommands.Add(CreateStripButton(
            flyout,
            actions,
            "Common.Copy",
            "\uE8C8",
            "Ctrl+C",
            async () => await actions.CopySelectionToClipboardAsync(false)));

        if (includeRename && renameTarget is not null)
        {
            flyout.PrimaryCommands.Add(CreateStripButton(
                flyout,
                actions,
                "Common.Rename",
                "\uE8AC",
                "F2",
                async () => await actions.RenameItemAsync(renameTarget)));
        }
    }

    private static void AddDeleteStripButton(
        CommandBarFlyout flyout,
        FileItemMenuActions actions)
    {
        flyout.PrimaryCommands.Add(CreateStripButton(
            flyout,
            actions,
            "Widget.MoveToRecycleBin",
            "\uE74D",
            "Delete",
            async () => await actions.DeleteItemsAsync(
                actions.GetSelectedItems())));
    }

    private static void AddOpenRow(
        CommandBarFlyout flyout,
        WidgetItem item,
        FileItemMenuActions actions)
    {
        flyout.SecondaryCommands.Add(CreateRowButton(
            flyout,
            actions,
            "Widget.Open",
            "\uE8E5",
            "Enter",
            async () => await actions.OpenItemAsync(item)));
    }

    private static void AddOpenWithRow(
        CommandBarFlyout flyout,
        WidgetItem item,
        FileItemMenuActions actions)
    {
        if (actions.CreateOpenWithSubmenu is null)
        {
            return;
        }

        MenuFlyoutSubItem? submenu =
            actions.CreateOpenWithSubmenu(item, flyout);
        if (submenu is not null)
        {
            flyout.SecondaryCommands.Add(
                new AppBarElementContainer { Content = submenu });
        }
    }

    private static void AddCompressToZipRow(
        CommandBarFlyout flyout,
        FileItemMenuActions actions)
    {
        if (actions.CanCompressSelection?.Invoke(
                actions.GetSelectedItems()) != true ||
            actions.CompressSelectionAsync is null)
        {
            return;
        }

        flyout.SecondaryCommands.Add(CreateRowButton(
            flyout,
            actions,
            "Widget.CompressToZip",
            "\uE979",
            null,
            async () => await actions.CompressSelectionAsync(
                actions.GetSelectedItems())));
    }

    private static void AddShowMoreOptionsRow(
        CommandBarFlyout flyout,
        WidgetItem item,
        FileItemMenuActions actions)
    {
        if (actions.ShowSystemContextMenuAsync is null)
        {
            return;
        }

        flyout.SecondaryCommands.Add(CreateRowButton(
            flyout,
            actions,
            "Widget.MoreSystemOperations",
            "\uE712",
            null,
            async () => await actions.ShowSystemContextMenuAsync(item)));
    }

    private static AppBarButton CreateStripButton(
        CommandBarFlyout flyout,
        FileItemMenuActions actions,
        string localizationKey,
        string glyph,
        string? acceleratorText,
        Func<Task> onClick)
    {
        AppBarButton button = CreateAppBarButton(
            flyout,
            actions,
            localizationKey,
            glyph,
            acceleratorText,
            onClick);
        // The strip renders icon-only, like the Windows 11 menu; the label
        // doubles as the tooltip.
        ToolTipService.SetToolTip(
            button,
            string.IsNullOrEmpty(acceleratorText)
                ? actions.Localize(localizationKey)
                : $"{actions.Localize(localizationKey)} ({acceleratorText})");
        return button;
    }

    private static AppBarButton CreateRowButton(
        CommandBarFlyout flyout,
        FileItemMenuActions actions,
        string localizationKey,
        string glyph,
        string? acceleratorText,
        Func<Task> onClick) =>
        CreateAppBarButton(
            flyout,
            actions,
            localizationKey,
            glyph,
            acceleratorText,
            onClick);

    private static AppBarButton CreateAppBarButton(
        CommandBarFlyout flyout,
        FileItemMenuActions actions,
        string localizationKey,
        string glyph,
        string? acceleratorText,
        Func<Task> onClick)
    {
        var button = new AppBarButton
        {
            Label = actions.Localize(localizationKey),
            Icon = new FontIcon { Glyph = glyph }
        };
        if (!string.IsNullOrEmpty(acceleratorText))
        {
            button.KeyboardAcceleratorTextOverride = acceleratorText;
        }

        button.Click += async (_, _) =>
        {
            // Strip buttons keep the flyout open by default; the Windows 11
            // menu closes on every command, so hide explicitly (harmless
            // for secondary rows, which already close).
            flyout.Hide();
            await onClick();
        };
        return button;
    }
}
