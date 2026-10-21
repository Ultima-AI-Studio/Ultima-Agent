using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;
using Microsoft.UI.Windowing;
using Windows.Graphics;

namespace UltimaAgent.HostShell;

internal static class DpiAcceptanceEvidence
{
    private const int LogicalDiameter = 180;
    private const uint MonitorDefaultToNearest = 2;
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

    private static readonly ExpectedMonitor[] ExpectedTopology =
    [
        new(@"\\.\DISPLAY3", new NativeRect(0, 0, 3840, 2160), 144),
        new(@"\\.\DISPLAY2", new NativeRect(3840, 0, 6400, 1440), 96),
        new(@"\\.\DISPLAY1", new NativeRect(6400, 0, 8960, 1440), 96)
    ];

    public static async Task RunAsync(
        AppWindow appWindow,
        nint handle,
        string directory,
        string stage,
        Func<SizeInt32> getCaptionRegionSize)
    {
        string outputPath = Path.Combine(directory, $"{stage}-dpi-acceptance.json");
        NativeRect originalRect = ReadWindowRect(handle);
        WindowSample original = ReadSample(handle, getCaptionRegionSize);
        IReadOnlyList<MonitorRecord> monitors = EnumerateMonitors();
        List<object> steps = [];
        List<string> violations = [];
        Exception? probeFailure = null;

        try
        {
            foreach (ExpectedMonitor expected in ExpectedTopology)
            {
                MonitorRecord? target = monitors.FirstOrDefault(item =>
                    string.Equals(item.DeviceName, expected.DeviceName, StringComparison.OrdinalIgnoreCase));
                if (target is null)
                {
                    violations.Add($"Missing physical monitor {expected.DeviceName}.");
                    continue;
                }

                SizeInt32 currentSize = appWindow.Size;
                int targetX = target.Work.Left + Math.Max(0, (target.Work.Width - currentSize.Width) / 2);
                int targetY = target.Work.Top + Math.Max(0, (target.Work.Height - currentSize.Height) / 2);
                DateTimeOffset moveStarted = DateTimeOffset.UtcNow;
                appWindow.Move(new PointInt32(targetX, targetY));
                StableWindow stable = await WaitForStableAsync(
                    handle,
                    target.DeviceName,
                    getCaptionRegionSize,
                    TimeSpan.FromSeconds(8));
                await Task.Delay(TimeSpan.FromSeconds(1));
                WindowSample afterHold = ReadSample(handle, getCaptionRegionSize);

                int expectedPhysicalDiameter = (int)Math.Round(LogicalDiameter * stable.Sample.Dpi / 96d);
                string prefix = target.DeviceName;
                if (stable.Sample.Dpi != expected.Dpi)
                    violations.Add($"{prefix}: actual DPI {stable.Sample.Dpi}, expected {expected.Dpi}.");
                if (!target.Outer.Equals(expected.Outer))
                    violations.Add($"{prefix}: physical monitor rectangle does not match the authorized topology.");
                if (stable.Sample.Rect.Width != expectedPhysicalDiameter || stable.Sample.Rect.Height != expectedPhysicalDiameter)
                    violations.Add($"{prefix}: physical size {stable.Sample.Rect.Width}x{stable.Sample.Rect.Height}, expected {expectedPhysicalDiameter}x{expectedPhysicalDiameter}.");
                if (Math.Abs(stable.Sample.LogicalWidth - LogicalDiameter) > 0.75
                    || Math.Abs(stable.Sample.LogicalHeight - LogicalDiameter) > 0.75)
                    violations.Add($"{prefix}: logical size {stable.Sample.LogicalWidth:F3}x{stable.Sample.LogicalHeight:F3}, expected {LogicalDiameter}x{LogicalDiameter}.");
                if (stable.Sample.CaptionRegion.Width != stable.Sample.Rect.Width
                    || stable.Sample.CaptionRegion.Height != stable.Sample.Rect.Height)
                    violations.Add($"{prefix}: caption drag region did not follow the window size.");
                if (!SameGeometry(stable.Sample, afterHold))
                    violations.Add($"{prefix}: position, size, or DPI drifted during the one-second hold.");

                steps.Add(new
                {
                    target = target.DeviceName,
                    targetOuter = target.Outer,
                    targetWorkArea = target.Work,
                    movedVia = "Microsoft.UI.Windowing.AppWindow.Move",
                    syntheticDpiMessage = false,
                    requestedPosition = new { x = targetX, y = targetY },
                    moveStartedAtUtc = moveStarted,
                    stableAtUtc = stable.StableAtUtc,
                    settleMilliseconds = stable.SettleMilliseconds,
                    stableSample = stable.Sample,
                    holdMilliseconds = 1000,
                    afterHold,
                    holdDrift = Drift(stable.Sample, afterHold)
                });
            }
        }
        catch (Exception exception)
        {
            probeFailure = exception;
            violations.Add($"Probe exception: {exception.GetType().Name}: {exception.Message}");
        }

        object restoration;
        try
        {
            DateTimeOffset restoreStarted = DateTimeOffset.UtcNow;
            appWindow.Move(new PointInt32(originalRect.Left, originalRect.Top));
            _ = await WaitForStableAsync(
                handle,
                original.DeviceName,
                getCaptionRegionSize,
                TimeSpan.FromSeconds(8));
            if (!ReadWindowRect(handle).Equals(originalRect))
            {
                appWindow.Resize(new SizeInt32(originalRect.Width, originalRect.Height));
            }

            StableWindow restored = await WaitForStableAsync(
                handle,
                original.DeviceName,
                getCaptionRegionSize,
                TimeSpan.FromSeconds(8));
            await Task.Delay(TimeSpan.FromSeconds(1));
            WindowSample afterRestoreHold = ReadSample(handle, getCaptionRegionSize);
            bool exactRestore = restored.Sample.Rect.Equals(originalRect)
                && restored.Sample.Dpi == original.Dpi
                && SameGeometry(restored.Sample, afterRestoreHold);
            if (!exactRestore)
                violations.Add("The original position, size, DPI, or one-second restore hold was not preserved.");
            restoration = new
            {
                restoreStartedAtUtc = restoreStarted,
                stableAtUtc = restored.StableAtUtc,
                settleMilliseconds = restored.SettleMilliseconds,
                original,
                restored = restored.Sample,
                afterRestoreHold,
                restoreDrift = Drift(restored.Sample, afterRestoreHold),
                exactRestore
            };
        }
        catch (Exception exception)
        {
            violations.Add($"Restore exception: {exception.GetType().Name}: {exception.Message}");
            restoration = new
            {
                original,
                errorType = exception.GetType().FullName,
                error = exception.Message,
                exactRestore = false
            };
        }

        bool passed = violations.Count == 0 && steps.Count == ExpectedTopology.Length;
        object evidence = new
        {
            status = passed ? "DPI_ACCEPTANCE_PASS" : "DPI_ACCEPTANCE_FAIL",
            stage,
            atUtc = DateTimeOffset.UtcNow,
            processId = Environment.ProcessId,
            mainWindowHandle = handle.ToInt64(),
            dpiAwareness = "PerMonitorV2 (application manifest)",
            logicalDiameter = LogicalDiameter,
            requiredHoldMilliseconds = 1000,
            monitorEnumeration = "EnumDisplayMonitors/GetMonitorInfoW",
            dpiReadback = "GetDpiForWindow",
            movement = "AppWindow.Move only; no WM_DPICHANGED injection and no display-setting changes",
            monitors,
            expectedTopology = ExpectedTopology,
            steps,
            restoration,
            violations,
            exception = probeFailure is null ? null : new { type = probeFailure.GetType().FullName, probeFailure.Message }
        };
        File.WriteAllText(outputPath, JsonSerializer.Serialize(evidence, JsonOptions));

        if (!passed)
            throw new InvalidOperationException($"Real cross-DPI acceptance failed; see {outputPath}");
    }

