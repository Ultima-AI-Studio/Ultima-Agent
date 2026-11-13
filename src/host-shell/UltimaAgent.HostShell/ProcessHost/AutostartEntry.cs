using System.Runtime.InteropServices;

namespace UltimaAgent.HostShell.ProcessHost;

internal static class AutostartEntry
{
    public const string ShortcutFileName = "UltimaAgent.lnk";
    public const string KindEnvironmentName = "ULTIMA_AUTOSTART_KIND";
    public const string HostExecutableEnvironmentName = "ULTIMA_HOST_EXE";
    private const string ShortcutKind = "shortcut";
    private const string NoneKind = "none";
    private const string ShellProgId = "WScript.Shell";

    public static string ShortcutPath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.Startup),
        ShortcutFileName);

    public static void Apply(string projectRoot)
    {
        string kind = Environment.GetEnvironmentVariable(KindEnvironmentName) ?? ShortcutKind;
        if (string.Equals(kind, NoneKind, StringComparison.OrdinalIgnoreCase))
        {
            Remove();
            return;
        }
        if (!string.Equals(kind, ShortcutKind, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException(
                $"{KindEnvironmentName} must be '{ShortcutKind}' or '{NoneKind}', not '{kind}'.");
        }
        Install(projectRoot);
    }

    public static void Install(string projectRoot)
    {
        string targetPath = ResolveHostExecutable();
        string workingDirectory = Path.GetFullPath(projectRoot);
        Directory.CreateDirectory(Path.GetDirectoryName(ShortcutPath)!);

        Type shellType = Type.GetTypeFromProgID(ShellProgId)
            ?? throw new InvalidOperationException($"COM ProgID '{ShellProgId}' is unavailable.");
        object? shellObject = null;
        object? shortcutObject = null;
        try
        {
            shellObject = Activator.CreateInstance(shellType)
                ?? throw new InvalidOperationException($"Could not create COM object '{ShellProgId}'.");
            dynamic shell = shellObject;
            dynamic shortcut = shell.CreateShortcut(ShortcutPath);
            shortcutObject = shortcut;
            shortcut.TargetPath = targetPath;
            shortcut.WorkingDirectory = workingDirectory;
            shortcut.WindowStyle = 1;
            shortcut.Description = "Ultima Agent HostShell";
            shortcut.Save();
        }
        finally
        {
            ReleaseComObject(shortcutObject);
            ReleaseComObject(shellObject);
        }
    }

    public static void Remove()
    {
        if (File.Exists(ShortcutPath))
        {
            File.Delete(ShortcutPath);
        }
    }

    public static bool IsInstalled() => File.Exists(ShortcutPath);

    private static string ResolveHostExecutable()
    {
        string? configured = Environment.GetEnvironmentVariable(HostExecutableEnvironmentName);
        string path = string.IsNullOrWhiteSpace(configured)
            ? Path.Combine(AppContext.BaseDirectory, "UltimaAgent.HostShell.exe")
            : configured;
        path = Path.GetFullPath(path);
        if (!File.Exists(path))
        {
            throw new FileNotFoundException("HostShell executable for autostart was not found.", path);
        }
        return path;
    }

    private static void ReleaseComObject(object? value)
    {
        if (value is not null && Marshal.IsComObject(value))
        {
            _ = Marshal.FinalReleaseComObject(value);
        }
    }
}
