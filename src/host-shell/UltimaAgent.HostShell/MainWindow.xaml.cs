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
        bool orbTest = Environment.GetEnvironmentVariable("ULTIMA_HOST_ORB_TEST") == "1";
        bool orbLive = Environment.GetEnvironmentVariable("ULTIMA_HOST_LIVE") == "1";
        bool combo = Environment.GetEnvironmentVariable("ULTIMA_HOST_COMBO") == "1";
        bool floatingBall = Environment.GetEnvironmentVariable("ULTIMA_HOST_FLOATINGBALL_TEST") == "1"
            || dpiAcceptance;
        Grid shell = CreateShell();
        Content = shell;
        // 关闭 WinUI3 默认 backdrop（Win11 默认 Mica 磨砂底色 = 窗体白框真凶），
        // 背景交由 ACCENT 透明接管（见 OrbWindowConfig.SetTransparent）
        if (orbLive || orbTest)
        {
            SystemBackdrop = null;
        }
        shell.Loaded += async (_, _) =>
        {
            try
            {
                if (combo)
                {
                    await ComboWindowRenderer.RunAsync(
                        _webView, _appWindow, handle, AppContext.BaseDirectory,
                        ResolveWriteRoot());
                }
                else if (orbLive)
                {
                    // 复现 10:41 成功配方：ACCENT + SetWindowPos 240 + 无 Region + 无特殊属性
                    OrbWindowConfig.ApplyAccent(handle);
                    OrbWindowConfig.ResizeAndLocate(_appWindow, handle);
                    await OrbLiveRenderer.RunAsync(
                        _webView, _appWindow, handle, AppContext.BaseDirectory,
                        ResolveWriteRoot());
                }
                else if (orbTest)
                {
                    await OrbBallRenderer.RunAsync(
                        _webView, _appWindow, handle, AppContext.BaseDirectory);
                }
                else if (floatingBall)
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
        if (orbTest || orbLive)
        {
            OrbWindowConfig.Configure(_appWindow, handle);
        }
        else if (floatingBall)
        {
            FloatingBallEvidence.ConfigureWindow(_appWindow, handle);
        }
        else if (!combo)
        {
            _appWindow.Resize(new SizeInt32(960, 640));
        }
    }

    /// <summary>写域根解析：环境变量优先，默认上溯 exe 目录到 UltimaAgent 根。</summary>
    private static string ResolveWriteRoot()
    {
        string? configured = Environment.GetEnvironmentVariable("ULTIMA_HOST_WRITE_ROOT");
        if (!string.IsNullOrWhiteSpace(configured))
        {
            return configured;
        }
        DirectoryInfo current = new(AppContext.BaseDirectory);
        while (current is not null)
        {
            if (File.Exists(Path.Combine(current.FullName, "INDEX.md"))
                || Directory.Exists(Path.Combine(current.FullName, "src", "brain")))
            {
                return current.FullName;
            }
            current = current.Parent ?? throw new InvalidOperationException("写域根解析失败：未找到 UltimaAgent 根");
        }
        return AppContext.BaseDirectory;
    }

    private Grid CreateShell()
    {
        bool useWebView = Environment.GetEnvironmentVariable("ULTIMA_HOST_LIVE") == "1"
            || Environment.GetEnvironmentVariable("ULTIMA_HOST_COMBO") == "1"
            || Environment.GetEnvironmentVariable("ULTIMA_HOST_WEBVIEW_TEST") == "1"
            || Environment.GetEnvironmentVariable("ULTIMA_HOST_FLOATINGBALL_TEST") == "1"
            || Environment.GetEnvironmentVariable("ULTIMA_HOST_DPI_ACCEPTANCE") == "1"
            || Environment.GetEnvironmentVariable("ULTIMA_HOST_ORB_TEST") == "1";
        // 复现历史成功配方：orbLive 根背景透明（ACCENT 透明窗口承载 WebView2 球）
        bool orbLive = Environment.GetEnvironmentVariable("ULTIMA_HOST_LIVE") == "1";
        var rootBg = orbLive
            ? new SolidColorBrush(Color.FromArgb(0, 0, 0, 0))
            : useWebView
                ? new SolidColorBrush(Color.FromArgb(0, 0, 0, 0))
                : new SolidColorBrush(Color.FromArgb(255, 15, 20, 32));
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
            Background = rootBg,
            Children = { stack }
        };
        _webView.Visibility = useWebView
            ? Visibility.Visible
            : Visibility.Collapsed;
        _webView.HorizontalAlignment = HorizontalAlignment.Stretch;
        _webView.VerticalAlignment = VerticalAlignment.Stretch;
        root.Children.Add(_webView);
        return root;
    }
}
