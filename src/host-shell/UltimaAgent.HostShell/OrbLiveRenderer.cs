using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml.Controls;
using Microsoft.Web.WebView2.Core;
using Windows.Storage.Streams;
using Windows.UI;

namespace UltimaAgent.HostShell;

internal sealed record OrbLiveRendererOptions(bool EnableWarmRing, string StatusPath)
{
    public static OrbLiveRendererOptions FromEnvironment(string writeRoot)
    {
        bool enableWarmRing = !string.Equals(
            Environment.GetEnvironmentVariable("ULTIMA_HOST_WARM_RING"),
            "0",
            StringComparison.Ordinal);
        string? configuredStatusPath = Environment.GetEnvironmentVariable("ULTIMA_HOST_STATUS_FILE");
        string statusPath = string.IsNullOrWhiteSpace(configuredStatusPath)
            ? Path.Combine(writeRoot, "data", "voice-next", "status.json")
            : Path.GetFullPath(configuredStatusPath, writeRoot);
        return new OrbLiveRendererOptions(enableWarmRing, statusPath);
    }
}

/// <summary>
/// L4 A2 组合窗口上壳：毒液悬浮球常驻事件循环（brain → 壳 文件 IPC）。
///
/// 数据流（对齐 product-alignment-20261025 L4=A2）：
///   brain（InteractionOrbBridge.orb_command / OrbStateMachine.render_command）
///     → 写域 data/host/orb_command.json（seq 递增，HostOrbPusher）
///     → 本循环轮询（250ms），seq 变化即 PostWebMessageAsString 推送
///     → orb.html applyCommand（状态/emotionId/label/prompt/visual 全部消费）
///
/// 与验收探针模式（OrbBallRenderer）并存：本类是常驻事件循环，
/// 探针类是逐状态截图验收；两者共用 WebView2 桥协议。
/// </summary>
internal static class OrbLiveRenderer
{
    private const string ReadyMessage = "orb-ready";
    private const string DragMessage = "drag-start";
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

    private static readonly nint HWND_TOPMOST = new(-1);
    private const uint SWP_NOSIZE = 0x0001;
    private const uint SWP_NOMOVE = 0x0002;
    private const uint SWP_NOACTIVATE = 0x0010;

    [DllImport("user32.dll")]
    private static extern bool SetWindowPos(nint hWnd, nint hWndInsertAfter, int x, int y, int cx, int cy, uint uFlags);

    [DllImport("user32.dll")]
    private static extern uint GetDpiForWindow(nint window);

