using Microsoft.UI.Windowing;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using Windows.UI;
using Windows.Graphics;
using WinRT.Interop;

namespace UltimaAgent.HostShell;

public sealed partial class MainWindow : Window
{
    private readonly WebView2 _webView = new();
    private readonly AppWindow _appWindow;

    public MainWindow()
    {
        InitializeComponent();
        nint handle = WindowNative.GetWindowHandle(this);
        _appWindow = AppWindow.GetFromWindowId(Microsoft.UI.Win32Interop.GetWindowIdFromWindow(handle));
        bool dpiAcceptance = Environment.GetEnvironmentVariable("ULTIMA_HOST_DPI_ACCEPTANCE") == "1";
        bool floatingBall = Environment.GetEnvironmentVariable("ULTIMA_HOST_FLOATINGBALL_TEST") == "1"
            || dpiAcceptance;
        Grid shell = CreateShell();
        Content = shell;
        shell.Loaded += async (_, _) =>
        {
            try
            {
                if (floatingBall)
                {
                    await FloatingBallEvidence.RunAsync(_webView, _appWindow, handle);
                }
                else if (Environment.GetEnvironmentVariable("ULTIMA_HOST_WEBVIEW_TEST") == "1")
                {
                    await WebViewEvidence.RunAsync(_webView);
                }
                else
                {
                    string? capturePath = Environment.GetEnvironmentVariable("ULTIMA_HOST_CAPTURE_PATH");
                    if (!string.IsNullOrWhiteSpace(capturePath))
                    {
                        await RuntimeEvidence.CaptureElementAsync(shell, capturePath);
                    }
                }
            }
            catch (Exception exception)
            {
                RuntimeEvidence.WriteFailure("WEBVIEW2_FAILED", exception);
                Application.Current.Exit();
            }
        };
        if (floatingBall)
        {
            FloatingBallEvidence.ConfigureWindow(_appWindow, handle);
        }
        else
        {
            _appWindow.Resize(new SizeInt32(960, 640));
        }
    }

    private Grid CreateShell()
    {
        TextBlock title = new()
        {
            Text = "Ultima Agent",
            HorizontalAlignment = HorizontalAlignment.Center,
            FontFamily = new FontFamily("ms-appx:///Assets/HarmonyOS_Sans.ttf#HarmonyOS Sans"),
            FontSize = 32,
            FontWeight = Microsoft.UI.Text.FontWeights.SemiBold,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 230, 234, 242))
        };
        TextBlock subtitle = new()
        {
            Text = "宿主壳已就绪",
            HorizontalAlignment = HorizontalAlignment.Center,
            FontFamily = new FontFamily("ms-appx:///Assets/HarmonyOS_Sans_SC.ttf#HarmonyOS Sans SC"),
            FontSize = 14,
            Foreground = new SolidColorBrush(Color.FromArgb(255, 154, 163, 184))
        };
        StackPanel stack = new()
        {
            HorizontalAlignment = HorizontalAlignment.Center,
            VerticalAlignment = VerticalAlignment.Center,
            Spacing = 8
        };
        stack.Children.Add(title);
        stack.Children.Add(subtitle);
        Grid root = new()
        {
            Background = new SolidColorBrush(Color.FromArgb(255, 15, 20, 32)),
            Children = { stack }
        };
        bool useWebView = Environment.GetEnvironmentVariable("ULTIMA_HOST_WEBVIEW_TEST") == "1"
            || Environment.GetEnvironmentVariable("ULTIMA_HOST_FLOATINGBALL_TEST") == "1"
            || Environment.GetEnvironmentVariable("ULTIMA_HOST_DPI_ACCEPTANCE") == "1";
        _webView.Visibility = useWebView
            ? Visibility.Visible
            : Visibility.Collapsed;
        _webView.HorizontalAlignment = HorizontalAlignment.Stretch;
        _webView.VerticalAlignment = VerticalAlignment.Stretch;
        root.Children.Add(_webView);
        return root;
    }
}
