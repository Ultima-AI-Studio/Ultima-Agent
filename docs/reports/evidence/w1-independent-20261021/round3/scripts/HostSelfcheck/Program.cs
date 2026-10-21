using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

if (args.Length != 2)
{
    Console.Error.WriteLine("Usage: HostSelfcheckProbe <workspace-root> <evidence-directory>");
    return 2;
}

string workspace = Path.GetFullPath(args[0]);
string evidence = Path.GetFullPath(args[1]);
Directory.CreateDirectory(evidence);
string project = Path.Combine(workspace, "src", "host-shell", "UltimaAgent.HostShell", "UltimaAgent.HostShell.csproj");
string executable = Path.Combine(workspace, "src", "host-shell", "UltimaAgent.HostShell", "bin", "Release",
    "net8.0-windows10.0.19041.0", "win-x64", "UltimaAgent.HostShell.exe");
string dotnet = @"C:\Users\Administrator\.dotnet\dotnet.exe";
string buildLog = Path.Combine(evidence, "t3-selfcheck-build.log");
string runtimePath = Path.Combine(evidence, "t3-selfcheck-runtime.json");
string featurePath = Path.Combine(evidence, "t3-selfcheck-floating-ball-ready.json");
string capturePath = Path.Combine(evidence, "t3-selfcheck-floating-ball.png");
DateTimeOffset startedAt = DateTimeOffset.UtcNow;
JsonSerializerOptions jsonOptions = new() { WriteIndented = true };

DevelopmentProcess[] beforeProcesses = CaptureDevelopmentProcesses();
WindowObservation[] baseline = NativeWindows.Snapshot();
HashSet<long> baselineHandles = baseline.Select(item => item.Handle).ToHashSet();
Dictionary<string, WindowObservation> observed = new(StringComparer.Ordinal);
BuildResult? build = null;
Process? host = null;
long hostHandle = 0;
int? hostExitCode = null;
string? failure = null;
bool hostWasTargetKilled = false;
List<NativeRect> hostRectHistory = [];

try
{
    build = await RunBuildAsync();
    if (build.ExitCode != 0)
        throw new InvalidOperationException($"Build failed with exit code {build.ExitCode}.");
    if (!File.Exists(executable))
        throw new FileNotFoundException("Host executable missing after build.", executable);

    ProcessStartInfo launch = new(executable)
    {
        WorkingDirectory = Path.GetDirectoryName(executable)!,
        UseShellExecute = false,
        CreateNoWindow = true,
        WindowStyle = ProcessWindowStyle.Hidden
    };
    launch.Environment["ULTIMA_HOST_EVIDENCE_DIR"] = evidence;
    launch.Environment["ULTIMA_HOST_STAGE"] = "t3-selfcheck";
    launch.Environment["ULTIMA_HOST_AUTO_EXIT_MS"] = "6500";
    launch.Environment["ULTIMA_HOST_FLOATINGBALL_TEST"] = "1";
    launch.Environment["ULTIMA_HOST_FLOATINGBALL_CAPTURE_PATH"] = capturePath;
    string launchExeHash = Sha256(executable);
    string launchDllHash = Sha256(Path.ChangeExtension(executable, ".dll"));
    host = Process.Start(launch) ?? throw new InvalidOperationException("Host process did not start.");
    File.WriteAllText(Path.Combine(evidence, "host-started.json"), JsonSerializer.Serialize(new
    {
        atUtc = DateTimeOffset.UtcNow,
        processId = host.Id,
        processStartTimeUtc = SafeStartTime(host),
        actualProcessExecutable = host.MainModule?.FileName,
        executable,
        executableSha256 = launchExeHash,
        assemblySha256 = launchDllHash,
        useShellExecute = false,
        createNoWindow = true,
        autoExitMilliseconds = 6500
    }, jsonOptions));

    Stopwatch runtimeDeadline = Stopwatch.StartNew();
    while (!host.HasExited && runtimeDeadline.Elapsed < TimeSpan.FromSeconds(30))
    {
        host.Refresh();
        long currentHostHandle = host.MainWindowHandle.ToInt64();
        if (currentHostHandle != 0 && NativeWindows.TryGetRect(currentHostHandle, out NativeRect currentHostRect)
            && !hostRectHistory.Contains(currentHostRect))
        {
            hostRectHistory.Add(currentHostRect);
        }
        CaptureNewWindows(observed, baselineHandles);
        if (hostHandle == 0 && File.Exists(runtimePath))
        {
            using JsonDocument runtime = JsonDocument.Parse(File.ReadAllText(runtimePath));
            if (runtime.RootElement.TryGetProperty("mainWindowHandle", out JsonElement handleElement))
                hostHandle = handleElement.GetInt64();
        }
        await Task.Delay(25);
    }
    CaptureNewWindows(observed, baselineHandles);
    if (!host.HasExited)
        throw new TimeoutException("Host did not auto-exit within 30 seconds.");
    hostExitCode = host.ExitCode;
    if (hostExitCode != 0)
        throw new InvalidOperationException($"Host exited with {hostExitCode}.");
}
catch (Exception exception)
{
    failure = $"{exception.GetType().Name}: {exception.Message}";
}
finally
{
    if (host is not null && !host.HasExited)
    {
        host.Kill(entireProcessTree: true);
        hostWasTargetKilled = true;
        await host.WaitForExitAsync();
    }
    if (host is not null && host.HasExited)
        hostExitCode = host.ExitCode;
}

