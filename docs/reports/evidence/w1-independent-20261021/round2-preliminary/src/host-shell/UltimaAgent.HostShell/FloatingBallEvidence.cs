using System.Runtime.InteropServices;
using System.Security.Cryptography;
using System.Text.Json;
using Microsoft.UI.Input;
using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml.Controls;
using Microsoft.Web.WebView2.Core;
using Windows.Graphics;
using Windows.Storage.Streams;

namespace UltimaAgent.HostShell;

internal static class FloatingBallEvidence
{
    private const int LogicalDiameter = 180;
    private const int WindowMargin = 32;
    private const int GwlStyle = -16;
    private const int GwlExStyle = -20;
    private const long WsCaption = 0x00C00000L;
    private const long WsExTopmost = 0x00000008L;
    private const uint WmNcLButtonDown = 0x00A1;
    private const int HtCaption = 2;
    private static int _captionRegionWidth;
    private static int _captionRegionHeight;
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

    private const string BallHtml = """
        <!doctype html>
        <html lang="zh-CN">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width,initial-scale=1">
          <style>
            * { box-sizing: border-box; user-select: none; }
            html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; }
            body { display: grid; place-items: center; background: #0F1420; }
            #ball { width: calc(100% - 14px); height: calc(100% - 14px); border-radius: 50%;
                    display: grid; place-items: center; position: relative; cursor: grab;
                    background: radial-gradient(circle at 35% 28%, #6B96FF 0, #3D7EFF 34%, #173A8A 72%, #0F1420 100%);
                    border: 1px solid rgba(230,234,242,.35);
                    box-shadow: inset 0 0 30px rgba(255,255,255,.12); }
            #ball:active { cursor: grabbing; }
            .mark { width: 43%; height: 43%; border-radius: 50%; display: grid; place-items: center;
                    color: #E6EAF2; font: 600 30px/1 "HarmonyOS Sans", sans-serif;
                    background: rgba(15,20,32,.35); border: 1px solid rgba(230,234,242,.22); }
            .status { position: absolute; width: 11px; height: 11px; right: 18%; bottom: 17%;
                      border-radius: 50%; background: #22C55E; box-shadow: 0 0 10px #22C55E; }
          </style>
        </head>
        <body>
          <main id="ball" role="button" aria-label="Ultima Agent 悬浮球，占位状态，可拖动" tabindex="0">
            <div class="mark">U</div><span class="status" aria-label="就绪"></span>
          </main>
          <script>
            document.getElementById('ball').addEventListener('pointerdown', event => {
              if (event.button === 0) {
                event.preventDefault();
                window.chrome.webview.postMessage('drag-start');
              }
            });
            window.chrome.webview.postMessage('floating-ball-ready');
          </script>
        </body>
        </html>
        """;

    public static void ConfigureWindow(AppWindow appWindow, nint handle)
    {
        if (appWindow.Presenter is not OverlappedPresenter presenter)
        {
            throw new InvalidOperationException("Floating ball requires OverlappedPresenter.");
        }

        presenter.SetBorderAndTitleBar(false, false);
        presenter.IsAlwaysOnTop = true;
        presenter.IsResizable = false;
        presenter.IsMaximizable = false;
        presenter.IsMinimizable = false;

        uint dpi = GetDpiForWindow(handle);
        double scale = dpi / 96d;
        int physicalDiameter = (int)Math.Round(LogicalDiameter * scale);
        DisplayArea display = DisplayArea.GetFromWindowId(appWindow.Id, DisplayAreaFallback.Nearest);
        RectInt32 work = display.WorkArea;
        int physicalMargin = (int)Math.Round(WindowMargin * scale);
        appWindow.MoveAndResize(new RectInt32(
            work.X + work.Width - physicalDiameter - physicalMargin,
            work.Y + work.Height - physicalDiameter - physicalMargin,
            physicalDiameter,
            physicalDiameter));
        InputNonClientPointerSource nonClient = InputNonClientPointerSource.GetForWindowId(appWindow.Id);
        void UpdateCaptionRegion()
        {
            SizeInt32 size = appWindow.Size;
            if (size.Width > 0 && size.Height > 0)
            {
                nonClient.SetRegionRects(NonClientRegionKind.Caption,
                    [new RectInt32(0, 0, size.Width, size.Height)]);
                Volatile.Write(ref _captionRegionWidth, size.Width);
                Volatile.Write(ref _captionRegionHeight, size.Height);
            }
        }
        UpdateCaptionRegion();
        appWindow.Changed += (_, change) =>
        {
            if (change.DidSizeChange) UpdateCaptionRegion();
        };
    }

