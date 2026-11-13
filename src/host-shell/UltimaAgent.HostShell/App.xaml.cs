using System.Diagnostics;
using System.Text.Json;
using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Media;
using UltimaAgent.HostShell.ProcessHost;

namespace UltimaAgent.HostShell;

public partial class App : Application
{
    private Window? _mainWindow;
    private DispatcherQueueTimer? _exitTimer;
    private JobObjectManager? _jobObject;
    private ReadinessProbe? _readinessProbe;
    private ChildProcessSupervisor? _processSupervisor;
    private HostTaskRegistry? _hostTaskRegistry;
    private GuardianService? _guardianService;
    private CancellationTokenSource? _processHostCancellation;
    private bool _windowActivated;
    private bool _processHostStopped;
    private readonly object _startupTimingLock = new();
    private readonly Stopwatch _startupStopwatch = new();
    private Task _startupTimingWriteTail = Task.CompletedTask;
    private CancellationTokenSource? _startupTimingCancellation;
    private DateTimeOffset _startupT0;
    private bool _startupUsesProcessStart;
    private long? _windowVisibleMilliseconds;
    private long? _firstFrameMilliseconds;
    private long? _voiceReadyMilliseconds;
    private bool _startupTimingAppended;

    public App()
    {
        InitializeComponent();
        UnhandledException += (_, args) =>
        {
            args.Handled = true;
            HandleUnhandledException(args.Exception);
        };
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        InitializeStartupTiming();
        _mainWindow = new MainWindow();
        _mainWindow.Activated += (_, _) =>
        {
            _windowActivated = true;
            _readinessProbe?.MarkWindowActivated();
            RecordWindowVisible();
        };
        _mainWindow.Closed += (_, _) => StopProcessHost();
        CompositionTarget.Rendering += OnFirstFrameRendering;
        _mainWindow.Activate();
        _mainWindow.DispatcherQueue.TryEnqueue(() => RuntimeEvidence.WriteWindowReady(_mainWindow));
        try
        {
            string projectRoot = Environment.GetEnvironmentVariable("ULTIMA_PROJECT_ROOT")
                ?? Directory.GetCurrentDirectory();
            AutostartEntry.Apply(projectRoot);
        }
        catch (Exception exception)
        {
            RuntimeEvidence.WriteFailure("AUTOSTART_FAILED", exception);
        }

        if (int.TryParse(Environment.GetEnvironmentVariable("ULTIMA_HOST_AUTO_EXIT_MS"), out int milliseconds)
            && milliseconds > 0)
        {
            _exitTimer = _mainWindow.DispatcherQueue.CreateTimer();
            _exitTimer.Interval = TimeSpan.FromMilliseconds(milliseconds);
            _exitTimer.IsRepeating = false;
            _exitTimer.Tick += (_, _) => _mainWindow.Close();
            _exitTimer.Start();
        }

        if (UseProcessHost())
        {
            StartProcessHost();
        }
        else if (CrashSelfRequested())
        {
            QueueCrashInjection();
        }
        _startupTimingCancellation = new CancellationTokenSource();
        _ = TrackVoiceReadyAsync(_startupTimingCancellation.Token);
    }

    private void InitializeStartupTiming()
    {
        _startupStopwatch.Restart();
        try
        {
            using Process process = Process.GetCurrentProcess();
            _startupT0 = new DateTimeOffset(process.StartTime);
            _startupUsesProcessStart = true;
        }
        catch (Exception exception) when (exception is InvalidOperationException or System.ComponentModel.Win32Exception)
        {
            _startupT0 = DateTimeOffset.Now;
            _startupUsesProcessStart = false;
        }
        lock (_startupTimingLock)
        {
            QueueStartupTimingWriteLocked(append: false);
        }
    }

    private void RecordWindowVisible()
    {
        lock (_startupTimingLock)
        {
            if (_windowVisibleMilliseconds is not null)
            {
                return;
            }
            _windowVisibleMilliseconds = ElapsedStartupMilliseconds();
            QueueStartupTimingWriteLocked(append: false);
        }
    }

    private void OnFirstFrameRendering(object? sender, object args)
    {
        CompositionTarget.Rendering -= OnFirstFrameRendering;
        lock (_startupTimingLock)
        {
            if (_firstFrameMilliseconds is not null)
            {
                return;
            }
            _firstFrameMilliseconds = ElapsedStartupMilliseconds();
            QueueStartupTimingWriteLocked(append: false);
        }
    }

    private async Task TrackVoiceReadyAsync(CancellationToken cancellationToken)
    {
        string projectRoot = Environment.GetEnvironmentVariable("ULTIMA_PROJECT_ROOT")
            ?? Directory.GetCurrentDirectory();
        string statusPath = Path.Combine(projectRoot, "data", "voice-next", "status.json");
        try
        {
            while (!cancellationToken.IsCancellationRequested)
            {
                if (IsVoiceReady(statusPath))
                {
                    lock (_startupTimingLock)
                    {
                        if (_voiceReadyMilliseconds is null)
                        {
                            _voiceReadyMilliseconds = ElapsedStartupMilliseconds();
                            QueueStartupTimingWriteLocked(append: true);
                        }
                    }
                    return;
                }
                await Task.Delay(100, cancellationToken).ConfigureAwait(false);
            }
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
        }
    }