DevelopmentProcess[] afterProcesses = CaptureDevelopmentProcesses();
HashSet<string> afterIdentities = afterProcesses.Select(item => item.Identity).ToHashSet(StringComparer.OrdinalIgnoreCase);
DevelopmentProcess[] missingProcesses = beforeProcesses.Where(item => !afterIdentities.Contains(item.Identity)).ToArray();
HashSet<string> beforeIdentities = beforeProcesses.Select(item => item.Identity).ToHashSet(StringComparer.OrdinalIgnoreCase);
DevelopmentProcess[] newProcesses = afterProcesses.Where(item => !beforeIdentities.Contains(item.Identity)).ToArray();

RuntimeReceipt? runtimeReceipt = ReadJson<RuntimeReceipt>(runtimePath);
FloatingReceipt? featureReceipt = ReadJson<FloatingReceipt>(featurePath);
int hostId = host?.Id ?? 0;
NativeRect hostRect = runtimeReceipt?.Rect is null
    ? default
    : new NativeRect(runtimeReceipt.Rect.Left, runtimeReceipt.Rect.Top, runtimeReceipt.Rect.Right, runtimeReceipt.Rect.Bottom);
WindowObservation[] allObserved = observed.Values.OrderBy(item => item.ObservedAtUtc).ToArray();
WindowObservation[] runOwned = allObserved.Where(item =>
    item.ProcessId == hostId || item.AncestorProcessIds.Contains(hostId)
    || (build is not null && (item.ProcessId == build.ProcessId || item.AncestorProcessIds.Contains(build.ProcessId)))).ToArray();
WindowObservation[] unexpectedOwned = runOwned.Where(item =>
    !IsAllowedHostWindow(item, hostId, hostHandle, hostRect, hostRectHistory)).ToArray();

bool buildPassed = build is not null && build.ExitCode == 0 && build.ZeroWarnings && build.ZeroErrors
    && build.MaximumMainWindowHandle == 0;
bool runtimePassed = runtimeReceipt is not null && runtimeReceipt.Status == "WINDOW_READY"
    && runtimeReceipt.ProcessId == hostId && runtimeReceipt.MainWindowHandle == hostHandle && hostHandle != 0;
bool featurePassed = featureReceipt is not null && featureReceipt.Status == "FLOATING_BALL_READY"
    && featureReceipt.ProcessId == hostId && featureReceipt.MainWindowHandle == hostHandle
    && featureReceipt.Borderless && featureReceipt.Topmost && File.Exists(featureReceipt.ScreenshotPath)
    && Sha256(featureReceipt.ScreenshotPath) == featureReceipt.ScreenshotSha256;
bool exitPassed = hostExitCode == 0 && !hostWasTargetKilled;
bool zeroExtraWindowPassed = unexpectedOwned.Length == 0;
bool processPreservationPassed = missingProcesses.Length == 0;
bool passed = failure is null && buildPassed && runtimePassed && featurePassed && exitPassed
    && zeroExtraWindowPassed && processPreservationPassed;

