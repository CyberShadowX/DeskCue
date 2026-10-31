using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Principal;
using System.Text;
using System.Text.Json;
using System.Xml;
using System.Xml.Linq;
using DeskCue.Services;

// Opt-in integration probe: run this EXE, including its DeskCue manifest.
// Creates only a disabled, GUID-scoped task and deletes it in finally.
// Never calls Enable/TryRegister, which would change the user's real startup task.
internal static partial class Program
{
    private static int Main(string[] args)
    {
        // Pure repair-tool modes MUST return before ACP/native/task integration.
        // Any unknown argument also fails closed instead of running the probe.
        if (args.Length != 0)
        {
            return RunPureMode(args);
        }
        string taskName = $"DeskCue Unicode Probe-小-{Guid.NewGuid():N}";
        string xmlPath = Path.Combine(Path.GetTempPath(), taskName + ".xml");
        bool registered = false;
        try
        {
            uint codePage = GetACP();
            Check(codePage == 65001, $"The DeskCue UTF-8 manifest was not applied: ACP={codePage}.");
            using WindowsIdentity identity = WindowsIdentity.GetCurrent();
            string sid = identity.User!.Value;
            const string executable = @"C:\DeskCue Unicode Probe\小 桌面 café 日本語 😀\DeskCue.exe";
            XDocument document = XDocument.Parse(DirectStartupTaskBackend.BuildTaskXml(executable, sid));
            XNamespace ns = document.Root!.Name.Namespace;
            document.Root.Element(ns + "Settings")!.Element(ns + "Enabled")!.Value = "false";
            document.Root.Element(ns + "RegistrationInfo")!.Element(ns + "URI")!.Value = "\\" + taskName;
            File.WriteAllText(xmlPath, document.ToString(), Encoding.Unicode);
            RunSchtasks("/Create", "/TN", taskName, "/XML", xmlPath);
            registered = true;

            foreach (ApartmentState apartment in new[] { ApartmentState.STA, ApartmentState.MTA })
            {
                Exception? failure = null;
                var thread = new Thread(() =>
                {
                    try
                    {
                        string xml = DirectStartupTaskXmlReader.Read(taskName);
                        DirectStartupTaskRegistration registration = DirectStartupTaskBackend.ParseTaskXml(xml);
                        Check(registration.ExecutablePath == executable, "Unicode executable path changed.");
                        Check(!registration.Enabled, "The probe task must stay disabled.");
                        Check(registration.TaskName == taskName, "Unicode task name changed.");

                        // The fixture has an isolated name and is disabled. Check
                        // the other production invariants on an in-memory copy.
                        registration = registration with
                        {
                            TaskName = DirectStartupTaskBackend.GetTaskName(sid),
                            Enabled = true
                        };
                        Check(new DirectStartupTaskBackend().IsPreferred(registration, executable),
                            DirectStartupTaskBackend.DescribePreferenceCheckResults(registration, executable));

                        // Rollback uses this exact Unicode snapshot, written as UTF-16.
                        File.WriteAllText(xmlPath, xml, Encoding.Unicode);
                        RunSchtasks("/Create", "/TN", taskName, "/XML", xmlPath, "/F");
                        Check(DirectStartupTaskBackend.ParseTaskXml(
                            DirectStartupTaskXmlReader.Read(taskName)).ExecutablePath == executable,
                            "Unicode snapshot restore changed the path.");
                    }
                    catch (Exception ex)
                    {
                        failure = ex;
                    }
                }) { IsBackground = true };
                thread.SetApartmentState(apartment);
                thread.Start();
                Check(thread.Join(TimeSpan.FromSeconds(30)), $"{apartment} read timed out.");
                if (failure is not null)
                {
                    throw new InvalidOperationException($"{apartment} probe failed.", failure);
                }
                Console.WriteLine($"PASS ACP={codePage} apartment={apartment} UnicodeQuery=True Contract=True SnapshotRestore=True");
            }

            try
            {
                _ = DirectStartupTaskXmlReader.Read(taskName + "-missing");
                throw new InvalidOperationException("Missing task unexpectedly read successfully.");
            }
            catch (Exception ex) when (ex.HResult == unchecked((int)0x80070002))
            {
                Console.WriteLine("PASS MissingTask=0x80070002");
            }
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex);
            return 1;
        }
        finally
        {
            if (registered)
            {
                RunSchtasks("/Delete", "/TN", taskName, "/F");
                Console.WriteLine("PASS ProbeTaskDeleted=True");
            }
            File.Delete(xmlPath);
        }
    }

    private static int RunPureMode(string[] args)
    {
        Console.OutputEncoding = new UTF8Encoding(false);
        try
        {
            bool emit = args[0] == "--emit-startup-contract" && args.Length == 2;
            bool validate = args[0] == "--validate-startup-contract" && args.Length == 4;
            Check(emit || validate, "Expected a recognized pure contract mode and its exact arguments.");
            using WindowsIdentity identity = WindowsIdentity.GetCurrent();
            string sid = identity.User?.Value ?? throw new InvalidOperationException("User SID unavailable.");
            string executable = args[1];
            CheckNormalPath(executable, executable);
            if (emit)
            {
                using var writer = new Utf8JsonWriter(Console.OpenStandardOutput());
                writer.WriteStartObject();
                writer.WriteString("TaskName", DirectStartupTaskBackend.GetTaskName(sid));
                writer.WriteString("Arguments", DirectStartupTaskBackend.StartupArguments);
                writer.WriteString("Xml", DirectStartupTaskBackend.BuildTaskXml(executable, sid));
                writer.WriteEndObject();
                writer.Flush();
                return 0;
            }

            string xml = File.ReadAllText(args[3], Encoding.UTF8);
            ValidateStrictShape(xml, executable, sid, identity.Name, args[2]);
            DirectStartupTaskRegistration registration = DirectStartupTaskBackend.ParseTaskXml(xml)
                with { TaskName = args[2] }; // Query identity, not the optional XML URI.
            Check(new DirectStartupTaskBackend().IsPreferred(registration, executable),
                DirectStartupTaskBackend.DescribePreferenceCheckResults(registration, executable));
            Console.WriteLine("{\"Valid\":true}");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }

    private static void CheckNormalPath(string candidate, string expected)
    {
        Check(Path.IsPathFullyQualified(candidate) && !candidate.StartsWith(@"\\", StringComparison.Ordinal) &&
              candidate.IndexOfAny(['"', '%', '~', '/']) < 0 &&
              string.Equals(Path.GetFullPath(candidate), candidate, StringComparison.OrdinalIgnoreCase) &&
              string.Equals(candidate, expected, StringComparison.OrdinalIgnoreCase), "Unnormalized or aliased task path.");
        for (string? part = candidate; part is not null; part = Path.GetDirectoryName(part))
        {
            if (File.Exists(part) || Directory.Exists(part))
            {
                Check((File.GetAttributes(part) & FileAttributes.ReparsePoint) == 0, "Task path contains a reparse point.");
            }
        }
    }

    private static void ValidateStrictShape(string xml, string executable, string sid, string user, string taskName)
    {
        using var reader = XmlReader.Create(new StringReader(xml), new XmlReaderSettings
        {
            DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null
        });
        XDocument document = XDocument.Load(reader);
        XNamespace ns = "http://schemas.microsoft.com/windows/2004/02/mit/task";
        XElement root = document.Root ?? throw new InvalidDataException("No task root.");
        Check(root.Name == ns + "Task", "Unexpected task root/namespace.");
        foreach (XElement node in root.DescendantsAndSelf())
        {
            Check(node.Name.Namespace == ns && node.Elements().GroupBy(e => e.Name).All(g => g.Count() == 1),
                "Foreign namespace or duplicate task element.");
        }
        static XElement One(XElement parent, XName name) => parent.Elements(name).Single();
        static string Value(XElement parent, XName name) => parent.Element(name)?.Value ?? "";
        XElement registration = One(root, ns + "RegistrationInfo");
        XElement settings = One(root, ns + "Settings");
        XElement principals = One(root, ns + "Principals");
        XElement principal = One(principals, ns + "Principal");
        XElement triggers = One(root, ns + "Triggers");
        XElement trigger = One(triggers, ns + "LogonTrigger");
        XElement actions = One(root, ns + "Actions");
        XElement action = One(actions, ns + "Exec");
        Check(principals.Elements().Count() == 1 && triggers.Elements().Count() == 1 && actions.Elements().Count() == 1,
            "Extra principal, trigger or action.");
        foreach (string tag in new[] { "Principal", "LogonTrigger", "Exec" })
        {
            Check(root.Descendants(ns + tag).Count() == 1, "Nested or extra principal/trigger/action.");
        }
        Check(!root.Descendants(ns + "GroupId").Any(), "Group principal not allowed.");
        bool CurrentUser(string value) => string.Equals(value, sid, StringComparison.OrdinalIgnoreCase) ||
                                          string.Equals(value, user, StringComparison.OrdinalIgnoreCase);
        Check(CurrentUser(Value(principal, ns + "UserId")) && CurrentUser(Value(trigger, ns + "UserId")), "Foreign user.");
        Check(Value(principal, ns + "LogonType") == "InteractiveToken" &&
              Value(principal, ns + "RunLevel") is "" or "LeastPrivilege", "Unexpected principal type/privilege.");
        foreach (XElement parent in new[] { settings, trigger })
        {
            Check(parent.Element(ns + "Enabled") is not { } enabled || enabled.Value is "true" or "1", "Task disabled.");
        }
        Check(Value(trigger, ns + "Delay") is "" or "PT0S" &&
              trigger.Elements().All(e => e.Name.LocalName is "UserId" or "Enabled" or "Delay"), "Unexpected logon trigger.");
        Check(taskName == DirectStartupTaskBackend.GetTaskName(sid) && Value(registration, ns + "Source") == "DeskCue",
            "Foreign task identity/source.");
        string uri = Value(registration, ns + "URI");
        Check(uri.Length == 0 || uri == "\\" + taskName, "Foreign task URI.");
        Check(action.Elements().All(e => e.Name.LocalName is "Command" or "Arguments" or "WorkingDirectory"),
            "Unexpected Exec element.");
        CheckNormalPath(Value(action, ns + "Command"), executable);
        Check(Value(action, ns + "Arguments") == DirectStartupTaskBackend.StartupArguments, "Unexpected arguments.");
        string directory = Value(action, ns + "WorkingDirectory");
        if (directory.Length != 0) { CheckNormalPath(directory, Path.GetDirectoryName(executable)!); }
    }

    private static void Check(bool condition, string message)
    {
        if (!condition)
        {
            throw new InvalidOperationException(message);
        }
    }

    private static void RunSchtasks(params string[] arguments)
    {
        var start = new ProcessStartInfo(Path.Combine(Environment.SystemDirectory, "schtasks.exe"))
        {
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };
        foreach (string argument in arguments)
        {
            start.ArgumentList.Add(argument);
        }
        using Process process = Process.Start(start)!;
        Task<string> output = process.StandardOutput.ReadToEndAsync();
        Task<string> error = process.StandardError.ReadToEndAsync();
        if (!process.WaitForExit(10_000))
        {
            process.Kill();
            throw new TimeoutException("Probe schtasks command timed out.");
        }
        Task.WaitAll(output, error);
        Check(process.ExitCode == 0, $"schtasks exit={process.ExitCode}: {error.Result} {output.Result}");
    }

    [LibraryImport("kernel32.dll")]
    private static partial uint GetACP();
}
