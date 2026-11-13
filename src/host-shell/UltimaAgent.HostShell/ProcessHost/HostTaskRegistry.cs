using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace UltimaAgent.HostShell.ProcessHost;

internal sealed class HostTaskRegistry
{
    public const string ManifestSchema = "ultimaagent-host-tasks/v1";
    public const string StateSchema = "ultimaagent-host-task-state/v1";

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true,
        WriteIndented = true,
    };

    private readonly object _sync = new();
    private readonly SemaphoreSlim _actionLock = new(1, 1);
    private readonly SemaphoreSlim _eventLock = new(1, 1);
    private readonly ChildProcessSupervisor _supervisor;
    private readonly string _projectRoot;
    private readonly string _statePath;
    private readonly string _eventsPath;
    private readonly string _logPath;
    private readonly Dictionary<string, HostTaskDefinition> _definitions;
    private readonly Dictionary<string, HostTaskRuntimeState> _states;

    public HostTaskRegistry(string projectRoot, ChildProcessSupervisor supervisor)
    {
        _projectRoot = Path.GetFullPath(projectRoot);
        _supervisor = supervisor;
        _statePath = Path.Combine(_projectRoot, "data", "host", "host-tasks-state.json");
        _eventsPath = Path.Combine(_projectRoot, "data", "logs", "guardian-events.jsonl");
        _logPath = Path.Combine(_projectRoot, "data", "logs", "guardian.log");

        string manifestPath = Path.Combine(_projectRoot, "config", "host-tasks.json");
        HostTaskManifest manifest = JsonSerializer.Deserialize<HostTaskManifest>(
                File.ReadAllText(manifestPath), JsonOptions)
            ?? throw new InvalidDataException("Host task manifest is empty.");
        if (!string.Equals(manifest.Schema, ManifestSchema, StringComparison.Ordinal))
        {
            throw new InvalidDataException($"Unsupported host task schema: {manifest.Schema}");
        }

        _definitions = manifest.Tasks.ToDictionary(task => task.Id, StringComparer.Ordinal);
        if (_definitions.Count != manifest.Tasks.Length)
        {
            throw new InvalidDataException("Host task ids must be unique.");
        }

        foreach (HostTaskDefinition definition in _definitions.Values)
        {
            ValidateDefinition(definition);
        }
        ValidateGuardianPolicy(_definitions.GetValueOrDefault("agent-server"));

        _states = _definitions.Values.ToDictionary(
            definition => definition.Id,
            definition => new HostTaskRuntimeState
            {
                TaskId = definition.Id,
                Name = definition.Name,
                Enabled = true,
                Status = "stopped",
                Pid = _supervisor.GetTrackedProcessId(definition.Id),
                RestartCount = 0,
            },
            StringComparer.Ordinal);
        RestorePersistedState();
        lock (_sync)
        {
            PersistLocked();
        }
    }

    public HostTaskStateDocument GetSnapshot()
    {
        lock (_sync)
        {
            return SnapshotLocked();
        }
    }

    public bool IsEnabled(string taskId)
    {
        lock (_sync)
        {
            return GetStateLocked(taskId).Enabled;
        }
    }

    public async Task<int> RestartAsync(
        string taskId,
        string reason,
        CancellationToken cancellationToken = default)
    {
        await _actionLock.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            lock (_sync)
            {
                if (!GetStateLocked(taskId).Enabled)
                {
                    throw new InvalidOperationException($"Host task is disabled: {taskId}");
                }
            }

            int processId = taskId switch
            {
                "agent-server" => _supervisor.RestartAgentServer(),
                "voice-launcher" => _supervisor.RestartVoiceLauncher(),
                _ => throw new InvalidOperationException($"No restart action is registered for {taskId}."),
            };

            lock (_sync)
            {
                HostTaskRuntimeState state = GetStateLocked(taskId);
                state.Pid = processId;
                state.RestartCount++;
                state.Status = "running";
                state.LastResult = reason;
                state.CooldownUntil = null;
                PersistLocked();
            }
            await AppendEventAsync(taskId, "restart", $"pid={processId} reason={reason}", cancellationToken)
                .ConfigureAwait(false);
            return processId;
        }
        finally
        {
            _actionLock.Release();
        }
    }

    public async Task SetEnabledAsync(
        string taskId,
        bool enabled,
        CancellationToken cancellationToken = default)
    {
        lock (_sync)
        {
            HostTaskRuntimeState state = GetStateLocked(taskId);
            state.Enabled = enabled;
            state.Status = enabled ? "stopped" : "disabled";
            state.LastResult = enabled ? "enabled" : "disabled";
            if (!enabled)
            {
                state.CooldownUntil = null;
            }
            PersistLocked();
        }
        await AppendEventAsync(taskId, "set_enabled", $"enabled={enabled.ToString().ToLowerInvariant()}", cancellationToken)
            .ConfigureAwait(false);
    }

    public async Task RecordProbeAsync(
        string taskId,
        bool healthy,
        string detail,
        CancellationToken cancellationToken = default)
    {
        lock (_sync)
        {
            HostTaskRuntimeState state = GetStateLocked(taskId);
            state.LastProbeAt = DateTimeOffset.Now;
            state.LastResult = detail;
            if (state.Enabled && state.Status != "cooldown")
            {
                state.Status = healthy ? "running" : "error";
            }
            if (!healthy && state.Pid is int processId && !IsProcessAlive(processId))
            {
                state.Pid = null;
            }
            PersistLocked();
        }
        await AppendEventAsync(taskId, healthy ? "probe_ok" : "probe_failed", detail, cancellationToken)
            .ConfigureAwait(false);
    }

    public async Task RecordCooldownAsync(
        string taskId,
        DateTimeOffset cooldownUntil,
        string detail,
        CancellationToken cancellationToken = default)
    {
        lock (_sync)
        {
            HostTaskRuntimeState state = GetStateLocked(taskId);
            state.Status = "cooldown";
            state.CooldownUntil = cooldownUntil;
            state.LastResult = detail;
            PersistLocked();
        }
        await AppendEventAsync(taskId, "cooldown", detail, cancellationToken).ConfigureAwait(false);
    }

    public async Task AppendEventAsync(
        string taskId,
        string kind,
        string detail,
        CancellationToken cancellationToken = default)
    {
        string directory = Path.GetDirectoryName(_eventsPath)
            ?? throw new InvalidOperationException("Guardian log directory is unavailable.");
        Directory.CreateDirectory(directory);
        string timestamp = DateTimeOffset.Now.ToString("O");
        string line = JsonSerializer.Serialize(new
        {
            ts = timestamp,
            task_id = taskId,
            kind,
            detail,
        });

        await _eventLock.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            await File.AppendAllTextAsync(_eventsPath, line + Environment.NewLine, cancellationToken)
                .ConfigureAwait(false);
            await File.AppendAllTextAsync(
                    _logPath,
                    $"{timestamp} task_id={taskId} kind={kind} detail={detail}{Environment.NewLine}",
                    cancellationToken)
                .ConfigureAwait(false);
        }
        finally
        {
            _eventLock.Release();
        }
    }

    private void ValidateDefinition(HostTaskDefinition definition)
    {
        if (string.IsNullOrWhiteSpace(definition.Id)
            || string.IsNullOrWhiteSpace(definition.Name)
            || string.IsNullOrWhiteSpace(definition.Executable))
        {
            throw new InvalidDataException("Host task id, name, and executable are required.");
        }
        _ = ResolveInsideProject(definition.Executable);
        foreach (string argument in definition.Arguments.Where(value => value.EndsWith(".py", StringComparison.OrdinalIgnoreCase)))
        {
            _ = ResolveInsideProject(argument);
        }
    }

    private static void ValidateGuardianPolicy(HostTaskDefinition? definition)
    {
        if (definition is null
            || definition.Restart.Policy != "guardian"
            || definition.Restart.CheckIntervalSeconds != 20
            || definition.Restart.FailLimit != 3
            || definition.Restart.CooldownSeconds != 300)
        {
            throw new InvalidDataException("agent-server must use the frozen guardian policy 20/3/300.");
        }
    }

    private string ResolveInsideProject(string relativePath)
    {
        if (Path.IsPathRooted(relativePath))
        {
            throw new InvalidDataException($"Host task paths must be project-relative: {relativePath}");
        }
        string resolved = Path.GetFullPath(Path.Combine(_projectRoot, relativePath));
        string prefix = _projectRoot.TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar)
            + Path.DirectorySeparatorChar;
        if (!resolved.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidDataException($"Host task path escapes the project root: {relativePath}");
        }
        return resolved;
    }

    private void RestorePersistedState()
    {
        try
        {
            HostTaskStateDocument? persisted = JsonSerializer.Deserialize<HostTaskStateDocument>(
                File.ReadAllText(_statePath), JsonOptions);
            if (persisted?.Schema != StateSchema)
            {
                return;
            }
            foreach (HostTaskRuntimeState prior in persisted.Tasks)
            {
                if (_states.TryGetValue(prior.TaskId, out HostTaskRuntimeState? state))
                {
                    state.Enabled = prior.Enabled;
                    state.RestartCount = prior.RestartCount;
                }
            }
        }
        catch (IOException)
        {
        }
        catch (JsonException)
        {
        }
    }

    private HostTaskRuntimeState GetStateLocked(string taskId)
    {
        return _states.TryGetValue(taskId, out HostTaskRuntimeState? state)
            ? state
            : throw new KeyNotFoundException($"Unknown host task: {taskId}");
    }

    private HostTaskStateDocument SnapshotLocked()
    {
        return new HostTaskStateDocument
        {
            Schema = StateSchema,
            GeneratedAt = DateTimeOffset.Now,
            Tasks = _states.Values
                .OrderBy(state => state.TaskId, StringComparer.Ordinal)
                .Select(state => state.Copy())
                .ToArray(),
        };
    }

    private void PersistLocked()
    {
        string directory = Path.GetDirectoryName(_statePath)
            ?? throw new InvalidOperationException("Host task state directory is unavailable.");
        Directory.CreateDirectory(directory);
        string temporary = _statePath + ".tmp";
        File.WriteAllText(temporary, JsonSerializer.Serialize(SnapshotLocked(), JsonOptions));
        File.Move(temporary, _statePath, overwrite: true);
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
}

