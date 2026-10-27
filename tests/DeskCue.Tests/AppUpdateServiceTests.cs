using System.Net;
using System.Security.Cryptography;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using DeskCue.Models;
using DeskCue.Services;
using DeskCue.ViewModels;

namespace DeskCue.Tests;

public sealed class AppUpdateServiceTests : IDisposable
{
    private readonly string _tempRoot = Path.Combine(Path.GetTempPath(), "DeskCue.Tests", Guid.NewGuid().ToString("N"));

    private const string ManifestFixtureJson = """
        {
          "ScHeMaVeRsIoN": "1",
          "version": "1.2.2",
          "downloadUrl": "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.2/DeskCue_Setup_1.2.2_x64.exe",
          "manualDownloadUrl": "https://pan.quark.cn/s/version-specific",
          "sha256": "abc",
          "SiZe": "1234",
          "arm64DownloadUrl": "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.2/DeskCue_Setup_1.2.2_arm64.exe",
          "arm64Sha256": "abc",
          "arm64Size": "1234",
          "summary": { "zh-CN": "修复多屏定位" },
          "futureManifestField": { "ignored": true }
        }
        """;

    [Theory]
    [InlineData("x64", "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.2/DeskCue_Setup_1.2.2_x64.exe")]
    [InlineData("arm64", "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.2/DeskCue_Setup_1.2.2_arm64.exe")]
    public void UpdateResponseFixtures_ContainMetadataForEachSupportedArchitecture(string architecture, string expectedUrl)
    {
        var options = new JsonSerializerOptions(JsonSerializerDefaults.Web)
        {
            NumberHandling = JsonNumberHandling.AllowReadingFromString
        };
        var manifest = JsonSerializer.Deserialize<AppUpdateManifest>(ManifestFixtureJson, options)!;
        Assert.True(AppUpdateService.TrySelectInstallerForArchitecture(manifest, architecture));
        Assert.Equal(expectedUrl, manifest.DownloadUrl);
        var download = CreateDownloadFixture("abc", 1234);
        Assert.True(AppUpdateService.TrySelectInstallerForArchitecture(download, architecture));
        Assert.Equal(expectedUrl, download.DownloadUrl);
    }

    [Fact]
    public void InstallerAssetSelection_UsesTheCurrentProcessArchitecture()
    {
        Assert.Equal("x64", AppUpdateService.GetInstallerArchitectureSuffix(Architecture.X64));
        Assert.Equal("arm64", AppUpdateService.GetInstallerArchitectureSuffix(Architecture.Arm64));
        Assert.True(AppUpdateService.IsInstallerAssetName("DeskCue_Setup_1.2.4_x64.exe", "x64"));
        Assert.False(AppUpdateService.IsInstallerAssetName("DeskCue_Setup_1.2.4_arm64.exe", "x64"));
        Assert.True(AppUpdateService.IsInstallerAssetName("DeskCue_Setup_1.2.4_arm64.exe", "arm64"));
        Assert.True(AppUpdateService.IsInstallerAssetName("DeskCue_Setup_1.4.8_x64.exe", "x64"));
        Assert.True(AppUpdateService.IsInstallerAssetName("DeskCue_Setup_1.4.8_arm64.exe", "arm64"));
        Assert.False(AppUpdateService.IsInstallerAssetName("DeskCue_Setup_1.4.3_x64_Full.exe", "x64"));
        Assert.False(AppUpdateService.IsInstallerAssetName("DeskCue_Setup_1.4.3_arm64_Full.exe", "arm64"));
        Assert.True(AppUpdateService.IsInstallerDownloadCompatibleWithArchitecture(
            "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.4/DeskCue_Setup_1.2.4_arm64.exe",
            "arm64"));
        Assert.False(AppUpdateService.IsInstallerDownloadCompatibleWithArchitecture(
            "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.4/DeskCue_Setup_1.2.4_x64.exe",
            "arm64"));
        Assert.False(AppUpdateService.IsInstallerDownloadCompatibleWithArchitecture(
            "https://example.com/download/latest",
            "arm64"));
        Assert.Equal(
            $"DeskCue_Setup_1.2.4_{AppUpdateService.CurrentInstallerArchitectureSuffix}.exe",
            AppUpdateService.GetInstallerFileName(new Uri("https://example.com/download/latest"), "1.2.4"));
    }

