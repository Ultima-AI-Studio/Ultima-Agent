using System.Diagnostics;
using System.Net;
using System.Text.Json;

namespace UltimaAgent.HostShell.ProcessHost;

internal sealed class ReadinessProbe : IReadinessProbe, IDisposable
{
    public static readonly TimeSpan AgentTimeout = TimeSpan.FromSeconds(20);
    public static readonly TimeSpan VoiceManagedTimeout = TimeSpan.FromSeconds(30);
    public static readonly TimeSpan VoiceReadyTimeout = TimeSpan.FromSeconds(300);
    public static readonly TimeSpan TtsReadyTimeout = TimeSpan.FromSeconds(300);
    public static readonly TimeSpan WorkerReadyTimeout = TimeSpan.FromSeconds(120);
    public static readonly TimeSpan ProviderProbeTimeout = TimeSpan.FromSeconds(10);

    private readonly HttpClient _httpClient = new() { Timeout = Timeout.InfiniteTimeSpan };
    private readonly string _projectRoot;
    private readonly string _statusPath;
    private bool _windowActivated;

    public ReadinessProbe(string projectRoot)
    {
        _projectRoot = projectRoot;
        _statusPath = Path.Combine(projectRoot, "data", "voice-next", "status.json");
    }

    public bool IsWindowActivated => _windowActivated;

    public void MarkWindowActivated()
    {
        _windowActivated = true;
    }

    public async Task<bool> IsAgentReadyAsync(CancellationToken cancellationToken)
    {
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(AgentTimeout);
        try
        {
            using HttpResponseMessage response = await _httpClient
                .GetAsync("http://127.0.0.1:8756/health", timeout.Token)
                .ConfigureAwait(false);
            if (response.StatusCode != HttpStatusCode.OK)
            {
                return false;
            }

            using JsonDocument body = JsonDocument.Parse(await response.Content.ReadAsStringAsync(timeout.Token));
            return body.RootElement.TryGetProperty("provider", out _)
                && body.RootElement.TryGetProperty("model", out _);
        }
        catch (HttpRequestException)
        {
            return false;
        }
        catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
        {
            return false;
        }
        catch (JsonException)
        {
            return false;
        }
    }

    public bool IsVoiceManaged()
    {
        return TryReadStatus(out JsonDocument? status)
            && StatusSatisfies(status, root =>
                root.TryGetProperty("state", out JsonElement state)
                && !string.IsNullOrWhiteSpace(state.GetString())
                && state.GetString() is not "error" and not "stopped"
                && root.TryGetProperty("pid", out JsonElement pidValue)
                && pidValue.TryGetInt32(out int processId)
                && IsProcessAlive(processId));
    }

    public Task<bool> WaitForAgentReadyAsync(TimeSpan timeout, CancellationToken cancellationToken)
    {
        return WaitUntilAsync(() => IsAgentReadyAsync(cancellationToken), timeout, cancellationToken);
    }

    public Task<bool> WaitForVoiceManagedAsync(TimeSpan timeout, CancellationToken cancellationToken)
    {
        return WaitUntilAsync(() => Task.FromResult(IsVoiceManaged()), timeout, cancellationToken);
    }

    public Task<bool> WaitForVoiceReadyAsync(CancellationToken cancellationToken)
    {
        return WaitUntilAsync(
            () => Task.FromResult(StatusMatches(root =>
                root.TryGetProperty("state", out JsonElement state) && state.GetString() == "ready")),
            VoiceReadyTimeout,
            cancellationToken);
    }

    public Task<bool> WaitForTtsReadyAsync(CancellationToken cancellationToken)
    {
        return WaitUntilAsync(
            () => Task.FromResult(StatusMatches(root =>
                root.TryGetProperty("tts_backend", out JsonElement backend)
                && backend.GetString() == "cv3"
                && root.TryGetProperty("tts_cv3_pending", out JsonElement pending)
                && pending.ValueKind == JsonValueKind.False)),
            TtsReadyTimeout,
            cancellationToken);
    }

    public Task<bool> WaitForWorkerReadyAsync(TimeSpan timeout, CancellationToken cancellationToken)
    {
        return WaitUntilAsync(
            () => Task.FromResult(StatusMatches(root =>
            {
                if (!root.TryGetProperty("worker_ready", out JsonElement ready)
                    || ready.ValueKind != JsonValueKind.True
                    || !root.TryGetProperty("worker_pid", out JsonElement pidValue)
                    || !pidValue.TryGetInt32(out int workerPid))
                {
                    return false;
                }

                return IsProcessAlive(workerPid);
            })),
            timeout,
            cancellationToken);
    }

    public async Task ProbeProviderAsync(CancellationToken cancellationToken)
    {
        string logDirectory = Path.Combine(_projectRoot, "Data", "logs");
        Directory.CreateDirectory(logDirectory);
        string logPath = Path.Combine(logDirectory, "provider-probe.log");
        string script = "import json; from dataclasses import asdict; "
            + "from src.brain.slot_adapter import main_settings; "
            + "from src.brain.providers.probe import probe; "
            + "print(json.dumps(asdict(probe(main_settings(), timeout=10)), ensure_ascii=False))";
        var startInfo = new ProcessStartInfo(
            Path.Combine(_projectRoot, "tools", "venv-openjarvis", "Scripts", "python.exe"))
        {
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            WorkingDirectory = _projectRoot,
        };
        startInfo.ArgumentList.Add("-X");
        startInfo.ArgumentList.Add("utf8");
        startInfo.ArgumentList.Add("-c");
        startInfo.ArgumentList.Add(script);

        using Process process = Process.Start(startInfo)
            ?? throw new InvalidOperationException("Unable to start provider probe.");
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(ProviderProbeTimeout);
        string output = await process.StandardOutput.ReadToEndAsync(timeout.Token).ConfigureAwait(false);
        string error = await process.StandardError.ReadToEndAsync(timeout.Token).ConfigureAwait(false);
        await process.WaitForExitAsync(timeout.Token).ConfigureAwait(false);
        await File.WriteAllTextAsync(
            logPath,
            $"exit_code={process.ExitCode}{Environment.NewLine}{output}{error}",
            cancellationToken).ConfigureAwait(false);
    }

    public void Dispose()
    {
        _httpClient.Dispose();
    }

    private bool StatusMatches(Func<JsonElement, bool> predicate)
    {
        return TryReadStatus(out JsonDocument? status) && StatusSatisfies(status, predicate);
    }

    private bool TryReadStatus(out JsonDocument? status)
    {
        try
        {
            status = JsonDocument.Parse(File.ReadAllText(_statusPath));
            return true;
        }
        catch (IOException)
        {
            status = null;
            return false;
        }
        catch (JsonException)
        {
            status = null;
            return false;
        }
    }

    private static bool StatusSatisfies(JsonDocument? status, Func<JsonElement, bool> predicate)
    {
        using (status)
        {
            return status is not null && predicate(status.RootElement);
        }
    }

    private static bool IsProcessAlive(int processId)
    {
        try
        {
            using Process process = Process.GetProcessById(processId);
            return !process.HasExited;
        }
        catch (ArgumentException)
        {
            return false;
        }
    }

    private static async Task<bool> WaitUntilAsync(
        Func<Task<bool>> predicate,
        TimeSpan timeout,
        CancellationToken cancellationToken)
    {
        Stopwatch wait = Stopwatch.StartNew();
        while (wait.Elapsed < timeout)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (await predicate().ConfigureAwait(false))
            {
                return true;
            }
            await Task.Delay(200, cancellationToken).ConfigureAwait(false);
        }
        return false;
    }
}
