namespace DeskCue.Models;

/// <summary>
/// Describes how persisted user text should be interpreted. Plain text is the
/// zero value so records written by older DeskCue versions remain lossless.
/// </summary>
public enum TextContentFormat
{
    PlainText = 0,
    Markdown = 1
}