    private static bool IsVoiceReady(string statusPath)
    {
        try
        {
            using JsonDocument document = JsonDocument.Parse(File.ReadAllText(statusPath));
            JsonElement root = document.RootElement;
            bool readyState = root.TryGetProperty("state", out JsonElement state)
                && state.GetString() == "ready";
            bool fullyWarm = root.TryGetProperty("warm_progress", out JsonElement progress)
                && progress.TryGetInt32(out int value)
                && value == 100;
            bool voiceProcessAlive = root.TryGetProperty("pid", out JsonElement processId)
                && processId.TryGetInt32(out int pid)
                && IsProcessAlive(pid);
            return (readyState || fullyWarm) && voiceProcessAlive;
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

    private long ElapsedStartupMilliseconds()
    {
        double milliseconds = _startupUsesProcessStart
            ? (DateTimeOffset.Now - _startupT0).TotalMilliseconds
            : _startupStopwatch.Elapsed.TotalMilliseconds;
        return Math.Max(1, (long)Math.Round(milliseconds));
    }

    private void QueueStartupTimingWriteLocked(bool append)
    {
        if (append && _startupTimingAppended)
        {
            return;
        }
        if (append)
        {
            _startupTimingAppended = true;
        }
        var record = new Dictionary<string, object?>
        {
            ["t0_iso"] = _startupT0.ToString("O"),
            ["window_visible_ms"] = _windowVisibleMilliseconds,
            ["first_frame_ms"] = _firstFrameMilliseconds,
            ["voice_ready_ms"] = _voiceReadyMilliseconds,
            ["pid"] = Environment.ProcessId,
            ["build"] = typeof(App).Assembly.GetName().Version?.ToString() ?? "unknown",
        };
        _startupTimingWriteTail = _startupTimingWriteTail.ContinueWith(
            _ => WriteStartupTimingAsync(record, append),
            CancellationToken.None,
            TaskContinuationOptions.None,
            TaskScheduler.Default).Unwrap();
    }

    private static async Task WriteStartupTimingAsync(Dictionary<string, object?> record, bool append)
    {
        string projectRoot = Environment.GetEnvironmentVariable("ULTIMA_PROJECT_ROOT")
            ?? Directory.GetCurrentDirectory();
        string directory = Path.Combine(projectRoot, "data", "logs");
        Directory.CreateDirectory(directory);
        string json = JsonSerializer.Serialize(record);
        string currentPath = Path.Combine(directory, "startup-timing.json");
        string temporaryPath = currentPath + ".tmp";
        await File.WriteAllTextAsync(temporaryPath, json + Environment.NewLine).ConfigureAwait(false);
        File.Move(temporaryPath, currentPath, overwrite: true);
        if (append)
        {
            await File.AppendAllTextAsync(
                Path.Combine(directory, "startup-timing.jsonl"),
                json + Environment.NewLine).ConfigureAwait(false);
        }
    }

    private static bool UseProcessHost()
    {
        string configured = Environment.GetEnvironmentVariable("ULTIMA_USE_PROCESS_HOST") ?? "true";
        return !bool.TryParse(configured, out bool enabled) || enabled;
    }

    private static bool CrashSelfRequested()
    {
        return bool.TryParse(Environment.GetEnvironmentVariable("ULTIMA_HOST_CRASH_SELF"), out bool crash)
            && crash;
    }

    private void StartProcessHost()
    {
        string projectRoot = Environment.GetEnvironmentVariable("ULTIMA_PROJECT_ROOT")
            ?? Directory.GetCurrentDirectory();
        _jobObject = new JobObjectManager();
        _readinessProbe = new ReadinessProbe(projectRoot);
        if (_windowActivated)
        {
            _readinessProbe.MarkWindowActivated();
        }
        _processSupervisor = new ChildProcessSupervisor(_jobObject, _readinessProbe, projectRoot);
        _processHostCancellation = new CancellationTokenSource();
        _ = StartProcessHostAsync(_processHostCancellation.Token);
    }

    private async Task StartProcessHostAsync(CancellationToken cancellationToken)
    {
        try
        {
            await _processSupervisor!.StartAsync(cancellationToken);
            string projectRoot = Environment.GetEnvironmentVariable("ULTIMA_PROJECT_ROOT")
                ?? Directory.GetCurrentDirectory();
            _hostTaskRegistry = new HostTaskRegistry(projectRoot, _processSupervisor);
            _guardianService = new GuardianService(_readinessProbe!, _hostTaskRegistry);
            _guardianService.Start(cancellationToken);
            _mainWindow!.DispatcherQueue.TryEnqueue(() =>
                ((MainWindow)_mainWindow).AttachTaskManager(_hostTaskRegistry));
            if (CrashSelfRequested())
            {
                QueueCrashInjection();
            }
        }
        catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
        {
        }
        catch (Exception exception)
        {
            RuntimeEvidence.WriteFailure("PROCESS_HOST_START", exception);
        }
    }

    private void QueueCrashInjection()
    {
        _mainWindow!.DispatcherQueue.TryEnqueue(() =>
        {
            try
            {
                throw new InvalidOperationException("ULTIMA_HOST_CRASH_SELF requested.");
            }
            catch (Exception exception)
            {
                HandleUnhandledException(exception);
            }
        });
    }

    private void HandleUnhandledException(Exception exception)
    {
        RuntimeEvidence.WriteFailure("UI_UNHANDLED", exception);
        StopProcessHost();
        _jobObject?.Close();
        Exit();
    }

    private void StopProcessHost()
    {
        if (_processHostStopped)
        {
            return;
        }
        _processHostStopped = true;

        CompositionTarget.Rendering -= OnFirstFrameRendering;
        _startupTimingCancellation?.Cancel();
        _processHostCancellation?.Cancel();
        _guardianService?.StopAsync().GetAwaiter().GetResult();
        _processSupervisor?.StopAll(TimeSpan.FromSeconds(3));
        _jobObject?.Close();
        _readinessProbe?.Dispose();
        _processHostCancellation?.Dispose();
        _startupTimingCancellation?.Dispose();
    }
}