internal sealed class HostTaskManifest
{
    [JsonPropertyName("schema")]
    public string Schema { get; init; } = string.Empty;

    [JsonPropertyName("tasks")]
    public HostTaskDefinition[] Tasks { get; init; } = [];
}

internal sealed class HostTaskDefinition
{
    [JsonPropertyName("id")]
    public string Id { get; init; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("executable")]
    public string Executable { get; init; } = string.Empty;

    [JsonPropertyName("arguments")]
    public string[] Arguments { get; init; } = [];

    [JsonPropertyName("restart")]
    public HostTaskRestartPolicy Restart { get; init; } = new();
}

internal sealed class HostTaskRestartPolicy
{
    [JsonPropertyName("policy")]
    public string Policy { get; init; } = string.Empty;

    [JsonPropertyName("check_interval_seconds")]
    public int? CheckIntervalSeconds { get; init; }

    [JsonPropertyName("fail_limit")]
    public int? FailLimit { get; init; }

    [JsonPropertyName("cooldown_seconds")]
    public int? CooldownSeconds { get; init; }
}

internal sealed class HostTaskStateDocument
{
    [JsonPropertyName("schema")]
    public string Schema { get; init; } = HostTaskRegistry.StateSchema;

    [JsonPropertyName("generated_at")]
    public DateTimeOffset GeneratedAt { get; init; }

