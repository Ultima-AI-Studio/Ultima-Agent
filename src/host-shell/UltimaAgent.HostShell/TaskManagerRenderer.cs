using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Microsoft.UI.Xaml.Controls;
using Microsoft.Web.WebView2.Core;
using UltimaAgent.HostShell.ProcessHost;
using Windows.Storage.Streams;

namespace UltimaAgent.HostShell;

internal static class TaskManagerRenderer
{
    private const string ReadyKind = "ultima.taskmanager.ready";
    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

    public static async Task RunAsync(
        WebView2 webView,
        HostTaskRegistry registry,
        string assetsRoot,
        string writeRoot)
    {
        string root = Path.GetFullPath(writeRoot);
        string htmlPath = Path.Combine(assetsRoot, "Assets", "taskmanager.html");
        if (!File.Exists(htmlPath))
        {
            throw new InvalidOperationException($"taskmanager.html not found at {htmlPath}");
        }

        string? stateOverrideRaw = Environment.GetEnvironmentVariable("ULTIMA_HOST_TASK_STATE_FILE");
        string? stateOverride = string.IsNullOrWhiteSpace(stateOverrideRaw)
            ? null
            : RequireInsideRoot(stateOverrideRaw, root, "task manager state override");
        string? actionFileRaw = Environment.GetEnvironmentVariable("ULTIMA_HOST_TASK_MANAGER_ACTION_FILE");
        string? actionFile = string.IsNullOrWhiteSpace(actionFileRaw)
            ? null
            : RequireInsideRoot(actionFileRaw, root, "task manager action file");
        string? evidenceRaw = Environment.GetEnvironmentVariable("ULTIMA_HOST_EVIDENCE_DIR");
        string? evidenceDir = string.IsNullOrWhiteSpace(evidenceRaw)
            ? null
            : RequireInsideRoot(evidenceRaw, root, "task manager evidence");
        if (evidenceDir is not null)
        {
            Directory.CreateDirectory(evidenceDir);
        }

        int liveSeconds = int.TryParse(
            Environment.GetEnvironmentVariable("ULTIMA_HOST_TASK_MANAGER_SECONDS"),
            out int parsedSeconds) && parsedSeconds > 0 ? parsedSeconds : 0;
        string logPath = Path.Combine(root, "data", "logs", "taskmanager-events.log");
        Directory.CreateDirectory(Path.GetDirectoryName(logPath)!);
        void Log(string value) => File.AppendAllText(
            logPath, $"{DateTimeOffset.Now:O} {value}{Environment.NewLine}");

        TaskCompletionSource<bool> navigation = NewCompletionSource<bool>();
        TaskCompletionSource<bool> ready = NewCompletionSource<bool>();
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
                navigation.TrySetException(
                    new InvalidOperationException($"Task manager navigation failed: {args.WebErrorStatus}"));
            }
        };
        core.WebMessageReceived += async (_sender, args) =>
        {
            try
            {
                using JsonDocument document = JsonDocument.Parse(args.WebMessageAsJson);
                JsonElement message = document.RootElement;
                string kind = GetRequiredString(message, "kind");
                if (kind == ReadyKind)
                {
                    ready.TrySetResult(true);
                    return;
                }
                if (kind is not ("restart" or "set-enabled"))
                {
                    return;
                }
                string taskId = GetRequiredString(message, "task_id");
                bool? enabled = kind == "set-enabled"
                    ? message.GetProperty("enabled").GetBoolean()
                    : null;
                Log($"ACTION_RECEIVED kind={kind} task_id={taskId} enabled={enabled}");
                if (kind == "restart")
                {
                    await Task.Run(() => registry.RestartAsync(taskId, "taskmanager manual restart"));
                }
                else
                {
                    await Task.Run(() => registry.SetEnabledAsync(taskId, enabled!.Value));
                }
                core.PostWebMessageAsJson(JsonSerializer.Serialize(new
                {
                    kind = "ultima.taskmanager.action-result",
                    action = kind,
                    task_id = taskId,
                    enabled,
                    ok = true,
                }));
                string snapshot = ReadSnapshotJson(registry, stateOverride);
                core.PostWebMessageAsJson(snapshot);
                Log($"ACTION_OK kind={kind} task_id={taskId} enabled={enabled}");
                if (evidenceDir is not null)
                {
                    await Task.Delay(350);
                    string suffix = enabled is null ? "" : $"-{enabled.Value.ToString().ToLowerInvariant()}";
                    string screenshot = Path.Combine(
                        evidenceDir,
                        $"taskmanager-action-{kind}{suffix}-{SafeName(taskId)}.png");
                    await File.WriteAllBytesAsync(screenshot, await CapturePngAsync(core));
                    Log($"ACTION_SCREENSHOT kind={kind} task_id={taskId} path={screenshot}");
                }
            }
            catch (Exception exception)
            {
                Log($"ACTION_ERROR type={exception.GetType().Name} message={exception.Message}");
                core.PostWebMessageAsJson(JsonSerializer.Serialize(new
                {
                    kind = "ultima.taskmanager.action-result",
                    ok = false,
                    message = exception.Message,
                }));
            }
        };

        core.Navigate(new Uri(htmlPath).AbsoluteUri);
        using CancellationTokenSource timeout = new(TimeSpan.FromSeconds(30));
        await navigation.Task.WaitAsync(timeout.Token);
        await ready.Task.WaitAsync(timeout.Token);
        Log("TASKMANAGER_READY");

        string previousDigest = string.Empty;
        int captureCount = 0;
        int lastActionSequence = 0;
        Stopwatch runtime = Stopwatch.StartNew();
        Stopwatch fallback = Stopwatch.StartNew();
        while (liveSeconds == 0 || runtime.Elapsed.TotalSeconds < liveSeconds)
        {
            try
            {
                string snapshot = ReadSnapshotJson(registry, stateOverride);
                string digest = ComputeStateDigest(snapshot);
                bool changed = !string.Equals(digest, previousDigest, StringComparison.Ordinal);
                if (changed || fallback.Elapsed >= TimeSpan.FromSeconds(1))
                {
                    core.PostWebMessageAsJson(snapshot);
                    previousDigest = digest;
                    fallback.Restart();
                    Log($"SNAPSHOT_PUSH changed={changed.ToString().ToLowerInvariant()} sha256={digest.ToLowerInvariant()}");
                    if (changed && evidenceDir is not null)
                    {
                        await Task.Delay(300);
                        captureCount++;
                        string status = GetFirstStatus(snapshot);
                        string screenshot = Path.Combine(
                            evidenceDir,
                            $"taskmanager-state-{captureCount}-{SafeName(status)}.png");
                        byte[] png = await CapturePngAsync(core);
                        await File.WriteAllBytesAsync(screenshot, png);
                        Log($"STATE_SCREENSHOT count={captureCount} status={status} path={screenshot}");
                    }
                }

                if (actionFile is not null && File.Exists(actionFile))
                {
                    using JsonDocument actionDocument = JsonDocument.Parse(await File.ReadAllTextAsync(actionFile));
                    JsonElement action = actionDocument.RootElement;
                    int sequence = action.GetProperty("seq").GetInt32();
                    if (sequence > lastActionSequence)
                    {
                        string kind = GetRequiredString(action, "kind");
                        string taskId = GetRequiredString(action, "task_id");
                        bool? enabled = action.TryGetProperty("enabled", out JsonElement enabledElement)
                            ? enabledElement.GetBoolean()
                            : null;
                        string script =
                            $"window.__ultimaTaskManagerTestClick({JsonSerializer.Serialize(kind)},"
                            + $"{JsonSerializer.Serialize(taskId)},{JsonSerializer.Serialize(enabled)});";
                        string result = await core.ExecuteScriptAsync(script);
                        if (string.Equals(result, "true", StringComparison.OrdinalIgnoreCase))
                        {
                            lastActionSequence = sequence;
                            Log($"TEST_CLICK seq={sequence} kind={kind} task_id={taskId} enabled={enabled}");
                        }
                    }
                }
            }
            catch (Exception exception) when (exception is IOException or JsonException)
            {
                core.PostWebMessageAsJson(JsonSerializer.Serialize(new
                {
                    kind = "ultima.taskmanager.error",
                    message = "任务状态暂时不可读，正在重试。",
                }));
                Log($"SNAPSHOT_ERROR type={exception.GetType().Name} message={exception.Message}");
            }
            await Task.Delay(100);
        }
        Log("TASKMANAGER_LOOP_END");
    }

    private static string ReadSnapshotJson(HostTaskRegistry registry, string? stateOverride)
    {
        string json = stateOverride is null
            ? JsonSerializer.Serialize(registry.GetSnapshot(), JsonOptions)
            : File.ReadAllText(stateOverride);
        using JsonDocument document = JsonDocument.Parse(json);
        JsonElement root = document.RootElement;
        if (!root.TryGetProperty("schema", out JsonElement schema)
            || schema.GetString() != HostTaskRegistry.StateSchema
            || !root.TryGetProperty("tasks", out JsonElement tasks)
            || tasks.ValueKind != JsonValueKind.Array)
        {
            throw new JsonException("Task manager snapshot does not match the host task state schema.");
        }
        return json;
    }

    private static string GetFirstStatus(string json)
    {
        using JsonDocument document = JsonDocument.Parse(json);
        JsonElement tasks = document.RootElement.GetProperty("tasks");
        return tasks.GetArrayLength() == 0
            ? "empty"
            : tasks[0].GetProperty("status").GetString() ?? "unknown";
    }

    private static string ComputeStateDigest(string json)
    {
        using JsonDocument document = JsonDocument.Parse(json);
        string taskState = document.RootElement.GetProperty("tasks").GetRawText();
        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(taskState)));
    }

    private static string GetRequiredString(JsonElement value, string propertyName)
    {
        if (!value.TryGetProperty(propertyName, out JsonElement property)
            || property.ValueKind != JsonValueKind.String
            || string.IsNullOrWhiteSpace(property.GetString()))
        {
            throw new JsonException($"Missing string property: {propertyName}");
        }
        return property.GetString()!;
    }

    private static string RequireInsideRoot(string value, string root, string label)
    {
        string resolved = Path.GetFullPath(value, root);
        string prefix = root.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
            + Path.DirectorySeparatorChar;
        if (!resolved.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException($"{label} must stay inside {root}");
        }
        return resolved;
    }

    private static string SafeName(string value)
    {
        char[] invalid = Path.GetInvalidFileNameChars();
        return new string(value.Select(character => invalid.Contains(character) ? '-' : character).ToArray());
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
}
