using System.Reflection;
using DeskCue.Controls;

namespace DeskCue.Tests;

public sealed class TodoNotesGestureTests
{
    [Theory]
    [InlineData(false, false, false, true)]
    [InlineData(true, false, false, false)]
    [InlineData(false, true, false, false)]
    [InlineData(false, false, true, false)]
    [InlineData(true, true, true, false)]
    public void ClickEditing_LeavesSelectionDragAndInteractiveContentAlone(
        bool hasSelection, bool isInteractive, bool hasDragged, bool expected)
    {
        var method = typeof(MarkdownDocumentView).GetMethod("CanBeginNotesEditing",
            BindingFlags.Static | BindingFlags.NonPublic);
        Assert.NotNull(method);
        Assert.Equal(expected, method.Invoke(null, [hasSelection, isInteractive, hasDragged]));
    }
}
