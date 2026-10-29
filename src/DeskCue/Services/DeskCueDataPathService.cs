using System.Security.Cryptography;
using System.Text;

namespace DeskCue.Services;

public sealed class DeskCueDataPathService
{
    public const string DevelopmentRootEnvironmentVariable = "DESKCUE_DEV_DATA_ROOT";
    public const string AotPreviewRootEnvironmentVariable = "DESKCUE_AOT_PREVIEW_DATA_ROOT";
    private const string ProductionInstanceScope = "0F10D29D";

    private static readonly object CurrentGate = new();
    private static DeskCueDataPathService? s_current;

    public static DeskCueDataPathService Current
    {
        get
        {
            lock (CurrentGate)
            {
                return s_current ??= new(ResolveConfiguredRoot());
            }
        }
    }

    // Called once by the friend test assembly's module initializer, before
    // App or a service can capture any process-wide storage paths. Retail
    // environment-variable behavior remains unchanged.
    internal static void InitializeForTests(string rootPath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(rootPath);
        var paths = new DeskCueDataPathService(rootPath);
        if (!paths.IsDevelopmentRoot)
        {
            throw new ArgumentException("Tests require an isolated application root.", nameof(rootPath));
        }

        lock (CurrentGate)
        {
            if (s_current is not null)
            {
                throw new InvalidOperationException("Application data paths have already been initialized.");
            }

            s_current = paths;
        }
    }

    public DeskCueDataPathService(string? rootPath = null)
    {
        string productionRoot = Path.GetFullPath(Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "DeskCue"));
        RootPath = string.IsNullOrWhiteSpace(rootPath)
            ? productionRoot
            : Path.GetFullPath(rootPath.Trim());
        IsDevelopmentRoot = !string.Equals(
            RootPath.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar),
            productionRoot.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar),
            StringComparison.OrdinalIgnoreCase);
        InstanceScope = IsDevelopmentRoot
            ? CreateInstanceScope(RootPath)
            : ProductionInstanceScope;
    }

    public string RootPath { get; }
    public bool IsDevelopmentRoot { get; }
    public string InstanceScope { get; }
    public string ActivationEventName => $"DeskCue_Activate_Event_{InstanceScope}";
    public string SingleInstanceMutexName => $"DeskCue_SingleInstance_Mutex_{InstanceScope}";
    public string DataDirectory => Path.Combine(RootPath, "data");
    public string UpdatesDirectory => Path.Combine(RootPath, "updates");
    // Recovery snapshots intentionally live beside, rather than inside, the
    // app-data root. Direct install: the directory really is
    // %LOCALAPPDATA%\DeskCue-Recovery and survives a normal uninstall.
    // Store (MSIX): AppData write virtualization redirects the write into
    // Packages\<PFN>\LocalCache, so uninstalling the package deletes the
    // recovery copy with it; an in-place update over the same
    // PackageFamilyName keeps LocalCache and therefore the snapshots.
    // Guaranteeing uninstall survival on the store channel as well would
    // require declaring desktop6:FileSystemWriteVirtualization=disabled —
    // a restricted capability that is effectively unavailable to third-party
    // apps (store-lifecycle audit 2026-10-07, option D); the accepted
    // alternative is the in-product disclosure on the backup settings page.
    public string RecoveryDirectory => IsDevelopmentRoot
        ? $"{RootPath}-Recovery"
        : Path.Combine(
            Path.GetDirectoryName(RootPath) ?? RootPath,
            "DeskCue-Recovery");
    public string LogFilePath => Path.Combine(RootPath, "DeskCue.log");

    private static string? ResolveConfiguredRoot()
    {
#if DEBUG
        return Environment.GetEnvironmentVariable(DevelopmentRootEnvironmentVariable);
#elif DESKCUE_NATIVE_AOT
        return Environment.GetEnvironmentVariable(AotPreviewRootEnvironmentVariable);
#else
        return null;
#endif
    }

    private static string CreateInstanceScope(string rootPath)
    {
        byte[] hash = SHA256.HashData(Encoding.UTF8.GetBytes(rootPath.ToUpperInvariant()));
        return Convert.ToHexString(hash.AsSpan(0, 8));
    }
}