    [JsonPropertyName("tasks")]
    public HostTaskRuntimeState[] Tasks { get; init; } = [];
}

internal sealed class HostTaskRuntimeState
{
    [JsonPropertyName("task_id")]
    public string TaskId { get; init; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; init; } = string.Empty;

    [JsonPropertyName("enabled")]
    public bool Enabled { get; set; }

    [JsonPropertyName("status")]
    public string Status { get; set; } = "stopped";

    [JsonPropertyName("pid")]
    public int? Pid { get; set; }

    [JsonPropertyName("restart_count")]
    public int RestartCount { get; set; }

    [JsonPropertyName("last_probe_at")]
    public DateTimeOffset? LastProbeAt { get; set; }

    [JsonPropertyName("last_result")]
    public string? LastResult { get; set; }

    [JsonPropertyName("cooldown_until")]
    public DateTimeOffset? CooldownUntil { get; set; }

    public HostTaskRuntimeState Copy()
    {
        return new HostTaskRuntimeState
        {
            TaskId = TaskId,
            Name = Name,
            Enabled = Enabled,
            Status = Status,
            Pid = Pid,
            RestartCount = RestartCount,
            LastProbeAt = LastProbeAt,
            LastResult = LastResult,
            CooldownUntil = CooldownUntil,
        };
    }
}
