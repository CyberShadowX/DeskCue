using System.ComponentModel;
using DeskCue.ViewModels;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.Foundation;

namespace DeskCue.Controls.WidgetContents;

public sealed partial class TodoWidgetContent
{
    internal event EventHandler? PreferredHeightInvalidated;
    private FrameworkElement? _heightMeasurementRow;
    private readonly HashSet<TodoItemViewModel> _heightObservedItems = [];

    private void InvalidatePreferredHeight() => PreferredHeightInvalidated?.Invoke(this, EventArgs.Empty);

    private void RefreshHeightSubscriptions(bool detachOnly = false)
    {
        foreach (var item in _heightObservedItems)
            item.PropertyChanged -= HeightItem_PropertyChanged;
        _heightObservedItems.Clear();
        if (!detachOnly && IsLoaded && ViewModel is not null)
            foreach (var item in ViewModel.VisibleItems)
                if (_heightObservedItems.Add(item)) item.PropertyChanged += HeightItem_PropertyChanged;
        InvalidatePreferredHeight();
    }

    private void HeightItem_PropertyChanged(object? sender, PropertyChangedEventArgs e) => InvalidatePreferredHeight();

    internal bool TryMeasurePreferredContentHeight(double width, double maxHeight, out double height)
    {
        height = 0;
        if (!IsLoaded || ViewModel is null || ViewModel.IsDetailPageOpen ||
            _isClosingDetail || _isInteractiveResizeActive || _isResponsiveLayoutTransitionActive ||
            _draggedTodoItemId is not null || _selectionPointerPressed ||
            TodoInlineEditor.Visibility == Visibility.Visible || CustomDueDateOverlay.Visibility == Visibility.Visible ||
            !double.IsFinite(width) || width <= 0 || !double.IsFinite(maxHeight) || maxHeight <= 0)
            return false;

        // The live panel stays virtualized. Only this single connected row is measured unbounded vertically.
        if (_heightMeasurementRow is null)
        {
            _heightMeasurementRow = (FrameworkElement)TodoListView.ItemTemplate.LoadContent();
            _heightMeasurementRow.DataContextChanged -= TodoItem_DataContextChanged;
            _heightMeasurementRow.IsHitTestVisible = false;
            HeightMeasurementCanvas.Children.Add(_heightMeasurementRow);
        }
        _heightMeasurementRow.Tag = ViewModel;
        double masterWidth = ListArea.ActualWidth;
        if (masterWidth <= 0) return false;
        // Visible scrollbar reserves a stable gutter in the live list. The panel's width
        // is the actual finite width offered to each item, independent of item realization.
        double rowWidth = TodoListView.ItemsPanelRoot?.ActualWidth ?? 0;
        if (rowWidth <= 0) return false;
        double Measure(FrameworkElement element, double availableWidth)
        {
            element.Measure(new Size(availableWidth, double.PositiveInfinity));
            return element.DesiredSize.Height;
        }
        double fixedHeight = RootGrid.Padding.Top + RootGrid.Padding.Bottom + 2 * RootGrid.RowSpacing
            + Measure(ListHeaderArea, masterWidth) + Measure(ListFooterArea, masterWidth)
            + TodoListView.Padding.Top + TodoListView.Padding.Bottom;
        double rowsHeight = TodoListView.Header is FrameworkElement header ? Measure(header, rowWidth) : 0;
        if (ViewModel.VisibleItems.Count == 0)
            rowsHeight += Measure(TodoEmptyState, masterWidth);
        _heightMeasurementRow.Width = rowWidth;
        try
        {
            foreach (var item in ViewModel.VisibleItems)
            {
                _heightMeasurementRow.DataContext = item;
                _heightMeasurementRow.InvalidateMeasure();
                rowsHeight += Measure(_heightMeasurementRow, rowWidth);
                if (fixedHeight + rowsHeight >= maxHeight) break;
            }
        }
        finally { _heightMeasurementRow.DataContext = null; }
        height = Math.Min(maxHeight, fixedHeight + rowsHeight);
        return true;
    }
}