    public static async Task RunAsync(
        WebView2 webView,
        AppWindow appWindow,
        nint handle,
        string assetsRoot,
        string writeRoot,
        OrbLiveRendererOptions options)
    {
        string htmlPath = Path.Combine(assetsRoot, "Assets", "orb.html");
        if (!File.Exists(htmlPath))
        {
            throw new InvalidOperationException($"orb.html not found at {htmlPath}");
        }
        string commandFile = Path.Combine(writeRoot, "data", "host", "orb_command.json");
        Directory.CreateDirectory(Path.GetDirectoryName(commandFile)!);

        string? evidenceDir = Environment.GetEnvironmentVariable("ULTIMA_HOST_EVIDENCE_DIR");
        bool collectEvidence = !string.IsNullOrWhiteSpace(evidenceDir);
        if (collectEvidence)
        {
            Directory.CreateDirectory(evidenceDir!);
        }
        string? liveSecondsRaw = Environment.GetEnvironmentVariable("ULTIMA_HOST_LIVE_SECONDS");
        int liveSeconds = int.TryParse(liveSecondsRaw, out int parsed) && parsed > 0
            ? parsed
            : 0; // 0 = 常驻不限时（由用户关闭窗口结束）

        List<object> delivered = new();
        string logPath = Path.Combine(writeRoot, "data", "logs", "orb-live-loop.txt");
        Directory.CreateDirectory(Path.GetDirectoryName(logPath)!);
        void Log(string line) => File.AppendAllText(
            logPath, $"{DateTimeOffset.UtcNow:O} {line}{Environment.NewLine}");

        TaskCompletionSource<bool> navigation = NewCompletionSource<bool>();
        TaskCompletionSource<string> ready = NewCompletionSource<string>();

        await webView.EnsureCoreWebView2Async();
        CoreWebView2 core = webView.CoreWebView2;
        // 页面背景已透明；WebView2 控件默认白色背景会产生"白框"，改为透明。
        // 关键：WinUI3 控件属性未必转发到合成器，必须同时设控制器级透明，
        // 透明窗口（DWM backdrop transparent）下 WebView2 内容才正常合成。
        // 不设置 DefaultBackgroundColor（保持 WebView2 默认）。经验证：显式设置
        // 透明背景会使 WebView2 走透明合成路径、窗口透出桌面；页面（orb.html）
        // 球外全黑不透明会覆盖默认背景，配合黑底+Region 圆剪裁实现无壳。
        core.Settings.AreDevToolsEnabled = false;
        core.Settings.AreDefaultContextMenusEnabled = false;
        core.Settings.IsStatusBarEnabled = false;
        core.NavigationCompleted += (_, args) =>
        {
            if (args.IsSuccess) navigation.TrySetResult(true);
            else navigation.TrySetException(new InvalidOperationException($"Navigation failed: {args.WebErrorStatus}"));
        };
        core.WebMessageReceived += (sender, args) =>
        {
            string message = args.TryGetWebMessageAsString();
            if (message == ReadyMessage)
            {
                ready.TrySetResult(message);
            }
            else if (message == DragMessage)
            {
                // 页面 pointerdown → 宿主驱动窗口拖动（非激活窗拖动协议）
                _ = ReleaseCapture();
                _ = SendMessage(handle, 0x00A1, 2, 0); // WM_NCLBUTTONDOWN / HTCAPTION
            }
            else if (message.StartsWith("{\"kind\":\"orb-error\"", StringComparison.Ordinal))
            {
                Log($"PAGE_ERROR {message}");
            }
        };

        core.Navigate(new Uri(htmlPath).ToString());
        using CancellationTokenSource timeout = new(TimeSpan.FromSeconds(30));
        await navigation.Task.WaitAsync(timeout.Token);
        await ready.Task.WaitAsync(timeout.Token);
        Log("ORB_READY");

        // WebView2 初始化完成、DPI 已稳定（构造期 GetDpiForWindow 返回 96 导致
        // 父窗口 160px、WebView2 子窗口按 144 DPI 变 240px → 球被裁切）。
        // 此时按真实 DPI 重算父窗口为 240 物理 + Region 240 圆，与子窗口对齐。
        OrbWindowConfig.ResizeAndLocate(appWindow, handle);
        OrbWindowConfig.ApplyRegion(handle);
        Log($"RELAYOUT dpi={GetDpiForWindow(handle)}");

        // 启动基线证据（idle 渲染一帧后截图）
        if (collectEvidence)
        {
            await Task.Delay(500);
            byte[] png = await CapturePngAsync(core);
            await File.WriteAllBytesAsync(Path.Combine(evidenceDir!, "a2-live-idle.png"), png);
            Log($"EVIDENCE idle {png.Length}B sha256={Convert.ToHexString(SHA256.HashData(png)).ToLowerInvariant()}");
        }

        // ── 常驻事件循环：轮询 orb_command.json，seq 递增即推送 ──
        int lastSeq = 0;
        int pushedCount = 0;
        string? lastWarmState = null;
        int? lastWarmProgress = null;
        Stopwatch clock = Stopwatch.StartNew();
        bool hasDeliveredAny = false;
        while (true)
        {
            if (liveSeconds > 0 && clock.Elapsed.TotalSeconds >= liveSeconds)
            {
                break;
            }
            try
            {
                if (options.EnableWarmRing
                    && TryReadWarmState(options.StatusPath, out string warmState, out int warmProgress)
                    && (!string.Equals(warmState, lastWarmState, StringComparison.Ordinal)
                        || warmProgress != lastWarmProgress))
                {
                    lastWarmState = warmState;
                    lastWarmProgress = warmProgress;
                    string warmMessage = JsonSerializer.Serialize(new
                    {
                        kind = "orb-warm",
                        state = warmState,
                        progress = warmProgress,
                    });
                    core.PostWebMessageAsString(warmMessage);
                    Log($"WARM_PUSH state={warmState} progress={warmProgress}");
                    if (collectEvidence)
                    {
                        await Task.Delay(warmProgress >= 100 || warmState == "ready" ? 700 : 150);
                        byte[] png = await CapturePngAsync(core);
                        string pngPath = Path.Combine(evidenceDir!, $"warm-ring-{warmProgress}.png");
                        await File.WriteAllBytesAsync(pngPath, png);
                        Log($"EVIDENCE warm state={warmState} progress={warmProgress} {png.Length}B");
                    }
                }
                if (File.Exists(commandFile))
                {
                    string json = File.ReadAllText(commandFile);
                    using JsonDocument doc = JsonDocument.Parse(json);
                    JsonElement root = doc.RootElement;
                    if (root.TryGetProperty("seq", out JsonElement seqEl)
                        && seqEl.TryGetInt32(out int seq)
                        && seq > lastSeq)
                    {
                        lastSeq = seq;
                        core.PostWebMessageAsString(json);
                        pushedCount++;
                        hasDeliveredAny = true;
                        string state = root.TryGetProperty("state", out JsonElement s) ? s.GetString() ?? "" : "";
                        string prompt = root.TryGetProperty("prompt", out JsonElement p) ? p.GetString() ?? "" : "";
                        Log($"PUSH seq={seq} state={state} prompt={(prompt.Length > 60 ? prompt[..60] + "…" : prompt)}");
                        delivered.Add(new
                        {
                            seq,
                            state,
                            prompt,
                            atUtc = DateTimeOffset.UtcNow,
                        });
                        if (collectEvidence && pushedCount <= 3)
                        {
                            await Task.Delay(400); // 等渲染参数生效
                            byte[] png = await CapturePngAsync(core);
                            string pngPath = Path.Combine(evidenceDir!, $"a2-live-{pushedCount}-{state}.png");
                            await File.WriteAllBytesAsync(pngPath, png);
                            Log($"EVIDENCE state={state} {png.Length}B sha256={Convert.ToHexString(SHA256.HashData(png)).ToLowerInvariant()}");
                        }
                    }
                }
            }
            catch (Exception exception)
            {
                Log($"LOOP_ERROR {exception.Message}");
            }
            // 保持最前：周期提升 z 序（防止被其他置顶窗口如监控/系统检查盖住）
            if (clock.ElapsedMilliseconds % 1000 < 250)
            {
                _ = SetWindowPos(handle, HWND_TOPMOST, 0, 0, 0, 0,
                    SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE);
            }
            await Task.Delay(250);
        }

        // ── 终局证据 ──
        if (collectEvidence)
        {
            byte[] finalPng = await CapturePngAsync(core);
            string finalPath = Path.Combine(evidenceDir!, "a2-live-final.png");
            await File.WriteAllBytesAsync(finalPath, finalPng);
            object evidence = new
            {
                status = "ORB_LIVE_LOOP_DONE",
                mode = "ULTIMA_HOST_LIVE",
                atUtc = DateTimeOffset.UtcNow,
                processId = Environment.ProcessId,
                runtimeVersion = core.Environment.BrowserVersionString,
                renderer = "WebGL2 venom-orb (crazygl shader + 毒液形态参数, Apache-2.0)",
                htmlAsset = htmlPath,
                commandFile,
                pollMs = 250,
                deliveredCount = pushedCount,
                delivered,
                hasDeliveredAny,
                finalScreenshotPath = finalPath,
                finalScreenshotSha256 = Convert.ToHexString(SHA256.HashData(finalPng)).ToLowerInvariant(),
            };
            File.WriteAllText(
                Path.Combine(evidenceDir!, "a2-live.json"),
                JsonSerializer.Serialize(evidence, JsonOptions));
        }
        Log($"LOOP_END pushed={pushedCount}");
    }

