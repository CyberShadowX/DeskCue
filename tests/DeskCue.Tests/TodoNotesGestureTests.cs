using DeskCue.Controls;

namespace DeskCue.Tests;

public sealed class TodoNotesGestureTests
{
    [Fact]
    public void HyperlinkClick_BlocksFollowingHandledTextTapUntilNextPointerPress()
    {
        var gesture = new MarkdownReaderPointerGesture();
        gesture.BeginPointerGesture();
        Assert.True(gesture.CanBeginNotesEditing(false, false, false));

        // Native RichTextBlock raises Hyperlink.Click and then forwards its
        // handled tap with RichTextBlock as OriginalSource (not Hyperlink).
        gesture.RecordHyperlinkActivation();
        Assert.False(gesture.CanBeginNotesEditing(false, false, false));
        Assert.False(gesture.CanBeginNotesEditing(false, false, false));

        // A subsequent click in blank space must not inherit the activation.
        gesture.BeginPointerGesture();
        Assert.True(gesture.CanBeginNotesEditing(false, false, false));
    }

    [Fact]
    public void AttachmentActivation_IsVisibleToSubsequentCallbackAndTapObserver()
    {
        var gesture = new MarkdownReaderPointerGesture();
        gesture.BeginPointerGesture();
        bool attachmentCallbackObservedBlockedEdit = false;
        void OpenAttachment() => attachmentCallbackObservedBlockedEdit =
            !gesture.CanBeginNotesEditing(false, false, false);

        // CreateHyperlink installs the common marker before AppendLink adds
        // its attachment callback; rendering never resets pointer state.
        gesture.RecordHyperlinkActivation();
        OpenAttachment();
        Assert.True(attachmentCallbackObservedBlockedEdit);
        Assert.False(gesture.CanBeginNotesEditing(false, false, false));
    }

    [Fact]
    public void KeyboardLinkActivation_DoesNotPoisonNextPointerGesture()
    {
        var gesture = new MarkdownReaderPointerGesture();
        gesture.RecordHyperlinkActivation();
        gesture.BeginPointerGesture();
        Assert.True(gesture.CanBeginNotesEditing(false, false, false));
    }

    [Theory]
    [InlineData(false, false, false, true)]
    [InlineData(true, false, false, false)]
    [InlineData(false, true, false, false)]
    [InlineData(false, false, true, false)]
    [InlineData(true, true, true, false)]
    public void ClickEditing_LeavesSelectionDragAndInteractiveContentAlone(
        bool hasSelection, bool isInteractive, bool hasDragged, bool expected)
    {
        var gesture = new MarkdownReaderPointerGesture();
        gesture.BeginPointerGesture();
        Assert.Equal(expected, gesture.CanBeginNotesEditing(hasSelection, isInteractive, hasDragged));
    }
}