    [Fact]
    public void ManifestInstallerSelection_UsesIndependentArm64Metadata()
    {
        var manifest = new AppUpdateManifest
        {
            Version = "1.3.8",
            DownloadUrl = "https://github.com/CyberShadowX/DeskCue/releases/download/v1.3.8/DeskCue_Setup_1.3.8_x64.exe",
            Sha256 = new string('A', 64),
            Size = 101,
            Arm64DownloadUrl = "https://github.com/CyberShadowX/DeskCue/releases/download/v1.3.8/DeskCue_Setup_1.3.8_arm64.exe",
            Arm64Sha256 = new string('B', 64),
            Arm64Size = 202
        };

        Assert.True(AppUpdateService.TrySelectInstallerForArchitecture(manifest, "arm64"));
        Assert.EndsWith("_arm64.exe", manifest.DownloadUrl, StringComparison.OrdinalIgnoreCase);
        Assert.Equal(new string('B', 64), manifest.Sha256);
        Assert.Equal(202, manifest.Size);
    }

    [Fact]
    public void ManifestInstallerSelection_LeavesPrimaryMetadataForX64()
    {
        var manifest = new AppUpdateManifest
        {
            Version = "1.3.8",
            DownloadUrl = "https://github.com/CyberShadowX/DeskCue/releases/download/v1.3.8/DeskCue_Setup_1.3.8_x64.exe",
            Sha256 = new string('A', 64),
            Size = 101,
            Arm64DownloadUrl = "https://github.com/CyberShadowX/DeskCue/releases/download/v1.3.8/DeskCue_Setup_1.3.8_arm64.exe",
            Arm64Sha256 = new string('B', 64),
            Arm64Size = 202
        };

        Assert.True(AppUpdateService.TrySelectInstallerForArchitecture(manifest, "x64"));
        Assert.EndsWith("_x64.exe", manifest.DownloadUrl, StringComparison.OrdinalIgnoreCase);
        Assert.Equal(new string('A', 64), manifest.Sha256);
        Assert.Equal(101, manifest.Size);
    }

    [Fact]
    public void LocalizedSummary_PrefersEnglishWhenLocaleIsMissing()
    {
        var manifest = new AppUpdateManifest
        {
            Summary =
            {
                ["zh-CN"] = "中文摘要",
                ["zh-TW"] = "繁體摘要",
                ["en-US"] = "English summary"
            }
        };

        Assert.Equal("English summary", manifest.GetLocalizedSummary("de-DE"));
        Assert.Equal("中文摘要", manifest.GetLocalizedSummary("zh-CN"));
        Assert.Equal("繁體摘要", manifest.GetLocalizedSummary("zh-TW"));
        Assert.Equal("繁體摘要", manifest.GetLocalizedSummary("zh-MO"));
    }

    [Theory]
    [InlineData("https://pan.quark.cn/s/version-specific", "https://mirror.example.com/deskbox")]
    [InlineData("javascript:alert('unsafe')", "http://mirror.example.com/deskbox")]
    [InlineData("", "")]
    public void ManualUpdateDownloadUrl_AlwaysOpensOfficialDownloadPage(string manualUrl, string mirrorUrl)
    {
        var manifest = new AppUpdateManifest
        {
            ManualDownloadUrl = manualUrl,
            MirrorUrl = mirrorUrl
        };

        Assert.Equal(
            "https://github.com/CyberShadowX/DeskCue/releases/latest",
            SettingsViewModel.GetManualUpdateDownloadUrl(manifest));
        Assert.Equal("https://github.com/CyberShadowX/DeskCue/releases/latest", SettingsViewModel.GetManualUpdateDownloadUrl(null));
    }

