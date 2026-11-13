$ErrorActionPreference = "Stop"

$rendererPath = "src/host-shell/UltimaAgent.HostShell/OrbLiveRenderer.cs"
$windowPath = "src/host-shell/UltimaAgent.HostShell/MainWindow.xaml.cs"
$htmlPath = "src/host-shell/UltimaAgent.HostShell/Assets/orb.html"

$renderer = Get-Content -LiteralPath $rendererPath -Raw
$window = Get-Content -LiteralPath $windowPath -Raw
$html = Get-Content -LiteralPath $htmlPath -Raw

$checks = [ordered]@{
    renderer_message = $renderer.Contains('"orb-warm"')
    renderer_status_override = $renderer.Contains('ULTIMA_HOST_STATUS_FILE')
    renderer_disable_switch = $renderer.Contains('ULTIMA_HOST_WARM_RING')
    window_ready_chain = $window.Contains('OrbLiveRendererOptions.FromEnvironment')
    html_ring = $html.Contains('id="warm-ring"')
    html_handler = $html.Contains("cmd.kind !== 'orb-warm'")
    html_reduced_motion = $html.Contains('prefers-reduced-motion: reduce')
}

$checks.GetEnumerator() | ForEach-Object {
    "{0}={1}" -f $_.Key, $_.Value
}

if ($checks.Values -contains $false) {
    throw "T6 warm-ring contract is incomplete."
}

"T6_CONTRACT_PASS"
