using System.Security.Cryptography;
using System.Text.Json;
using Microsoft.UI.Xaml.Controls;
using Microsoft.Web.WebView2.Core;
using Windows.Storage.Streams;

namespace UltimaAgent.HostShell;

internal static class WebViewEvidence
{
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

    private const string PlaceholderHtml = """
        <!doctype html>
        <html lang="zh-CN">
        <head>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width,initial-scale=1">
          <style>
            * { box-sizing: border-box; }
            html, body { width: 100%; height: 100%; margin: 0; }
            body { display: grid; place-items: center; background: #0F1420; color: #E6EAF2;
                   font-family: "HarmonyOS Sans SC", "Microsoft YaHei UI", sans-serif; }
            main { text-align: center; }
            h1 { margin: 0 0 8px; font: 600 32px/1.25 "HarmonyOS Sans", sans-serif; }
            p { margin: 0; color: #9AA3B8; font-size: 14px; }
            output { display: block; margin-top: 18px; color: #22C55E; font-size: 12px; }
          </style>
        </head>
        <body>
          <main>
            <h1>Ultima Agent</h1>
            <p id="state">WebView2 渲染就绪</p>
            <output id="roundtrip">等待宿主消息</output>
          </main>
          <script>
            window.chrome.webview.addEventListener('message', event => {
              const response = `web-received:${event.data}`;
              document.getElementById('roundtrip').textContent = response;
              window.chrome.webview.postMessage(response);
            });
            window.chrome.webview.postMessage('web-ready');
          </script>
        </body>
        </html>
        """;

    public static async Task RunAsync(WebView2 webView)
    {
        string directory = Environment.GetEnvironmentVariable("ULTIMA_HOST_EVIDENCE_DIR")
            ?? throw new InvalidOperationException("ULTIMA_HOST_EVIDENCE_DIR is required for the WebView2 probe.");
        Directory.CreateDirectory(directory);
        string stage = Environment.GetEnvironmentVariable("ULTIMA_HOST_STAGE") ?? "t3";
        string screenshotPath = Environment.GetEnvironmentVariable("ULTIMA_HOST_WEBVIEW_CAPTURE_PATH")
            ?? Path.Combine(directory, $"{stage}-webview-render.png");

        TaskCompletionSource<bool> navigation = NewCompletionSource<bool>();
        TaskCompletionSource<string> webReady = NewCompletionSource<string>();
        TaskCompletionSource<string> roundTrip = NewCompletionSource<string>();

        await webView.EnsureCoreWebView2Async();
        CoreWebView2 core = webView.CoreWebView2;
        core.Settings.AreDevToolsEnabled = false;
        core.Settings.AreDefaultContextMenusEnabled = false;
        core.Settings.IsStatusBarEnabled = false;
        core.NavigationCompleted += (_, args) =>
        {
            if (args.IsSuccess)
            {
                navigation.TrySetResult(true);
            }
            else
            {
                navigation.TrySetException(new InvalidOperationException($"Navigation failed: {args.WebErrorStatus}"));
            }
        };
        core.WebMessageReceived += (_, args) =>
        {
            string message = args.TryGetWebMessageAsString();
            if (message == "web-ready")
            {
                webReady.TrySetResult(message);
            }
            else if (message == "web-received:host-ping")
            {
                roundTrip.TrySetResult(message);
            }
        };

        webView.NavigateToString(PlaceholderHtml);
        using CancellationTokenSource timeout = new(TimeSpan.FromSeconds(30));
        await navigation.Task.WaitAsync(timeout.Token);
        string readyMessage = await webReady.Task.WaitAsync(timeout.Token);
        core.PostWebMessageAsString("host-ping");
        string responseMessage = await roundTrip.Task.WaitAsync(timeout.Token);

        string pageTitle = await core.ExecuteScriptAsync("document.querySelector('h1').textContent");
        string pageState = await core.ExecuteScriptAsync("document.getElementById('state').textContent");
        Directory.CreateDirectory(Path.GetDirectoryName(screenshotPath)!);
        using InMemoryRandomAccessStream preview = new();
        await core.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png, preview);
        preview.Seek(0);
        using DataReader reader = new(preview.GetInputStreamAt(0));
        await reader.LoadAsync((uint)preview.Size);
        byte[] png = new byte[preview.Size];
        reader.ReadBytes(png);
        await File.WriteAllBytesAsync(screenshotPath, png);

        string screenshotHash = Convert.ToHexString(await SHA256.HashDataAsync(File.OpenRead(screenshotPath))).ToLowerInvariant();
        object evidence = new
        {
            status = "WEBVIEW2_READY",
            stage,
            atUtc = DateTimeOffset.UtcNow,
            processId = Environment.ProcessId,
            runtimeVersion = core.Environment.BrowserVersionString,
            initialized = true,
            navigationSucceeded = true,
            source = "NavigateToString (offline placeholder)",
            pageTitle = JsonSerializer.Deserialize<string>(pageTitle),
            pageState = JsonSerializer.Deserialize<string>(pageState),
            webToHost = readyMessage,
            hostToWeb = "host-ping",
            roundTrip = responseMessage,
            screenshotPath,
            screenshotSha256 = screenshotHash,
            externalRequests = 0
        };
        File.WriteAllText(Path.Combine(directory, $"{stage}-webview.json"), JsonSerializer.Serialize(evidence, JsonOptions));
    }

    private static TaskCompletionSource<T> NewCompletionSource<T>() =>
        new(TaskCreationOptions.RunContinuationsAsynchronously);
}
