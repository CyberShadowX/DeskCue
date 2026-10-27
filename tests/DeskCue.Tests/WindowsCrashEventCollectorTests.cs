using System.Text.Json;
using DeskCue.Services;

namespace DeskCue.Tests;

public sealed class WindowsCrashEventCollectorTests
{
    [Theory]
    [InlineData("C:\\Users\\someone\\AppData\\Local\\DeskCue\\DeskCue.exe")]
    [InlineData("C:\\Windows\\explorer.exe")]
    [InlineData("DeskCue.exe")]
    [InlineData("EXPLORER.EXE")]
    [InlineData("\"C:\\Program Files\\DeskCue\\DeskCue.exe\"")]
    public void FilterPolicy_IncludesMonitoredImages(string value)
    {
        Assert.True(WindowsCrashEventFilterPolicy.ShouldInclude(
            new Dictionary<string, string> { ["AppPath"] = value }));
    }

    [Theory]
    [InlineData("C:\\Games\\MyDeskCue.exe")]
    [InlineData("C:\\Windows\\System32\\notepad.exe")]
    [InlineData("explorer")]
    [InlineData("")]
    [InlineData("C:\\Users\\someone\\Desktop\\explorer.exe.bak")]
    public void FilterPolicy_ExcludesEverythingElse(string value)
    {
        Assert.False(WindowsCrashEventFilterPolicy.ShouldInclude(
            new Dictionary<string, string> { ["AppPath"] = value }));
    }

    [Fact]
    public void ParseEvents_ExtractsCrashMetadataAndFiltersUnrelatedApps()
    {
        string xml = """
            <Events>
              <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
                <System>
                  <Provider Name="Application Error"/>
                  <EventID Qualifiers="0">1000</EventID>
                  <TimeCreated SystemTime="2026-10-13T13:51:30.500000000Z"/>
                </System>
                <EventData>
                  <Data Name="AppName">DeskCue.exe</Data>
                  <Data Name="AppPath">C:\Users\someone\AppData\Local\DeskCue\DeskCue.exe</Data>
                  <Data Name="ExceptionCode">0xc0000409</Data>
                  <Data Name="FaultingModule">deskcue_native.dll</Data>
                </EventData>
              </Event>
              <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
                <System>
                  <Provider Name="Windows Error Reporting"/>
                  <EventID>1001</EventID>
                  <TimeCreated SystemTime="2026-10-13T13:52:10.000000000Z"/>
                </System>
                <EventData>
                  <Data Name="AppPath">C:\Windows\explorer.exe</Data>
                  <Data Name="FaultingModule">thirdparty.shell.dll</Data>
                </EventData>
              </Event>
              <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
                <System>
                  <Provider Name="Application Error"/>
                  <EventID>1000</EventID>
                  <TimeCreated SystemTime="2026-10-13T13:53:00.000000000Z"/>
                </System>
                <EventData>
                  <Data Name="AppName">SomeOtherApp.exe</Data>
                </EventData>
              </Event>
            </Events>
            """;

        IReadOnlyList<WindowsCrashEventEntry> events = WindowsCrashEventCollector.ParseEvents(
            xml,
            DeskCueDiagnosticsBundleService.SanitizeDiagnosticsValue);

        Assert.Equal(2, events.Count);
        WindowsCrashEventEntry deskCue = events[0];
        Assert.Equal("Application Error", deskCue.Provider);
        Assert.Equal(1000, deskCue.EventId);
        Assert.Equal(
            new DateTimeOffset(2026, 10, 13, 13, 51, 30, 500, TimeSpan.Zero),
            deskCue.TimeCreatedUtc);
        Assert.Equal("<PATH>\\DeskCue.exe", deskCue.Properties["AppPath"]);
        Assert.Equal("0xc0000409", deskCue.Properties["ExceptionCode"]);

        WindowsCrashEventEntry explorer = events[1];
        Assert.Equal("Windows Error Reporting", explorer.Provider);
        Assert.Equal("thirdparty.shell.dll", explorer.Properties["FaultingModule"]);
    }

    [Fact]
    public async Task CollectAsync_ReportsUnavailableWhenQueryFails()
    {
        var collector = new WindowsCrashEventCollector(
            () => throw new InvalidOperationException("wevtutil missing"));

        WindowsCrashEventReport report = await collector.CollectAsync(
            DeskCueDiagnosticsBundleService.SanitizeDiagnosticsValue);

        Assert.Equal("unavailable", report.Status);
        Assert.Empty(report.Events);
    }

    [Fact]
    public async Task CollectAsync_CollectsThroughTestSeam()
    {
        string xml = """
            <Events>
              <Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
                <System>
                  <Provider Name="Application Error"/>
                  <EventID>1000</EventID>
                  <TimeCreated SystemTime="2026-10-13T21:51:32.000000000Z"/>
                </System>
                <EventData>
                  <Data Name="AppPath">C:\Users\someone\AppData\Local\DeskCue\DeskCue.exe</Data>
                  <Data Name="AppName">DeskCue.exe</Data>
                </EventData>
              </Event>
            </Events>
            """;
        var collector = new WindowsCrashEventCollector(() => Task.FromResult(xml));

        WindowsCrashEventReport report = await collector.CollectAsync(
            DeskCueDiagnosticsBundleService.SanitizeDiagnosticsValue);

        Assert.Equal("ok", report.Status);
        WindowsCrashEventEntry entry = Assert.Single(report.Events);
        Assert.Equal("DeskCue.exe", entry.Properties["AppName"]);
    }

    [Fact]
    public void SerializeReport_UsesCamelCaseAndIndentedJson()
    {
        var report = new WindowsCrashEventReport(
            WindowsCrashEventCollector.SchemaVersion,
            "ok",
            DateTimeOffset.UtcNow,
            []);

        string json = WindowsCrashEventCollector.SerializeReport(report);

        Assert.Contains("\"schemaVersion\"", json);
        Assert.Contains("\"windowStartUtc\"", json);
        Assert.NotNull(JsonDocument.Parse(json));
    }
}