object result = new
{
    status = passed ? "PASS" : "FAIL",
    startedAtUtc = startedAt,
    completedAtUtc = DateTimeOffset.UtcNow,
    chain = new
    {
        build = new
        {
            passed = buildPassed,
            processId = build?.ProcessId,
            exitCode = build?.ExitCode,
            compilerZeroWarnings = build?.ZeroWarnings,
            compilerZeroErrors = build?.ZeroErrors,
            noWarnUsed = false,
            maximumMainWindowHandle = build?.MaximumMainWindowHandle
        },
        launch = new { passed = runtimePassed && featurePassed, processId = hostId, useShellExecute = false },
        window = new { passed = runtimePassed && featurePassed, mainWindowHandle = hostHandle },
        exit = new { passed = exitPassed, exitCode = hostExitCode, targetedKillUsed = hostWasTargetKilled }
    },
    zeroExtraWindows = new
    {
        passed = zeroExtraWindowPassed,
        method = "25 ms EnumWindows samples; ownership by Toolhelp32 parent chain; WebView surface checked against host HWND rectangle history",
        baselineVisibleWindowCount = baseline.Length,
        uniqueNewVisibleWindowObservations = allObserved.Length,
        runOwnedObservationCount = runOwned.Length,
        unexpectedRunOwnedWindowCount = unexpectedOwned.Length,
        unexpectedRunOwnedWindows = unexpectedOwned,
        allRunOwnedWindows = runOwned,
        hostRectHistory,
        note = "No desktop pixels were captured. WebView2 CapturePreview is component-only evidence."
    },
    processPreservation = new
    {
        passed = processPreservationPassed,
        identity = "process name + PID + StartTimeUtc",
        before = beforeProcesses,
        after = afterProcesses,
        missing = missingProcesses,
        newAfter = newProcesses
    },
    files = new
    {
        project,
        executable,
        executableSha256 = File.Exists(executable) ? Sha256(executable) : null,
        buildLog,
        runtimePath,
        featurePath,
        capturePath
    },
    failure
};

string jsonPath = Path.Combine(evidence, "result.json");
File.WriteAllText(jsonPath, JsonSerializer.Serialize(result, jsonOptions));
string reportPath = Path.Combine(evidence, "report.md");
File.WriteAllText(reportPath, $"""
    # 宿主壳最终自检

    - 结论：{(passed ? "通过" : "失败")}
    - 构建：{(buildPassed ? "通过，0 warning / 0 error" : "失败")}
    - 启动与窗口：{(runtimePassed && featurePassed ? $"通过，PID {hostId}，HWND {hostHandle}" : "失败")}
    - 原生退出：{(exitPassed ? "通过，exit 0" : $"失败，exit {hostExitCode}")}
    - 本轮进程树额外可见窗口：{unexpectedOwned.Length}
    - 后台开发进程创建身份：{(processPreservationPassed ? $"通过，{beforeProcesses.Length}/{beforeProcesses.Length} 保留" : $"失败，缺失 {missingProcesses.Length}")}
    - 桌面截图：未执行；悬浮球图像仅来自 WebView2 CapturePreview。

    这是执行端自检证据，不代表 root 已完成最终鼠标拖动或 W1 签署。
    """);

Console.WriteLine($"HOST_SHELL_SELFCHECK={(passed ? "PASS" : "FAIL")}");
Console.WriteLine($"BUILD={(buildPassed ? "PASS" : "FAIL")} HOST_PID={hostId} HWND={hostHandle} EXIT={hostExitCode}");
Console.WriteLine($"UNEXPECTED_RUN_OWNED_WINDOWS={unexpectedOwned.Length}");
Console.WriteLine($"BACKGROUND_IDENTITIES={beforeProcesses.Length - missingProcesses.Length}/{beforeProcesses.Length}");
return passed ? 0 : 1;

