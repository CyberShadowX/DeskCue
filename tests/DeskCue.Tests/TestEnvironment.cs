using System.Runtime.CompilerServices;
using DeskCue.Services;

namespace DeskCue.Tests;

/// <summary>
/// Isolate process-wide application paths before services or App capture them,
/// including ordinary Release hosts which do not accept a development root.
/// </summary>
internal static class TestEnvironment
{
    internal static string ApplicationRoot { get; } = Path.Combine(
        TestPaths.FromRepository(".artifacts/test-data"),
        $"application-{Environment.ProcessId}-{Guid.NewGuid():N}", "root");

    [ModuleInitializer]
    internal static void Initialize()
    {
        DeskCueDataPathService.InitializeForTests(ApplicationRoot);
    }
}
