namespace DeskCue.Contracts;

/// <summary>Optional content measurement; host retains geometry and persistence ownership.</summary>
public interface IWidgetPreferredHeightContent
{
    event EventHandler? PreferredHeightInvalidated;
    bool TryMeasurePreferredContentHeight(double width, double maxHeight, out double height);
}