    private static async Task<StableWindow> WaitForStableAsync(
        nint handle,
        string expectedDevice,
        Func<SizeInt32> getCaptionRegionSize,
        TimeSpan timeout)
    {
        Stopwatch elapsed = Stopwatch.StartNew();
        WindowSample? previous = null;
        int consecutive = 0;
        while (elapsed.Elapsed < timeout)
        {
            await Task.Delay(50);
            WindowSample current = ReadSample(handle, getCaptionRegionSize);
            bool targetReached = string.Equals(current.DeviceName, expectedDevice, StringComparison.OrdinalIgnoreCase);
            if (targetReached && previous is not null && SameGeometry(previous, current))
                consecutive++;
            else
                consecutive = 0;
            previous = current;
            if (consecutive >= 5)
                return new StableWindow(current, DateTimeOffset.UtcNow, elapsed.Elapsed.TotalMilliseconds);
        }

        throw new TimeoutException($"Window did not stabilize on {expectedDevice} within {timeout.TotalSeconds:F0} seconds.");
    }

    private static WindowSample ReadSample(nint handle, Func<SizeInt32> getCaptionRegionSize)
    {
        NativeRect rect = ReadWindowRect(handle);
        uint dpi = GetDpiForWindow(handle);
        nint monitor = MonitorFromWindow(handle, MonitorDefaultToNearest);
        MonitorRecord monitorRecord = ReadMonitor(monitor);
        SizeInt32 caption = getCaptionRegionSize();
        return new WindowSample(
            DateTimeOffset.UtcNow,
            monitorRecord.DeviceName,
            dpi,
            dpi / 96d,
            rect,
            rect.Width * 96d / dpi,
            rect.Height * 96d / dpi,
            new SizeRecord(caption.Width, caption.Height));
    }