    private static bool TryReadWarmState(string statusPath, out string state, out int progress)
    {
        state = string.Empty;
        progress = 0;
        try
        {
            if (!File.Exists(statusPath))
            {
                return false;
            }
            using JsonDocument document = JsonDocument.Parse(File.ReadAllText(statusPath));
            JsonElement root = document.RootElement;
            if (!root.TryGetProperty("state", out JsonElement stateElement)
                || stateElement.ValueKind != JsonValueKind.String
                || !root.TryGetProperty("warm_progress", out JsonElement progressElement)
                || !progressElement.TryGetInt32(out int parsedProgress))
            {
                return false;
            }
            state = stateElement.GetString() ?? string.Empty;
            progress = Math.Clamp(parsedProgress, 0, 100);
            return true;
        }
        catch (IOException)
        {
            return false;
        }
        catch (UnauthorizedAccessException)
        {
            return false;
        }
        catch (JsonException)
        {
            return false;
        }
    }

    private static async Task<byte[]> CapturePngAsync(CoreWebView2 core)
    {
        using InMemoryRandomAccessStream preview = new();
        await core.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, preview);
        preview.Seek(0);
        using DataReader reader = new(preview.GetInputStreamAt(0));
        await reader.LoadAsync((uint)preview.Size);
        byte[] png = new byte[preview.Size];
        reader.ReadBytes(png);
        return png;
    }

    private static TaskCompletionSource<T> NewCompletionSource<T>() =>
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool ReleaseCapture();

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern nint SendMessage(nint window, uint message, nint wParam, nint lParam);
}