async Task<BuildResult> RunBuildAsync()
{
    ProcessStartInfo info = new(dotnet)
    {
        WorkingDirectory = workspace,
        UseShellExecute = false,
        CreateNoWindow = true,
        WindowStyle = ProcessWindowStyle.Hidden,
        RedirectStandardOutput = true,
        RedirectStandardError = true
    };
    foreach (string argument in new[]
    {
        "build", project, "-c", "Release", "-r", "win-x64", "--no-restore", "-v", "minimal",
        "-p:UseSharedCompilation=false"
    }) info.ArgumentList.Add(argument);
    info.Environment["DOTNET_CLI_UI_LANGUAGE"] = "en-US";
    using Process process = Process.Start(info) ?? throw new InvalidOperationException("Build process did not start.");
    Task<string> stdout = process.StandardOutput.ReadToEndAsync();
    Task<string> stderr = process.StandardError.ReadToEndAsync();
    long maximumMainWindowHandle = 0;
    Stopwatch timeout = Stopwatch.StartNew();
    while (!process.HasExited && timeout.Elapsed < TimeSpan.FromSeconds(120))
    {
        process.Refresh();
        maximumMainWindowHandle = Math.Max(maximumMainWindowHandle, process.MainWindowHandle.ToInt64());
        CaptureNewWindows(observed, baselineHandles);
        await Task.Delay(25);
    }
    if (!process.HasExited)
    {
        process.Kill(entireProcessTree: true);
        await process.WaitForExitAsync();
        throw new TimeoutException($"Build PID {process.Id} exceeded 120 seconds and only its process tree was terminated.");
    }
    string log = (await stdout) + (await stderr);
    File.WriteAllText(buildLog, log);
    return new BuildResult(
        process.Id,
        process.ExitCode,
        maximumMainWindowHandle,
        ContainsZero(log, "warning", "警告"),
        ContainsZero(log, "error", "错误"));
}

static bool ContainsZero(string text, string english, string chinese) =>
    System.Text.RegularExpressions.Regex.IsMatch(text, $@"(?m)^\s*0\s+{english}(?:\(s\)|s)?\s*$", System.Text.RegularExpressions.RegexOptions.IgnoreCase)
    || System.Text.RegularExpressions.Regex.IsMatch(text, $@"(?m)^\s*0\s*个{chinese}\s*$");

static void CaptureNewWindows(Dictionary<string, WindowObservation> collection, HashSet<long> baselineWindowHandles)
{
    foreach (WindowObservation item in NativeWindows.Snapshot())
    {
        if (baselineWindowHandles.Contains(item.Handle)) continue;
        string key = $"{item.Handle}|{item.ProcessId}|{item.Left}|{item.Top}|{item.Right}|{item.Bottom}";
        collection.TryAdd(key, item);
    }
}

static bool IsAllowedHostWindow(
    WindowObservation item,
    int hostId,
    long hostHandle,
    NativeRect hostRect,
    IReadOnlyList<NativeRect> hostRectHistory)
{
    if (item.ProcessId == hostId && item.Handle == hostHandle) return true;
    if (!item.ProcessName.Equals("msedgewebview2", StringComparison.OrdinalIgnoreCase)
        || !item.AncestorProcessIds.Contains(hostId)) return false;
    NativeRect surface = new(item.Left, item.Top, item.Right, item.Bottom);
    return Contains(hostRect, surface) || hostRectHistory.Any(rect => Contains(rect, surface));
}

static bool Contains(NativeRect outer, NativeRect inner) =>
    inner.Left >= outer.Left && inner.Top >= outer.Top
    && inner.Right <= outer.Right && inner.Bottom <= outer.Bottom;

static DevelopmentProcess[] CaptureDevelopmentProcesses()
{
    string[] names = ["codex", "codex-app-server", "codex-exec-server", "python", "pythonw", "node", "dotnet", "ollama", "brain", "watchdog"];
    List<DevelopmentProcess> result = [];
    foreach (Process process in Process.GetProcesses())
    {
        using (process)
        {
            if (!names.Contains(process.ProcessName, StringComparer.OrdinalIgnoreCase)) continue;
            try
            {
                result.Add(new DevelopmentProcess(process.ProcessName, process.Id,
                    process.StartTime.ToUniversalTime().ToString("O")));
            }
            catch (InvalidOperationException) { }
            catch (System.ComponentModel.Win32Exception) { }
        }
    }
    return result.OrderBy(item => item.Name).ThenBy(item => item.ProcessId).ToArray();
}

static string? SafeStartTime(Process process)
{
    try { return process.StartTime.ToUniversalTime().ToString("O"); }
    catch { return null; }
}

