using Microsoft.UI.Dispatching;
using Microsoft.UI.Xaml;

namespace UltimaAgent.HostShell;

public partial class App : Application
{
    private Window? _mainWindow;
    private DispatcherQueueTimer? _exitTimer;

    public App()
    {
        InitializeComponent();
        UnhandledException += (_, args) =>
        {
            RuntimeEvidence.WriteFailure("UI_UNHANDLED", args.Exception);
            args.Handled = true;
            Exit();
        };
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        _mainWindow = new MainWindow();
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
    }
}
