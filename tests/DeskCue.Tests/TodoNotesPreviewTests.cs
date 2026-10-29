using DeskCue.Models;
using DeskCue.ViewModels;
using Microsoft.UI.Xaml;

namespace DeskCue.Tests;

public sealed class TodoNotesPreviewTests
{
    [Fact]
    public void Preview_UsesPlainTextAndPreservesRawMarkdown()
    {
        const string notes = "  # Planning\n\n**Review** [guide](https://example.com)  \n";
        var item = new TodoItemViewModel(new TodoItem { Text = "Review", Notes = notes });

        Assert.Equal("Planning" + Environment.NewLine + "Review guide", Preview(item));
        Assert.Equal(Visibility.Visible, PreviewVisibility(item));
        Assert.Equal(notes, item.Notes);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData(" \n\t ")]
    public void EmptyPreview_OccupiesNoSpace(string? notes)
    {
        var item = new TodoItemViewModel(new TodoItem { Notes = notes! });
        Assert.True(string.IsNullOrWhiteSpace(Preview(item)));
        Assert.Equal(Visibility.Collapsed, PreviewVisibility(item));
    }

    [Fact]
    public void Refresh_UpdatesCachedPreviewAndNotifiesBindingsIncludingRollback()
    {
        var model = new TodoItem { Notes = "**Original**" };
        var item = new TodoItemViewModel(model);
        var notifications = new List<string?>();
        item.PropertyChanged += (_, e) => notifications.Add(e.PropertyName);
        Assert.Equal("Original", Preview(item));
        model.Notes = "# Revised";
        Assert.Equal("Original", Preview(item));
        item.RefreshDetailProperties();
        Assert.Equal("Revised", Preview(item));
        Assert.Contains("NotesPreview", notifications);
        Assert.Contains("NotesPreviewVisibility", notifications);
        model.Notes = "**Original**";
        item.RefreshDetailProperties();
        Assert.Equal("Original", Preview(item));
    }

    // Reflection keeps the initial red run executable before the binding exists.
    private static string Preview(TodoItemViewModel item) =>
        Assert.IsType<string>(typeof(TodoItemViewModel).GetProperty("NotesPreview")?.GetValue(item));

    private static Visibility PreviewVisibility(TodoItemViewModel item) =>
        Assert.IsType<Visibility>(typeof(TodoItemViewModel).GetProperty("NotesPreviewVisibility")?.GetValue(item));
}