static T? ReadJson<T>(string path)
{
    if (!File.Exists(path)) return default;
    return JsonSerializer.Deserialize<T>(File.ReadAllText(path), new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
}

static string Sha256(string path)
{
    using FileStream stream = File.OpenRead(path);
    return Convert.ToHexString(SHA256.HashData(stream)).ToLowerInvariant();
}

internal sealed record BuildResult(int ProcessId, int ExitCode, long MaximumMainWindowHandle, bool ZeroWarnings, bool ZeroErrors);
internal sealed record DevelopmentProcess(string Name, int ProcessId, string StartTimeUtc)
{
    public string Identity => $"{Name}|{ProcessId}|{StartTimeUtc}";
}
internal sealed record RuntimeReceipt(string Status, int ProcessId, long MainWindowHandle, ReceiptRect Rect);
internal sealed record ReceiptRect(int Left, int Top, int Right, int Bottom);
internal sealed record FloatingReceipt(
    string Status,
    int ProcessId,
    long MainWindowHandle,
    bool Borderless,
    bool Topmost,
    string ScreenshotPath,
    string ScreenshotSha256);

internal sealed record WindowObservation(
    long Handle,
    int ProcessId,
    int[] AncestorProcessIds,
    string ProcessName,
    string ClassName,
    int Left,
    int Top,
    int Right,
    int Bottom,
    DateTimeOffset ObservedAtUtc);

[StructLayout(LayoutKind.Sequential)]
internal readonly record struct NativeRect(int Left, int Top, int Right, int Bottom);

internal static class NativeWindows
{
    private const uint GaRoot = 2;

    public static WindowObservation[] Snapshot()
    {
        Dictionary<int, int> parents = SnapshotParents();
        List<WindowObservation> result = [];
        EnumWindows((window, state) =>
        {
            if (!IsWindowVisible(window) || GetAncestor(window, GaRoot) != window) return true;
            _ = GetWindowThreadProcessId(window, out uint processIdValue);
            int processId = checked((int)processIdValue);
            StringBuilder className = new(256);
            _ = GetClassName(window, className, className.Capacity);
            _ = GetWindowRect(window, out NativeRect rect);
            string processName = "";
            try { using Process process = Process.GetProcessById(processId); processName = process.ProcessName; } catch { }
            result.Add(new WindowObservation(
                window.ToInt64(),
                processId,
                Ancestors(processId, parents),
                processName,
                className.ToString(),
                rect.Left,
                rect.Top,
                rect.Right,
                rect.Bottom,
                DateTimeOffset.UtcNow));
            return true;
        }, 0);
        return result.ToArray();
    }

    public static bool TryGetRect(long handle, out NativeRect rect) =>
        GetWindowRect((nint)handle, out rect);

    private static Dictionary<int, int> SnapshotParents()
    {
        Dictionary<int, int> result = [];
        nint snapshot = CreateToolhelp32Snapshot(2, 0);
        if (snapshot == -1) return result;
        try
        {
            ProcessEntry entry = new() { Size = (uint)Marshal.SizeOf<ProcessEntry>() };
            if (Process32First(snapshot, ref entry))
            {
                do result[checked((int)entry.ProcessId)] = checked((int)entry.ParentProcessId);
                while (Process32Next(snapshot, ref entry));
            }
        }
        finally { _ = CloseHandle(snapshot); }
        return result;
    }

    private static int[] Ancestors(int processId, Dictionary<int, int> parents)
    {
        List<int> result = [];
        int current = processId;
        for (int depth = 0; depth < 16 && parents.TryGetValue(current, out int parent)
            && parent != 0 && parent != current; depth++)
        {
            result.Add(parent);
            current = parent;
        }
        return result.ToArray();
    }

    private delegate bool EnumWindowsDelegate(nint window, nint state);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    private struct ProcessEntry
    {
        public uint Size;
        public uint Usage;
        public uint ProcessId;
        public nint DefaultHeapId;
        public uint ModuleId;
        public uint Threads;
        public uint ParentProcessId;
        public int PriorityBase;
        public uint Flags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
        public string? ExeFile;
    }

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumWindows(EnumWindowsDelegate callback, nint state);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool IsWindowVisible(nint window);
    [DllImport("user32.dll")]
    private static extern nint GetAncestor(nint window, uint flags);
    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(nint window, out uint processId);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetClassName(nint window, StringBuilder text, int count);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetWindowRect(nint window, out NativeRect rect);
    [DllImport("kernel32.dll")]
    private static extern nint CreateToolhelp32Snapshot(uint flags, uint processId);
    [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool Process32First(nint snapshot, ref ProcessEntry entry);
    [DllImport("kernel32.dll", CharSet = CharSet.Auto)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool Process32Next(nint snapshot, ref ProcessEntry entry);
    [DllImport("kernel32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CloseHandle(nint handle);
}