    private static IReadOnlyList<MonitorRecord> EnumerateMonitors()
    {
        List<MonitorRecord> monitors = [];
        MonitorEnum callback = (monitor, _, _, _) =>
        {
            monitors.Add(ReadMonitor(monitor));
            return true;
        };
        if (!EnumDisplayMonitors(0, 0, callback, 0))
            throw new InvalidOperationException($"EnumDisplayMonitors failed with Win32 error {Marshal.GetLastWin32Error()}.");
        GC.KeepAlive(callback);
        return monitors.OrderBy(item => item.Outer.Left).ThenBy(item => item.Outer.Top).ToArray();
    }

    private static MonitorRecord ReadMonitor(nint monitor)
    {
        MonitorInfo info = new() { Size = (uint)Marshal.SizeOf<MonitorInfo>() };
        if (!GetMonitorInfo(monitor, ref info))
            throw new InvalidOperationException($"GetMonitorInfoW failed with Win32 error {Marshal.GetLastWin32Error()}.");
        return new MonitorRecord(info.DeviceName ?? string.Empty, info.Monitor, info.Work, (info.Flags & 1) != 0);
    }

    private static NativeRect ReadWindowRect(nint handle)
    {
        if (!GetWindowRect(handle, out NativeRect rect))
            throw new InvalidOperationException($"GetWindowRect failed with Win32 error {Marshal.GetLastWin32Error()}.");
        return rect;
    }

    private static bool SameGeometry(WindowSample left, WindowSample right) =>
        left.Dpi == right.Dpi
        && left.Rect.Equals(right.Rect)
        && left.CaptionRegion.Equals(right.CaptionRegion)
        && string.Equals(left.DeviceName, right.DeviceName, StringComparison.OrdinalIgnoreCase);

    private static object Drift(WindowSample before, WindowSample after) => new
    {
        left = after.Rect.Left - before.Rect.Left,
        top = after.Rect.Top - before.Rect.Top,
        width = after.Rect.Width - before.Rect.Width,
        height = after.Rect.Height - before.Rect.Height,
        dpi = (long)after.Dpi - before.Dpi,
        captionWidth = after.CaptionRegion.Width - before.CaptionRegion.Width,
        captionHeight = after.CaptionRegion.Height - before.CaptionRegion.Height
    };

    private sealed record ExpectedMonitor(string DeviceName, NativeRect Outer, uint Dpi);
    private sealed record MonitorRecord(string DeviceName, NativeRect Outer, NativeRect Work, bool IsPrimary);
    private sealed record SizeRecord(int Width, int Height);
    private sealed record WindowSample(
        DateTimeOffset AtUtc,
        string DeviceName,
        uint Dpi,
        double ScaleFactor,
        NativeRect Rect,
        double LogicalWidth,
        double LogicalHeight,
        SizeRecord CaptionRegion);
    private sealed record StableWindow(WindowSample Sample, DateTimeOffset StableAtUtc, double SettleMilliseconds);

    [StructLayout(LayoutKind.Sequential)]
    private readonly record struct NativeRect(int Left, int Top, int Right, int Bottom)
    {
        public int Width => Right - Left;
        public int Height => Bottom - Top;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct MonitorInfo
    {
        public uint Size;
        public NativeRect Monitor;
        public NativeRect Work;
        public uint Flags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
        public string? DeviceName;
    }

    private delegate bool MonitorEnum(nint monitor, nint deviceContext, nint monitorRect, nint data);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumDisplayMonitors(nint deviceContext, nint clipRect, MonitorEnum callback, nint data);

    [DllImport("user32.dll", EntryPoint = "GetMonitorInfoW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetMonitorInfo(nint monitor, ref MonitorInfo info);

    [DllImport("user32.dll")]
    private static extern nint MonitorFromWindow(nint window, uint flags);

    [DllImport("user32.dll")]
    private static extern uint GetDpiForWindow(nint window);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetWindowRect(nint window, out NativeRect rect);
}