    [Theory]
    [InlineData("1.2.1", "1.2.2", true)]
    [InlineData("1.2.1", "v1.2.2", true)]
    [InlineData("1.2.1", "1.2.2-beta.1", true)]
    [InlineData("1.2.1", "1.2.1", false)]
    [InlineData("1.2.1", "1.2.0", false)]
    [InlineData("1.2.1", "not-a-version", false)]
    [InlineData("1.5.9.1", "v1.5.9.2", true)]
    [InlineData("1.5.9.1", "v1.5.10.1", true)]
    [InlineData("1.5.9.2", "1.5.9.1", false)]
    public void IsRemoteVersionNewer_ComparesSemanticVersionPrefix(string currentVersion, string remoteVersion, bool expected)
    {
        Assert.Equal(expected, AppUpdateService.IsRemoteVersionNewer(currentVersion, remoteVersion));
    }

    [Fact]
    public async Task CheckForUpdatesAsync_ReadsManifestAndDetectsUpdate()
    {
        using var httpClient = CreateHttpClient(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(
                ManifestFixtureJson,
                Encoding.UTF8,
                "application/json")
        });

        var service = new AppUpdateService(httpClient, "https://github.com/CyberShadowX/DeskCue/releases/latest/download/stable.json", _tempRoot);

        var result = await service.CheckForUpdatesAsync("1.2.1");

