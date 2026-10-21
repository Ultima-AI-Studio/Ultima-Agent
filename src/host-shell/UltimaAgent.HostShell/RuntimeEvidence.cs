using System.Runtime.InteropServices;
using System.Text.Json;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Media.Imaging;
using Windows.Graphics.Imaging;
using Windows.Security.Cryptography;
using Windows.Storage.Streams;
using WinRT.Interop;

namespace UltimaAgent.HostShell;

internal static class RuntimeEvidence
{
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };
    private static readonly object EvidenceLock = new();
    private static int _hasFailures;
    public static bool HasFailures => Volatile.Read(ref _hasFailures) != 0;

    public static void WriteWindowReady(Window window)
    {
        if (HasFailures) return;
        nint handle = WindowNative.GetWindowHandle(window);
        _ = GetWindowRect(handle, out Rect rect);
        Write(new
        {
            status = "WINDOW_READY",
            stage = Environment.GetEnvironmentVariable("ULTIMA_HOST_STAGE") ?? "runtime",
            atUtc = DateTimeOffset.UtcNow,
            processId = Environment.ProcessId,
            processPath = Environment.ProcessPath,
            mainWindowHandle = handle.ToInt64(),
            title = window.Title,
            rect = new { rect.Left, rect.Top, rect.Right, rect.Bottom, width = rect.Right - rect.Left, height = rect.Bottom - rect.Top },
            packageType = "unpackaged",
            architectureBoundary = "terminal host only: IO, rendering, protocol"
        });
    }

    public static void WriteFailure(string code, Exception exception)
    {
        Interlocked.Exchange(ref _hasFailures, 1);
        Environment.ExitCode = 1;
        try
        {
            Write(new
            {
                status = "FAIL",
                code,
                atUtc = DateTimeOffset.UtcNow,
                errorType = exception.GetType().FullName,
                error = exception.Message,
                stack = exception.StackTrace
            }, isFailure: true);
        }
        catch (IOException) { }
        catch (UnauthorizedAccessException) { }
    }

    public static async Task CaptureElementAsync(UIElement element, string destination)
    {
        try
        {
            RenderTargetBitmap renderTarget = new();
            await renderTarget.RenderAsync(element);
            IBuffer pixels = await renderTarget.GetPixelsAsync();
            CryptographicBuffer.CopyToByteArray(pixels, out byte[] bytes);
            using InMemoryRandomAccessStream stream = new();
            BitmapEncoder encoder = await BitmapEncoder.CreateAsync(BitmapEncoder.PngEncoderId, stream);
            encoder.SetPixelData(
                BitmapPixelFormat.Bgra8,
                BitmapAlphaMode.Premultiplied,
                (uint)renderTarget.PixelWidth,
                (uint)renderTarget.PixelHeight,
                96,
                96,
                bytes);
            await encoder.FlushAsync();
            stream.Seek(0);
            using DataReader reader = new(stream.GetInputStreamAt(0));
            await reader.LoadAsync((uint)stream.Size);
            byte[] png = new byte[stream.Size];
            reader.ReadBytes(png);
            Directory.CreateDirectory(Path.GetDirectoryName(destination)!);
            await File.WriteAllBytesAsync(destination, png);
        }
        catch (Exception exception)
        {
            WriteFailure("CAPTURE_FAILED", exception);
        }
    }

    private static void Write(object record, bool isFailure = false)
    {
        string? directory = Environment.GetEnvironmentVariable("ULTIMA_HOST_EVIDENCE_DIR");
        if (string.IsNullOrWhiteSpace(directory)) return;
        string stage = Environment.GetEnvironmentVariable("ULTIMA_HOST_STAGE") ?? "runtime";
        lock (EvidenceLock)
        {
            Directory.CreateDirectory(directory);
            File.AppendAllText(Path.Combine(directory, $"{stage}-events.jsonl"),
                JsonSerializer.Serialize(record) + Environment.NewLine);
            if (isFailure)
            {
                string failurePath = Path.Combine(directory,
                    $"{stage}-failure-{DateTimeOffset.UtcNow:yyyyMMddTHHmmssfff}-{Guid.NewGuid():N}.json");
                using FileStream file = new(failurePath, FileMode.CreateNew, FileAccess.Write, FileShare.Read);
                JsonSerializer.Serialize(file, record, JsonOptions);
            }
            if (isFailure || !HasFailures)
                File.WriteAllText(Path.Combine(directory, $"{stage}-runtime.json"),
                    JsonSerializer.Serialize(record, JsonOptions));
        }
    }

    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetWindowRect(nint window, out Rect rect);

    [StructLayout(LayoutKind.Sequential)]
    private struct Rect
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }
}
