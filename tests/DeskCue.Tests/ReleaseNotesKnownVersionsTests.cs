using DeskCue.Services;
using Xunit;

namespace DeskCue.Tests;

/// <summary>
/// The release-notes window's version rail unions the published list with
/// each machine's notes cache, so every machine shows the same versions.
/// These pins keep the list strictly to versions that have a GitHub
/// release (their notes can resolve through the tag) and keep it ordered.
/// </summary>
public sealed class ReleaseNotesKnownVersionsTests
{
    [Fact]
    public void KnownReleaseVersions_AreNewestFirst()
    {
        var versions = ReleaseNotesService.KnownReleaseVersions;
        for (int i = 1; i < versions.Count; i++)
        {
            Version previous = Version.Parse(versions[i - 1]);
            Version current = Version.Parse(versions[i]);
            Assert.True(
                previous > current,
                $"{versions[i - 1]} must sort newer than {versions[i]}.");
        }
    }

    [Fact]
    public void KnownReleaseVersions_CoverCurrentAndPreviousRelease()
    {
        Assert.Contains("1.5.9", ReleaseNotesService.KnownReleaseVersions);
        Assert.Contains("1.5.8", ReleaseNotesService.KnownReleaseVersions);
        Assert.Contains("1.4.0", ReleaseNotesService.KnownReleaseVersions);
    }

    [Fact]
    public void KnownReleaseVersions_KeepPublishedDeskCueHistoryWithCurrentRelease()
    {
        var versions = ReleaseNotesService.KnownReleaseVersions;
        string current = AppUpdateService.GetCurrentAppVersion();

        Assert.Equal(current, versions[0]);
        Assert.Equal(
            ["1.5.9.7", "1.5.9.6", "1.5.9.5", "1.5.9.4", "1.5.9.3"],
            versions.Where(version => version is "1.5.9.7" or "1.5.9.6" or "1.5.9.5" or "1.5.9.4" or "1.5.9.3"));
    }

    [Fact]
    public void MergeKnownReleaseVersions_PreservesHistoryForFutureCurrentAndUpstreamRelease()
    {
        IReadOnlyList<string> versions = ReleaseNotesService.MergeKnownReleaseVersions(
            ["1.5.10", "1.5.10.1", "1.4.0", "1.5.10.1"]);

        Assert.Equal(
            ["1.5.10.1", "1.5.10", "1.5.9.7", "1.5.9.6", "1.5.9.5", "1.5.9.4", "1.5.9.3", "1.4.0"],
            versions);
    }

    [Fact]
    public void MergeKnownReleaseVersions_FutureRevisionRetainsForkHistoryWithoutCache()
    {
        IReadOnlyList<string> versions = ReleaseNotesService.MergeKnownReleaseVersions(
            ["1.5.9.8", "1.5.9", "1.5.9.8"]);

        Assert.Equal(
            ["1.5.9.8", "1.5.9.7", "1.5.9.6", "1.5.9.5", "1.5.9.4", "1.5.9.3", "1.5.9"],
            versions);
    }

    [Fact]
    public void MergeKnownReleaseVersions_CurrentRevisionIsDeduplicatedAgainstForkHistory()
    {
        IReadOnlyList<string> versions = ReleaseNotesService.MergeKnownReleaseVersions(
            ["1.5.9.7", "1.5.9", "1.5.9.7"]);

        Assert.Equal(
            ["1.5.9.7", "1.5.9.6", "1.5.9.5", "1.5.9.4", "1.5.9.3", "1.5.9"],
            versions);
    }

    [Fact]
    public void KnownReleaseVersions_NewestMatchesCurrentRelease()
    {
        // Appending the new version at release time is a manual step; this
        // pin turns a forgotten append into a red suite on the first build
        // of the next version instead of a silently missing rail entry on
        // every 1.5.9 machine.
        string current = AppUpdateService.GetCurrentAppVersion();
        Assert.NotEqual("0.0.0", current);
        Assert.Equal(current, ReleaseNotesService.KnownReleaseVersions[0]);
    }

    [Fact]
    public void KnownReleaseVersions_ExcludeVersionsWithoutAGitHubRelease()
    {
        // v1.4.4 was never released; v1.4.5 exists as a tag only, so its
        // release notes cannot resolve through the tag URL.
        Assert.DoesNotContain("1.4.4", ReleaseNotesService.KnownReleaseVersions);
        Assert.DoesNotContain("1.4.5", ReleaseNotesService.KnownReleaseVersions);
        Assert.DoesNotContain("1.4.5-rc1", ReleaseNotesService.KnownReleaseVersions);
    }
}