        Assert.Equal(AppUpdateCheckStatus.UpdateAvailable, result.Status);
        Assert.NotNull(result.Manifest);
        Assert.Equal(1, result.Manifest.SchemaVersion);
        Assert.Equal("1.2.2", result.Manifest.Version);
        Assert.Equal(1234, result.Manifest.Size);
        Assert.Equal("https://pan.quark.cn/s/version-specific", result.Manifest.ManualDownloadUrl);
        Assert.Same(result, service.LastCheckResult);
    }

    [Fact]
    public async Task CheckForUpdatesAsync_FallsBackToGitHubReleaseWhenManifestUnavailable()
    {
        using var httpClient = CreateHttpClient(request =>
        {
            string url = request.RequestUri!.ToString();
            if (url.Contains("stable.json", StringComparison.OrdinalIgnoreCase))
            {
                return new HttpResponseMessage(HttpStatusCode.NotFound);
            }

            return new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(
                    """
                    {
                      "tag_name": "v1.2.4",
                      "html_url": "https://github.com/CyberShadowX/DeskCue/releases/tag/v1.2.4",
                      "body": "## Highlights\n- Improved update flow",
                      "assets": [
                        {
                          "name": "DeskCue_Setup_1.2.4_x64.exe",
                          "browser_download_url": "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.4/DeskCue_Setup_1.2.4_x64.exe",
                          "size": 23423211,
                          "digest": "sha256:8ecb3092ae5bd6883f8a75bbea03d9800251e0c23fdbe1bf4d91fd3a62565561"
                        },
                        {
                          "name": "DeskCue_Setup_1.2.4_arm64.exe",
                          "browser_download_url": "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.4/DeskCue_Setup_1.2.4_arm64.exe",
                          "size": 23423211,
                          "digest": "sha256:8ecb3092ae5bd6883f8a75bbea03d9800251e0c23fdbe1bf4d91fd3a62565561"
                        }
                      ]
                    }
                    """,
                    Encoding.UTF8,
                    "application/json")
            };
        });

        var service = new AppUpdateService(
            httpClient,
            "https://github.com/CyberShadowX/DeskCue/releases/latest/download/stable.json",
            _tempRoot,
            AppUpdateService.DefaultGitHubLatestReleaseApiUrl);

        var result = await service.CheckForUpdatesAsync("1.2.3");

        Assert.Equal(AppUpdateCheckStatus.UpdateAvailable, result.Status);
        Assert.NotNull(result.Manifest);
        Assert.Equal("1.2.4", result.Manifest.Version);
        Assert.Equal($"https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.4/DeskCue_Setup_1.2.4_{AppUpdateService.CurrentInstallerArchitectureSuffix}.exe", result.Manifest.DownloadUrl);
        Assert.Equal("8ECB3092AE5BD6883F8A75BBEA03D9800251E0C23FDBE1BF4D91FD3A62565561", result.Manifest.Sha256);
        Assert.Equal(23423211, result.Manifest.Size);
        Assert.Equal("https://github.com/CyberShadowX/DeskCue/releases/tag/v1.2.4", result.Manifest.ReleaseNotesUrl);
        Assert.Equal("## Highlights\n- Improved update flow", result.Manifest.GetReleaseNotesForLocale("en-US"));
    }

    [Fact]
    public async Task CheckForUpdatesAsync_FallsBackToGitHubShaAssetWhenDigestMissing()
    {
        using var httpClient = CreateHttpClient(request =>
        {
            string url = request.RequestUri!.ToString();
            if (url.Contains("stable.json", StringComparison.OrdinalIgnoreCase))
            {
                return new HttpResponseMessage(HttpStatusCode.NotFound);
            }

            if (url.EndsWith(".sha256", StringComparison.OrdinalIgnoreCase))
            {
                return new HttpResponseMessage(HttpStatusCode.OK)
                {
                    Content = new StringContent(
                        $"8ECB3092AE5BD6883F8A75BBEA03D9800251E0C23FDBE1BF4D91FD3A62565561  DeskCue_Setup_1.2.4_{AppUpdateService.CurrentInstallerArchitectureSuffix}.exe",
                        Encoding.UTF8,
                        "text/plain")
                };
            }

            return new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent(
                    """
                    {
                      "tag_name": "v1.2.4",
                      "html_url": "https://github.com/CyberShadowX/DeskCue/releases/tag/v1.2.4",
                      "assets": [
                        {
                          "name": "DeskCue_Setup_1.2.4_x64.exe",
                          "browser_download_url": "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.4/DeskCue_Setup_1.2.4_x64.exe",
                          "size": 23423211
                        },
                        {
                          "name": "DeskCue_Setup_1.2.4_x64.exe.sha256",
                          "browser_download_url": "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.4/DeskCue_Setup_1.2.4_x64.exe.sha256",
                          "size": 95
                        },
                        {
                          "name": "DeskCue_Setup_1.2.4_arm64.exe",
                          "browser_download_url": "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.4/DeskCue_Setup_1.2.4_arm64.exe",
                          "size": 23423211
                        },
                        {
                          "name": "DeskCue_Setup_1.2.4_arm64.exe.sha256",
                          "browser_download_url": "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.4/DeskCue_Setup_1.2.4_arm64.exe.sha256",
                          "size": 95
                        }
                      ]
                    }
                    """,
                    Encoding.UTF8,
                    "application/json")
            };
        });

        var service = new AppUpdateService(
            httpClient,
            "https://github.com/CyberShadowX/DeskCue/releases/latest/download/stable.json",
            _tempRoot,
            AppUpdateService.DefaultGitHubLatestReleaseApiUrl);

        var result = await service.CheckForUpdatesAsync("1.2.3");

        Assert.Equal(AppUpdateCheckStatus.UpdateAvailable, result.Status);
        Assert.NotNull(result.Manifest);
        Assert.Equal("8ECB3092AE5BD6883F8A75BBEA03D9800251E0C23FDBE1BF4D91FD3A62565561", result.Manifest.Sha256);
    }

    [Fact]
    public async Task DownloadUpdateAsync_RejectsInstallerWithoutHash()
    {
        using var httpClient = CreateHttpClient(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new ByteArrayContent([1, 2, 3])
        });
        var service = new AppUpdateService(httpClient, updateRootPath: _tempRoot);

        var result = await service.DownloadUpdateAsync(CreateDownloadFixture());

        Assert.False(result.Success);
        Assert.Equal(AppUpdateDownloadFailureKind.HashMissing, result.FailureKind);
    }

    [Fact]
    public async Task DownloadUpdateAsync_VerifiesSha256AndWritesInstaller()
    {
        byte[] payload = Encoding.UTF8.GetBytes("deskcue-installer");
        string sha256 = Convert.ToHexString(SHA256.HashData(payload));
        using var httpClient = CreateHttpClient(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new ByteArrayContent(payload)
        });
        var service = new AppUpdateService(httpClient, updateRootPath: _tempRoot);

        var result = await service.DownloadUpdateAsync(CreateDownloadFixture(sha256, payload.Length));

        Assert.True(result.Success, $"{result.FailureKind}: {result.ErrorMessage}");
        Assert.True(File.Exists(result.FilePath));
        Assert.Equal(payload, await File.ReadAllBytesAsync(result.FilePath!));
    }

    [Fact]
    public async Task DownloadUpdateAsync_RejectsInstallerForAnotherArchitecture()
    {
        byte[] payload = Encoding.UTF8.GetBytes("deskcue-installer");
        string sha256 = Convert.ToHexString(SHA256.HashData(payload));
        string otherArchitecture = AppUpdateService.CurrentInstallerArchitectureSuffix == "arm64"
            ? "x64"
            : "arm64";
        using var httpClient = CreateHttpClient(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new ByteArrayContent(payload)
        });
        var service = new AppUpdateService(httpClient, updateRootPath: _tempRoot);

        var result = await service.DownloadUpdateAsync(new AppUpdateManifest
        {
            Version = "1.2.2",
            DownloadUrl = $"https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.2/DeskCue_Setup_1.2.2_{otherArchitecture}.exe",
            Sha256 = sha256,
            Size = payload.Length
        });

        Assert.False(result.Success);
        Assert.Equal(AppUpdateDownloadFailureKind.InvalidManifest, result.FailureKind);
    }

    [Fact]
    public async Task DownloadUpdateAsync_ReportsCallerCancellationSeparately()
    {
        using var httpClient = CreateHttpClient(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new ByteArrayContent([1, 2, 3])
        });
        var service = new AppUpdateService(httpClient, updateRootPath: _tempRoot);
        using var cancellation = new CancellationTokenSource();
        cancellation.Cancel();

        var result = await service.DownloadUpdateAsync(new AppUpdateManifest
        {
            Version = "1.2.2",
            DownloadUrl = $"https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.2/DeskCue_Setup_1.2.2_{AppUpdateService.CurrentInstallerArchitectureSuffix}.exe",
            Sha256 = "00"
        }, cancellationToken: cancellation.Token);

        Assert.False(result.Success);
        Assert.Equal(AppUpdateDownloadFailureKind.Cancelled, result.FailureKind);
    }

    [Fact]
    public async Task PrepareDetachedUpdaterHelper_CopiesUpdaterOutsideAppDirectory()
    {
        string appDirectory = Path.Combine(_tempRoot, "app");
        string updateRoot = Path.Combine(_tempRoot, "updates");
        Directory.CreateDirectory(appDirectory);

        string sourceExe = Path.Combine(appDirectory, "DeskCue.Updater.exe");
        string sourceRuntimeConfig = Path.Combine(appDirectory, "DeskCue.Updater.runtimeconfig.json");
        string nativeModule = Path.Combine(appDirectory, "deskcue_native.dll");
        await File.WriteAllTextAsync(sourceExe, "exe");
        await File.WriteAllTextAsync(sourceRuntimeConfig, "{}");
        await File.WriteAllTextAsync(nativeModule, "native");

        string detachedExe = AppUpdateService.PrepareDetachedUpdaterHelper(appDirectory, updateRoot);

        Assert.True(File.Exists(detachedExe));
        Assert.NotEqual(sourceExe, detachedExe);
        Assert.StartsWith(Path.Combine(updateRoot, "helper"), detachedExe, StringComparison.OrdinalIgnoreCase);
        Assert.Equal("exe", await File.ReadAllTextAsync(detachedExe));
        Assert.True(File.Exists(Path.Combine(Path.GetDirectoryName(detachedExe)!, "DeskCue.Updater.runtimeconfig.json")));
        Assert.False(File.Exists(Path.Combine(Path.GetDirectoryName(detachedExe)!, "deskcue_native.dll")));
    }

    [Fact]
    public void TryGetInstallDirectory_ReturnsCurrentDeskCueExecutableDirectory()
    {
        string installDirectory = Directory.CreateDirectory(Path.Combine(_tempRoot, "D-drive", "DeskCue")).FullName;
        string appPath = Path.Combine(installDirectory, "DeskCue.exe");
        File.WriteAllText(appPath, "exe");

        bool resolved = AppUpdateService.TryGetInstallDirectory(appPath, out string actualDirectory);

        Assert.True(resolved);
        Assert.Equal(installDirectory, actualDirectory, ignoreCase: true);
        Assert.False(AppUpdateService.TryGetInstallDirectory(
            Path.Combine(installDirectory, "OtherApp.exe"),
            out _));
    }

    [Fact]
    public async Task ContentManifestFetch_AcceptsNotesOnlyManifest_AndRejectsInstallerOnlyManifest()
    {
        // The Store channel's synthesized manifest carries a
        // ms-windowsstore:// download target; the display path must accept a
        // manifest that has notes but no installer link at all.
        string notesOnlyJson =
            """{"schemaVersion":1,"channel":"stable","version":"1.5.9","releaseNotesUrl":"https://github.com/CyberShadowX/DeskCue/releases/tag/v1.5.9"}""";
        string installerOnlyJson =
            """{"schemaVersion":1,"channel":"stable","version":"1.5.9","downloadUrl":"https://deskbox.fun/DeskBox_Setup.exe","sha256":"aa"}""";

        var notesClient = CreateHttpClient(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(notesOnlyJson, Encoding.UTF8, "application/json")
        });
        AppUpdateManifest? accepted = await AppUpdateService.FetchContentManifestAsync(
            "https://github.com/CyberShadowX/DeskCue/releases/latest/download/stable.json", notesClient, CancellationToken.None);
        Assert.NotNull(accepted);
        Assert.Equal("1.5.9", accepted!.Version);
        Assert.True(AppUpdateManifest.IsSafeReleaseNotesUrl(accepted.ReleaseNotesUrl));

        var installerClient = CreateHttpClient(_ => new HttpResponseMessage(HttpStatusCode.OK)
        {
            Content = new StringContent(installerOnlyJson, Encoding.UTF8, "application/json")
        });
        AppUpdateManifest? rejected = await AppUpdateService.FetchContentManifestAsync(
            "https://github.com/CyberShadowX/DeskCue/releases/latest/download/stable.json", installerClient, CancellationToken.None);
        Assert.Null(rejected);
    }

    [Fact]
    public void ReleaseNotesOnlyManifest_PointsAtGitHubTagForExactVersion()
    {
        AppUpdateManifest manifest = AppUpdateService.CreateReleaseNotesOnlyManifest("1.5.9");

        Assert.Equal("1.5.9", manifest.Version);
        Assert.Equal(
            "https://github.com/CyberShadowX/DeskCue/releases/tag/v1.5.9",
            manifest.ReleaseNotesUrl);
        Assert.True(AppUpdateManifest.IsSafeReleaseNotesUrl(manifest.ReleaseNotesUrl));
        Assert.True(manifest.HasReleaseNotesOrUrl);
        Assert.False(AppUpdateService.IsManifestUsable(manifest));
    }

    public void Dispose()
    {
        if (Directory.Exists(_tempRoot))
        {
            Directory.Delete(_tempRoot, recursive: true);
        }
    }

    private static AppUpdateManifest CreateDownloadFixture(string sha256 = "", long size = 0) => new()
    {
        Version = "1.2.2",
        DownloadUrl = "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.2/DeskCue_Setup_1.2.2_x64.exe",
        Sha256 = sha256,
        Size = size,
        Arm64DownloadUrl = "https://github.com/CyberShadowX/DeskCue/releases/download/v1.2.2/DeskCue_Setup_1.2.2_arm64.exe",
        Arm64Sha256 = sha256,
        Arm64Size = size
    };

    private static HttpClient CreateHttpClient(Func<HttpRequestMessage, HttpResponseMessage> handler)
    {
        return new HttpClient(new StubHttpMessageHandler(handler));
    }

    private sealed class StubHttpMessageHandler : HttpMessageHandler
    {
        private readonly Func<HttpRequestMessage, HttpResponseMessage> _handler;

        public StubHttpMessageHandler(Func<HttpRequestMessage, HttpResponseMessage> handler)
        {
            _handler = handler;
        }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            return Task.FromResult(_handler(request));
        }
    }

    [Theory]
    [InlineData("https://deskbox.fun/update/DeskBox_Setup.exe", false)]
    [InlineData("https://cdn.deskbox.fun/DeskBox_Setup.exe", false)]
    [InlineData("https://github.com/CyberShadowX/DeskCue/releases/download/v1.5.2/DeskCue_Setup_1.5.2_x64.exe", true)]
    [InlineData("http://deskbox.fun/update/DeskBox_Setup.exe", false)]
    [InlineData("https://evil.example.com/DeskBox_Setup.exe", false)]
    [InlineData("https://deskbox.fun.evil.example.com/DeskBox_Setup.exe", false)]
    [InlineData("https://github.evil.example.com/DeskBox_Setup.exe", false)]
    [InlineData("https://github.com/attacker/evil/releases/download/v1.0.0/DeskBox_Setup.exe", false)]
    [InlineData("https://github.com/CyberShadowX/DeskCue/blob/main/DeskBox_Setup.exe", false)]
    [InlineData("https://objects.githubusercontent.com/some-asset-path", false)]
    public void IsManifestUsable_PinsTheInstallerOriginToTrustedHttpsHosts(
        string downloadUrl,
        bool expected)
    {
        var manifest = new AppUpdateManifest
        {
            Version = "1.5.2.0",
            DownloadUrl = downloadUrl
        };

        Assert.Equal(expected, AppUpdateService.IsManifestUsable(manifest));
    }

    [Fact]
    public void IsManifestUsable_RejectsAnUntrustedArm64DownloadUrl()
    {
        var manifest = new AppUpdateManifest
        {
            Version = "1.5.2.0",
            DownloadUrl = "https://deskbox.fun/update/DeskCue_Setup_x64.exe",
            Arm64DownloadUrl = "http://evil.example.com/DeskCue_Setup_arm64.exe"
        };

        Assert.False(AppUpdateService.IsManifestUsable(manifest));
    }

    public static TheoryData<string, string> AppCultureToInstallerLanguageCases => new()
    {
        { LocalizationService.LanguageChinese, "chinesesimplified" },
        { LocalizationService.LanguageChineseTraditional, "chinesetraditional" },
        { LocalizationService.LanguageEnglish, "english" },
        { LocalizationService.LanguageJapanese, "japanese" },
        { LocalizationService.LanguageGerman, "german" },
        { LocalizationService.LanguagePortuguese, "brazilianportuguese" },
        { LocalizationService.LanguageHindi, "hindi" },
        { LocalizationService.LanguageSpanish, "spanish" },
        { LocalizationService.LanguageFrench, "french" },
        { LocalizationService.LanguageArabic, "arabic" },
        { LocalizationService.LanguageBengali, "bengali" },
        { LocalizationService.LanguageRussian, "russian" },
        { LocalizationService.LanguageKorean, "korean" },
    };

    [Theory]
    [MemberData(nameof(AppCultureToInstallerLanguageCases))]
    public void InstallerLanguageMapping_CoversEveryAppLanguage(
        string appCultureName,
        string installerLanguage)
    {
        // Reverse of InstallLanguageCode in installer/DeskCue.iss (identical
        // [Languages] in DeskCue.arm64.iss) — extend both sides together.
        Assert.Equal(installerLanguage, AppUpdateService.MapAppCultureToInstallerLanguage(appCultureName));
    }

    [Fact]
    public void InstallerLanguageMapping_RejectsValuesOutsideTheAppLanguageDomain()
    {
        Assert.Null(AppUpdateService.MapAppCultureToInstallerLanguage(null));
        Assert.Null(AppUpdateService.MapAppCultureToInstallerLanguage(string.Empty));
        Assert.Null(AppUpdateService.MapAppCultureToInstallerLanguage(LocalizationService.LanguageSystem));
        Assert.Null(AppUpdateService.MapAppCultureToInstallerLanguage("zh-HK"));
        Assert.Null(AppUpdateService.MapAppCultureToInstallerLanguage("fr-CA"));
    }

    [Fact]
    public void InstallerLanguageMapping_AgreesWithTheUpdaterWhitelist()
    {
        // The app-side mapping and the updater-side whitelist are two halves
        // of one contract; every mapped name must survive the whitelist so
        // the /LANG pin can never be silently dropped for a shipped language.
        foreach (object?[] row in AppCultureToInstallerLanguageCases)
        {
            string installerLanguage = (string)row[1]!;
            Assert.Equal(
                installerLanguage,
                DeskCue.Updater.Program.ResolveInstallerLanguage(installerLanguage));
        }
    }
}
