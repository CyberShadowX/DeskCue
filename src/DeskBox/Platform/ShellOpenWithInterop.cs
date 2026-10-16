using System.Runtime.InteropServices;

namespace DeskBox.Platform;

/// <summary>
/// Native interop for the documented Open With association APIs
/// (SHAssocEnumHandlers / IAssocHandler). These are Shell-owned objects that
/// read association data only; no third-party context menu handler is ever
/// loaded through this path, so the shell-extension process isolation
/// contract is preserved. Vtable order and IIDs are verified against the
/// Windows SDK 10.0.26100 shobjidl_core.h header.
/// </summary>
internal static class ShellOpenWithInterop
{
    internal const uint AssocFilterRecommended = 0x1;

    internal static readonly Guid IID_IDataObject =
        new("0000010e-0000-0000-c000-000000000046");

    private static readonly Guid IID_IShellItem =
        new("43826d1e-e718-42ee-bc55-a1e261c37bfe");

    [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = false)]
    internal static extern void SHAssocEnumHandlers(
        string extension,
        uint filter,
        [MarshalAs(UnmanagedType.Interface)]
        out ShellOpenWithEnumHandlers handlers);

    [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = false)]
    private static extern void SHCreateItemFromParsingName(
        string path,
        IntPtr bindContext,
        ref Guid riid,
        out IntPtr shellItem);

    [DllImport("shell32.dll", PreserveSig = false)]
    private static extern void SHCreateShellItemArrayFromShellItem(
        IntPtr shellItem,
        ref Guid riid,
        out IntPtr shellItemArray);

    [DllImport("ole32.dll")]
    internal static extern void CoTaskMemFree(IntPtr buffer);

    /// <summary>
    /// Builds the Shell data object for one item so it can be handed to
    /// <c>IAssocHandler::Invoke</c>, which accepts an IDataObject.
    /// Returns the data object pointer; the caller must release it with
    /// <see cref="ReleaseDataObject"/> after the invoke returns.
    /// </summary>
    internal static bool TryCreateDataObjectForPath(
        string path,
        out IntPtr dataObject,
        out IntPtr shellItem)
    {
        dataObject = IntPtr.Zero;
        shellItem = IntPtr.Zero;
        Guid shellItemId = IID_IShellItem;
        Guid dataObjectId = IID_IDataObject;
        try
        {
            SHCreateItemFromParsingName(
                path,
                IntPtr.Zero,
                ref shellItemId,
                out shellItem);
            SHCreateShellItemArrayFromShellItem(
                shellItem,
                ref dataObjectId,
                out dataObject);
            return dataObject != IntPtr.Zero;
        }
        catch (COMException)
        {
            ReleaseDataObject(ref dataObject, ref shellItem);
            return false;
        }
    }

    internal static void ReleaseDataObject(
        ref IntPtr dataObject,
        ref IntPtr shellItem)
    {
        if (dataObject != IntPtr.Zero)
        {
            Marshal.Release(dataObject);
            dataObject = IntPtr.Zero;
        }

        if (shellItem != IntPtr.Zero)
        {
            Marshal.Release(shellItem);
            shellItem = IntPtr.Zero;
        }
    }

    /// <summary>
    /// Shows the system Open With dialog through the documented
    /// <c>openas</c> verb.
    /// </summary>
    internal static bool TryShowOpenAsDialog(
        IntPtr ownerWindow,
        string filePath)
    {
        var info = new ShellExecuteInfo
        {
            Size = (uint)Marshal.SizeOf<ShellExecuteInfo>(),
            OwnerWindow = ownerWindow,
            Verb = "openas",
            FileName = filePath,
            Show = 1
        };
        return ShellExecuteEx(ref info);
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct ShellExecuteInfo
    {
        public uint Size;
        public uint Mask;
        public IntPtr OwnerWindow;
        public IntPtr Monitor;
        public string? Verb;
        public string? FileName;
        public string? Parameters;
        public string? Directory;
        public int Show;
        public IntPtr InstApp;
        public IntPtr IdList;
        public string? Class;
        public IntPtr HkeyClass;
        public uint HotKey;
        public IntPtr Icon;
        public IntPtr ProcessHandle;
    }

    [DllImport("shell32.dll", EntryPoint = "ShellExecuteExW",
        SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool ShellExecuteEx(ref ShellExecuteInfo info);

    [ComImport]
    [Guid("973810ae-9599-4b88-9e4d-6ee98c9552da")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface ShellOpenWithEnumHandlers
    {
        // IEnumAssocHandlers exposes only Next in the SDK header.
        void Next(
            uint celt,
            [Out] IntPtr[] rgelt,
            out uint pceltFetched);
    }

    [ComImport]
    [Guid("F04061AC-1659-4a3f-A954-775AA57FC083")]
    [InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    internal interface ShellOpenWithAssocHandler
    {
        // Order per shobjidl_core.h: GetName, GetUIName, GetIconLocation,
        // IsRecommended, MakeDefault, Invoke(IDataObject), CreateInvoker.
        void GetName(out IntPtr displayName);
        void GetUIName(out IntPtr uiDisplayName);
        void GetIconLocation(out IntPtr iconPath, out int iconIndex);
        [PreserveSig] int IsRecommended();
        void MakeDefault(string description);
        void Invoke(IntPtr dataObject);
        void CreateInvoker(
            IntPtr dataObject,
            out IntPtr invoker);
    }
}
