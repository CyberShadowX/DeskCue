using System.Diagnostics;
using System.Reflection;
using System.Security.Cryptography;
using DeskCue.Contracts;
using DeskCue.Services;

namespace DeskCue.Tests;

public sealed class EverythingIntegrationTests
{
    [Theory]
    [InlineData("budget report", false, "\"budget report\"")]
    [InlineData("ext:pdf budget", true, "ext:pdf budget")]
    [InlineData("  notes  ", false, "\"notes\"")]
    public void ProviderQuery_IsLiteralUnlessAdvancedSyntaxIsEnabled(
        string query,
        bool advancedSyntax,
        string expected)
    {
        Assert.Equal(expected, EverythingSearchService.BuildProviderQuery(query, advancedSyntax));
    }

    [Theory]
    [InlineData("report.txt", "report.txt", 100)]
    [InlineData("report.txt", "report", 90)]
    [InlineData("report-final.txt", "report", 80)]
    [InlineData("annual-report.txt", "report", 50)]
    public void ProviderResultRelevance_PreservesDeskCueRanking(
        string fileName,
        string query,
        double expected)
    {
        Assert.Equal(expected, EverythingSearchService.ComputeRelevance(fileName, query));
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public void Dispose_LeavesSdkReusableAcrossProviderInstances(bool initializeBeforeDispose)
    {
        string root = Path.Combine(
            Path.GetTempPath(),
            "DeskCue-EverythingLifecycle-" + Guid.NewGuid().ToString("N"));
        try
        {
            var settings = new SettingsService(root);
            for (int iteration = 0; iteration < 3; iteration++)
            {
                var provider = new EverythingSearchService(settings);
                if (initializeBeforeDispose)
                {
                    AssertSdkReusable($"before-dispose-{iteration}");
                }

                provider.Dispose();
                provider.Dispose();

                using var nextProvider = new EverythingSearchService(settings);
                AssertSdkReusable($"next-provider-{iteration}");
            }
        }
        finally
        {
            EverythingNativeMethods.Reset();
            if (Directory.Exists(root))
            {
                Directory.Delete(root, recursive: true);
            }
        }
    }

    [Fact]
    public async Task Dispose_RejectsNewWorkWithoutMutatingConnectionState()
    {
        string root = Path.Combine(
            Path.GetTempPath(),
            "DeskCue-EverythingDisposed-" + Guid.NewGuid().ToString("N"));
        try
        {
            var settings = new SettingsService(root);
            settings.Settings.SearchEverythingExecutablePath = "keep.exe";
            var provider = new EverythingSearchService(settings);
            EverythingConnectionSnapshot before = provider.CurrentSnapshot;
            int changes = 0;
            provider.ConnectionChanged += _ => changes++;
            provider.Dispose();
            provider.Dispose();

            await Assert.ThrowsAsync<ObjectDisposedException>(
                () => provider.RefreshConnectionAsync(allowIpcProbe: false));
            await Assert.ThrowsAsync<ObjectDisposedException>(
                () => provider.UseAutomaticDetectionAsync());
            await Assert.ThrowsAsync<ObjectDisposedException>(
                () => provider.SetExecutablePathAsync("new.exe"));
            Assert.Same(SearchFileQueryPage.Empty,
                await provider.SearchPageAsync("unused", 0, 10));
            Assert.Equal("keep.exe", settings.Settings.SearchEverythingExecutablePath);
            Assert.Equal(before, provider.CurrentSnapshot);
            Assert.Equal(0, changes);
        }
        finally
        {
            if (Directory.Exists(root))
            {
                Directory.Delete(root, recursive: true);
            }
        }
    }

    [Fact]
    public async Task Dispose_DrainsInFlightWorkAndLeavesItsGateUsable()
    {
        string root = Path.Combine(
            Path.GetTempPath(),
            "DeskCue-EverythingDrain-" + Guid.NewGuid().ToString("N"));
        var provider = new EverythingSearchService(new SettingsService(root));
        const BindingFlags privateInstance = BindingFlags.Instance | BindingFlags.NonPublic;
        var gate = Assert.IsType<SemaphoreSlim>(typeof(EverythingSearchService)
            .GetField("_nativeGate", privateInstance)!.GetValue(provider));
        FieldInfo disposed = typeof(EverythingSearchService)
            .GetField("_isDisposed", privateInstance)!;
        await gate.WaitAsync();
        bool workOwnsGate = true;
        Task disposal = Task.Factory.StartNew(provider.Dispose, CancellationToken.None,
            TaskCreationOptions.LongRunning, TaskScheduler.Default);
        try
        {
            // Hold the same lease as an active native transaction. Observe that
            // Dispose has entered before checking that it waits for that work.
            var started = Stopwatch.StartNew();
            while (!(bool)disposed.GetValue(provider)!)
            {
                Assert.True(started.Elapsed < TimeSpan.FromSeconds(5), "Dispose did not start.");
                await Task.Delay(1);
            }

            Assert.NotSame(disposal, await Task.WhenAny(disposal, Task.Delay(100)));
            gate.Release();
            workOwnsGate = false;
            await disposal.WaitAsync(TimeSpan.FromSeconds(5));

            // Do not invalidate the gate: continuations from already-started
            // work may still acquire or release it after the drain completes.
            Assert.True(await gate.WaitAsync(TimeSpan.FromSeconds(1)));
            gate.Release();
        }
        finally
        {
            if (workOwnsGate)
            {
                gate.Release();
            }

            await disposal.WaitAsync(TimeSpan.FromSeconds(5));
            Directory.Delete(root, recursive: true);
        }
    }

    [Fact]
    public void LegacyCleanup_RemovesOnlyDeskCueOwnedIndexArtifacts()
    {
        string root = Path.Combine(
            Path.GetTempPath(),
            "DeskCue-LegacySearchCleanup-" + Guid.NewGuid().ToString("N"));
        string cache = Path.Combine(root, "cache");
        Directory.CreateDirectory(cache);
        string[] obsolete =
        [
            Path.Combine(cache, "search-index.json"),
            Path.Combine(cache, "search-index-v2.json.tmp"),
            Path.Combine(cache, "search-index-v2.json.roots")
        ];
        string retained = Path.Combine(cache, "search-history.json");
        try
        {
            foreach (string path in obsolete)
            {
                File.WriteAllText(path, "obsolete");
            }

            File.WriteAllText(retained, "keep");
            Assert.Equal(obsolete.Length, LegacySearchIndexCleanupService.TryCleanup(root));
            Assert.All(obsolete, path => Assert.False(File.Exists(path)));
            Assert.True(File.Exists(retained));
        }
        finally
        {
            if (Directory.Exists(root))
            {
                Directory.Delete(root, recursive: true);
            }
        }
    }

    [Fact]
    public void ProjectPackagesOfficialSdkForBothSupportedArchitectures()
    {
        string project = File.ReadAllText(TestPaths.FromRepository(
            "src/DeskCue/DeskCue.csproj"));
        string cargo = File.ReadAllText(TestPaths.FromRepository("native/Cargo.toml"));

        Assert.Contains("ThirdParty\\Everything\\Everything64.dll", project, StringComparison.Ordinal);
        Assert.Contains("ThirdParty\\Everything\\EverythingARM64.dll", project, StringComparison.Ordinal);
        Assert.Contains("<TargetPath>EverythingSdk.dll</TargetPath>", project, StringComparison.Ordinal);
        Assert.DoesNotContain("DeskCueSearchCore", project, StringComparison.Ordinal);
        Assert.DoesNotContain("deskcue-search-core", cargo, StringComparison.Ordinal);

        Assert.Equal(
            "81B5BE18126ACD2C2B913F8F4A821E476B18393CDD3DEBD03387C50AFD8DB88F",
            Hash("src/DeskCue/ThirdParty/Everything/Everything64.dll"));
        Assert.Equal(
            "8531EA393677DD8FD37BED7420AC93344CD458B9A1324BA65C4A75D024D61886",
            Hash("src/DeskCue/ThirdParty/Everything/EverythingARM64.dll"));
    }

    private static string Hash(string relativePath)
    {
        using FileStream stream = File.OpenRead(TestPaths.FromRepository(relativePath));
        return Convert.ToHexString(SHA256.HashData(stream));
    }

    private static void AssertSdkReusable(string search)
    {
        // Exercise the actual SDK's process state without contacting Everything.
        EverythingNativeMethods.Reset();
        EverythingNativeMethods.SetSearch(search);
        Assert.Equal(0u, EverythingNativeMethods.GetNumResults());
    }
}
