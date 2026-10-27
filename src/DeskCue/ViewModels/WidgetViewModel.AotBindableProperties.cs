#if DESKCUE_NATIVE_AOT
namespace DeskCue.ViewModels;

// FileSurfaceContent keeps its established runtime Binding surface. Expose
// only the root and layout properties consumed by the real File Widget XAML.
[WinRT.GeneratedBindableCustomProperty([
    nameof(CurrentFolderDisplayName),
    nameof(CurrentFolderRelativePath),
    nameof(EmptyStateGlyph),
    nameof(EmptyStateTitle),
    nameof(FolderNavigationVisibility),
    nameof(IconCellHeight),
    nameof(IconCellWidth),
    nameof(IconContentSpacing),
    nameof(IconImageSize),
    nameof(IconLabelFontSize),
    nameof(IconLabelMaxLines),
    nameof(IconLabelMaxWidth),
    nameof(IconLabelVisibility),
    nameof(IconTileHeight),
    nameof(IconTileMargin),
    nameof(IconTileWidth),
    nameof(IconViewVisibility),
    nameof(IsLoading),
    nameof(ListIconSize),
    nameof(ListItemDetailFontSize),
    nameof(ListItemDetailVisibility),
    nameof(ListLabelFontSize),
    nameof(ListViewVisibility),
    nameof(LoadingVisibility),
    nameof(ShowFileItemPathTooltips),
    nameof(VisibleItems),
    nameof(RenderedItems)
], [])]
public partial class WidgetViewModel
{
}
#endif
