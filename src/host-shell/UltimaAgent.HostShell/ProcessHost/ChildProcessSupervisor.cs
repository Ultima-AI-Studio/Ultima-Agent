using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text.Json;

namespace UltimaAgent.HostShell.ProcessHost;

internal interface IReadinessProbe
{
    Task<bool> IsAgentReadyAsync(CancellationToken cancellationToken);

    bool IsVoiceManaged();

    Task<bool> WaitForAgentReadyAsync(TimeSpan timeout, CancellationToken cancellationToken);

    Task<bool> WaitForVoiceManagedAsync(TimeSpan timeout, CancellationToken cancellationToken);

    Task<bool> WaitForWorkerReadyAsync(TimeSpan timeout, CancellationToken cancellationToken);

    Task ProbeProviderAsync(CancellationToken cancellationToken);
}

internal sealed class ChildProcessSupervisor
{
    private const uint CTRL_BREAK_EVENT = 1;
    private readonly object _sync = new();
    private readonly JobObjectManager _job;
    private readonly IReadinessProbe _probe;
    private readonly string _projectRoot;
    private readonly string _logPath;
    private readonly string _pidPath;
    private readonly List<Process> _children = [];

    public ChildProcessSupervisor(JobObjectManager job, IReadinessProbe probe, string projectRoot)
    {
        _job = job;
        _probe = probe;
        _projectRoot = projectRoot;
        string dataDirectory = Path.Combine(projectRoot, "Data", "logs");
        Directory.CreateDirectory(dataDirectory);
        _logPath = Path.Combine(dataDirectory, "process-host.log");
        _pidPath = Path.Combine(dataDirectory, "process-host-pids.json");
    }

    public IReadOnlyList<int> ChildProcessIds
    {
        get
        {
            lock (_sync)
            {
                return _children.Where(process => !process.HasExited).Select(process => process.Id).ToArray();
            }
        }
    }

    public async Task StartAsync(CancellationToken cancellationToken = default)
    {
        bool agentReady = await _probe.IsAgentReadyAsync(cancellationToken).ConfigureAwait(false);
        if (agentReady)
        {
            Log("agent_server adopted=existing");
        }

        if (_probe.IsVoiceManaged())
        {
            Log("voice-live adopted=existing");
        }
        else
        {
            StartAssigned(
                Path.Combine(_projectRoot, "tools", "venv-openjarvis", "Scripts", "python.exe"),
                "-X", "utf8", Path.Combine(_projectRoot, "src", "voice-next", "launch.py"));
        }

        if (!agentReady)
        {
            agentReady = await _probe.WaitForAgentReadyAsync(TimeSpan.FromSeconds(20), cancellationToken)
                .ConfigureAwait(false);
            if (agentReady)
            {
                Log("agent_server adopted=existing after voice launcher");
            }
            else
            {
                StartAssigned(
                    Path.Combine(_projectRoot, "tools", "venv-openjarvis", "Scripts", "python.exe"),
                    "-X", "utf8", Path.Combine(_projectRoot, "src", "brain", "agent_server.py"));
                agentReady = await _probe.WaitForAgentReadyAsync(TimeSpan.FromSeconds(20), cancellationToken)
                    .ConfigureAwait(false);
            }
        }

        if (agentReady)
        {
            await _probe.ProbeProviderAsync(cancellationToken).ConfigureAwait(false);
        }

        if (await _probe.WaitForVoiceManagedAsync(TimeSpan.FromSeconds(30), cancellationToken).ConfigureAwait(false))
        {
            await _probe.WaitForWorkerReadyAsync(TimeSpan.FromSeconds(120), cancellationToken).ConfigureAwait(false);
        }
    }

    public void StopAll(TimeSpan grace)
    {
        RequestVoiceStop();

        Process[] processes;
        lock (_sync)
        {
            processes = _children.ToArray();
        }

        foreach (Process process in processes.Where(process => !process.HasExited))
        {
            GenerateConsoleCtrlEvent(CTRL_BREAK_EVENT, (uint)process.Id);
        }

        Stopwatch wait = Stopwatch.StartNew();
        while (wait.Elapsed < grace && !IsVoiceStopped())
        {
            Thread.Sleep(100);
        }

        foreach (Process process in processes.Where(process => !process.HasExited))
        {
            TimeSpan remaining = grace - wait.Elapsed;
            if (remaining > TimeSpan.Zero)
            {
                process.WaitForExit((int)Math.Min(remaining.TotalMilliseconds, int.MaxValue));
            }
        }

        foreach (Process process in processes.Where(process => !process.HasExited))
        {
            process.Kill(entireProcessTree: false);
            process.WaitForExit(3000);
        }

        lock (_sync)
        {
            foreach (Process process in _children)
            {
                process.Dispose();
            }
            _children.Clear();
            File.Delete(_pidPath);
        }
    }

    private Process StartAssigned(string fileName, params string[] arguments)
    {
        var startInfo = new ProcessStartInfo(fileName)
        {
            UseShellExecute = false,
            CreateNoWindow = true,
            WorkingDirectory = _projectRoot,
        };
        foreach (string argument in arguments)
        {
            startInfo.ArgumentList.Add(argument);
        }

        Process process = Process.Start(startInfo)
            ?? throw new InvalidOperationException($"Unable to start {fileName}.");
        if (_job.IsActive && !_job.Assign(process.Handle)) // AssignProcessToJobObject immediately follows Process.Start.
        {
            int error = Marshal.GetLastWin32Error();
            process.Kill(entireProcessTree: false);
            process.Dispose();
            throw new Win32Exception(error, $"Unable to assign {fileName} to the process Job Object.");
        }

        lock (_sync)
        {
            _children.Add(process);
            WritePidFile();
        }
        Log($"started pid={process.Id} command={Path.GetFileName(fileName)} {string.Join(' ', arguments)}");
        return process;
    }

    private void RequestVoiceStop()
    {
        string dataDirectory = Path.Combine(_projectRoot, "data", "voice-next");
        string statusPath = Path.Combine(dataDirectory, "status.json");
        try
        {
            using JsonDocument status = JsonDocument.Parse(File.ReadAllText(statusPath));
            if (!status.RootElement.TryGetProperty("run_id", out JsonElement runId))
            {
                return;
            }

            string? value = runId.GetString();
            if (!string.IsNullOrWhiteSpace(value))
            {
                string request = JsonSerializer.Serialize(new { run_id = value });
                File.WriteAllText(Path.Combine(dataDirectory, "stop.request.json"), request);
            }
        }
        catch (IOException)
        {
        }
        catch (JsonException)
        {
        }
    }

    private void WritePidFile()
    {
        int[] processIds = _children.Where(process => !process.HasExited).Select(process => process.Id).ToArray();
        File.WriteAllText(_pidPath, JsonSerializer.Serialize(processIds));
    }

    private bool IsVoiceStopped()
    {
        try
        {
            string statusPath = Path.Combine(_projectRoot, "data", "voice-next", "status.json");
            using JsonDocument status = JsonDocument.Parse(File.ReadAllText(statusPath));
            return status.RootElement.TryGetProperty("state", out JsonElement state)
                && state.GetString() == "stopped";
        }
        catch (IOException)
        {
            return false;
        }
        catch (JsonException)
        {
            return false;
        }
    }

    private void Log(string message)
    {
        File.AppendAllText(_logPath, $"{DateTimeOffset.Now:O} {message}{Environment.NewLine}");
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GenerateConsoleCtrlEvent(uint dwCtrlEvent, uint dwProcessGroupId);
}