    public static async Task RunAsync(WebView2 webView, AppWindow appWindow, nint handle)
    {
        string directory = Environment.GetEnvironmentVariable("ULTIMA_HOST_EVIDENCE_DIR")
            ?? throw new InvalidOperationException("ULTIMA_HOST_EVIDENCE_DIR is required for the floating-ball probe.");
        Directory.CreateDirectory(directory);
        string stage = Environment.GetEnvironmentVariable("ULTIMA_HOST_STAGE") ?? "t4";
        string screenshotPath = Environment.GetEnvironmentVariable("ULTIMA_HOST_FLOATINGBALL_CAPTURE_PATH")
            ?? Path.Combine(directory, $"{stage}-floating-ball.png");
        TaskCompletionSource<bool> navigation = NewCompletionSource<bool>();
        TaskCompletionSource<string> ready = NewCompletionSource<string>();

        await webView.EnsureCoreWebView2Async();
        CoreWebView2 core = webView.CoreWebView2;
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
            if (message == "floating-ball-ready")
            {
                ready.TrySetResult(message);
            }
            else if (message == "drag-start")
            {
                _ = ReleaseCapture();
                _ = SendMessage(handle, WmNcLButtonDown, HtCaption, 0);
            }
        };

        webView.NavigateToString(BallHtml);
        using CancellationTokenSource timeout = new(TimeSpan.FromSeconds(30));
        await navigation.Task.WaitAsync(timeout.Token);
        await ready.Task.WaitAsync(timeout.Token);

        if (Environment.GetEnvironmentVariable("ULTIMA_HOST_DPI_ACCEPTANCE") == "1")
        {
            await DpiAcceptanceEvidence.RunAsync(
                appWindow,
                handle,
                directory,
                stage,
                GetCaptionRegionSize);
        }

        using InMemoryRandomAccessStream preview = new();
        await core.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, preview);
        preview.Seek(0);
        using DataReader reader = new(preview.GetInputStreamAt(0));
        await reader.LoadAsync((uint)preview.Size);
        byte[] png = new byte[preview.Size];
        reader.ReadBytes(png);
        await File.WriteAllBytesAsync(screenshotPath, png);

        _ = GetWindowRect(handle, out NativeRect rect);
        uint dpi = GetDpiForWindow(handle);
        long style = GetWindowLongPtr(handle, GwlStyle).ToInt64();
        long exStyle = GetWindowLongPtr(handle, GwlExStyle).ToInt64();
        OverlappedPresenter presenter = (OverlappedPresenter)appWindow.Presenter;
        object evidence = new
        {
            status = "FLOATING_BALL_READY",
            stage,
            atUtc = DateTimeOffset.UtcNow,
            processId = Environment.ProcessId,
            mainWindowHandle = handle.ToInt64(),
            runtimeVersion = core.Environment.BrowserVersionString,
            presenter = "Overlapped",
            presenterHasBorder = presenter.HasBorder,
            presenterHasTitleBar = presenter.HasTitleBar,
            presenterIsAlwaysOnTop = presenter.IsAlwaysOnTop,
            borderless = !presenter.HasBorder && !presenter.HasTitleBar,
            topmost = presenter.IsAlwaysOnTop,
            nativeStyleHasCaption = (style & WsCaption) != 0,
            nativeExtendedStyleHasTopmost = (exStyle & WsExTopmost) != 0,
            resizable = presenter.IsResizable,
            logicalDiameter = LogicalDiameter,
            dpi,
            scaleFactor = dpi / 96d,
            rect = RectObject(rect),
            screenshotPath,
            screenshotSha256 = Convert.ToHexString(SHA256.HashData(png)).ToLowerInvariant(),
            dragProtocol = "Windows App SDK InputNonClientPointerSource Caption region"
        };
        File.WriteAllText(Path.Combine(directory, $"{stage}-floating-ball-ready.json"), JsonSerializer.Serialize(evidence, JsonOptions));
    }

    private static object RectObject(NativeRect rect) => new
    {
        rect.Left,
        rect.Top,
        rect.Right,
        rect.Bottom,
        width = rect.Right - rect.Left,
        height = rect.Bottom - rect.Top
    };

    private static TaskCompletionSource<T> NewCompletionSource<T>() =>
        new(TaskCreationOptions.RunContinuationsAsynchronously);

    private static SizeInt32 GetCaptionRegionSize() => new(
        Volatile.Read(ref _captionRegionWidth),
        Volatile.Read(ref _captionRegionHeight));

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool ReleaseCapture();

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern nint SendMessage(nint window, uint message, nint wParam, nint lParam);

    [DllImport("user32.dll")]
    private static extern uint GetDpiForWindow(nint window);

    [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW")]
    private static extern nint GetWindowLongPtr(nint window, int index);

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetWindowRect(nint window, out NativeRect rect);

    [StructLayout(LayoutKind.Sequential)]
    private struct NativeRect
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }
}
