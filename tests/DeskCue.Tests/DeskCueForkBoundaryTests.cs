using System.Net;
using System.Security.Cryptography;
using DeskCue.Models;
using DeskCue.Services;

namespace DeskCue.Tests;

public sealed class DeskCueForkBoundaryTests
{
    private const string OwnRelease = "https://github.com/CyberShadowX/DeskCue/releases/download/v1.5.10.1/";

    [Fact]
    public void Manifest_AcceptsOnlyForkOwnedProductInstallers()
    {
        Assert.True(AppUpdateService.IsManifestUsable(Manifest(OwnRelease + "DeskCue_Setup_1.5.10.1_x64.exe")));
    }

    [Theory]
    [InlineData("https://github.com/Tianyu199509/DeskBox/releases/download/v1.5.10/DeskBox_Setup_1.5.10_x64.exe")]
    [InlineData("https://deskbox.fun/DeskCue_Setup_1.5.10.1_x64.exe")]
    [InlineData("https://github.com/someone/DeskCue/releases/download/v1/DeskCue_Setup_1.5.10.1_x64.exe")]
    [InlineData(OwnRelease + "DeskBox_Setup_1.5.10.1_x64.exe")]
    [InlineData(OwnRelease + "other.exe")]
    [InlineData("http://github.com/CyberShadowX/DeskCue/releases/download/v1/DeskCue_Setup_1.5.10.1_x64.exe")]
    [InlineData("https://github.com/CyberShadowX/DeskCue-other/releases/download/v1/DeskCue_Setup_1.5.10.1_x64.exe")]
    public void Manifest_RejectsForeignOriginOrProduct(string url)
    {
        Assert.False(AppUpdateService.IsManifestUsable(Manifest(url)));
    }

    [Theory]
    [InlineData("DeskBox_Setup_1.5.10.1_x64.exe")]
    [InlineData("unknown.exe")]
    [InlineData("DeskCue_Setup_1.5.10.1_arm64.exe")]
    public void DownloadCompatibility_RejectsUnknownProductAndWrongArchitecture(string name)
    {
        Assert.False(AppUpdateService.IsInstallerDownloadCompatibleWithArchitecture(OwnRelease + name, "x64"));
    }

    [Fact]
    public async Task DefaultFeedback_DoesNotSendContentOrDiagnosticsToAnotherPublisher()
    {
        var handler = new CountRequestsHandler();
        using var client = new HttpClient(handler);
        string root = Path.Combine(Path.GetTempPath(), "DeskCue.ForkBoundary", Guid.NewGuid().ToString("N"));
        var service = new FeedbackService(httpClient: client,
            clientStateFilePath: Path.Combine(root, "id.txt"),
            cooldownStateFilePath: Path.Combine(root, "cooldown.txt"));
        try
        {
            var result = await service.SubmitAsync(DeskCueFeedbackKind.Bug, "A sufficiently detailed fork feedback report.", true);
            await service.GetMyFeedbackAsync();
            await service.UploadDiagnosticsAsync(42, Path.Combine(root, "missing.zip"));
            Assert.False(result.Ok);
            Assert.Equal(0, handler.RequestCount);
            Assert.False(Directory.Exists(root));
        }
        finally
        {
            if (Directory.Exists(root)) Directory.Delete(root, recursive: true);
        }
    }

    private static AppUpdateManifest Manifest(string url) => new()
    {
        SchemaVersion = 1,
        Version = "1.5.10.1",
        DownloadUrl = url,
        Sha256 = new string('A', 64)
    };

    [Fact]
    public async Task HashMismatch_DiscardsPartialDownloadAndPreservesPriorInstaller()
    {
        string root = Path.Combine(Path.GetTempPath(), "DeskCue.ForkBoundary", Guid.NewGuid().ToString("N"));
        string name = $"DeskCue_Setup_1.5.10.1_{AppUpdateService.CurrentInstallerArchitectureSuffix}.exe";
        string folder = Path.Combine(root, "1.5.10.1");
        string priorInstaller = Path.Combine(folder, name);
        byte[] prior = [1, 2, 3];
        Directory.CreateDirectory(folder);
        await File.WriteAllBytesAsync(priorInstaller, prior);
        using var client = new HttpClient(new PayloadHandler([4, 5, 6]));
        var service = new AppUpdateService(client, updateRootPath: root);
        var manifest = Manifest(OwnRelease + name);
        manifest.Sha256 = Convert.ToHexString(SHA256.HashData([7, 8, 9]));
        try
        {
            var result = await service.DownloadUpdateAsync(manifest);
            Assert.False(result.Success);
            Assert.Equal(AppUpdateDownloadFailureKind.HashMismatch, result.FailureKind);
            Assert.Null(result.FilePath);
            Assert.Null(service.LastDownloadedInstallerPath);
            Assert.Equal(prior, await File.ReadAllBytesAsync(priorInstaller));
            Assert.False(File.Exists(priorInstaller + ".tmp"));
        }
        finally
        {
            Directory.Delete(root, recursive: true);
        }
    }

    private sealed class PayloadHandler(byte[] bytes) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken) =>
            Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK) { Content = new ByteArrayContent(bytes) });
    }

    private sealed class CountRequestsHandler : HttpMessageHandler
    {
        public int RequestCount { get; private set; }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            RequestCount++;
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK)
            {
                Content = new StringContent("{\"ok\":true,\"id\":1,\"items\":[]}")
            });
        }
    }
}
