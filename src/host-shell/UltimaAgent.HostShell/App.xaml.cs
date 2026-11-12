using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;
using UltimaAgent.HostShell.ProcessHost;

namespace UltimaAgent.HostShell;

public partial class App : Application
{
    private Window? _mainWindow;
    private DispatcherQueueTimer? _exitTimer;
    private JobObjectManager? _jobObject;
    private ReadinessProbe? _readinessProbe;
    private ChildProcessSupervisor? _processSupervisor;
    private CancellationTokenSource? _processHostCancellation;
    private bool _windowActivated;
    private bool _processHostStopped;

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
        _mainWindow = new MainWindow();
        _mainWindow.Activated += (_, _) =>
        {
            _windowActivated = true;
            _readinessProbe?.MarkWindowActivated();
        };
        _mainWindow.Closed += (_, _) => StopProcessHost();
        _mainWindow.Activate();
        _mainWindow.DispatcherQueue.TryEnqueue(() => RuntimeEvidence.WriteWindowReady(_mainWindow));

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

        _processHostCancellation?.Cancel();
        _processSupervisor?.StopAll(TimeSpan.FromSeconds(3));
        _jobObject?.Close();
        _readinessProbe?.Dispose();
        _processHostCancellation?.Dispose();
    }
}
