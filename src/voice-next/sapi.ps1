#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Request
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$synthesizer = $null

try {
    $payload = Get-Content -LiteralPath $Request -Raw -Encoding utf8 | ConvertFrom-Json
    if ($payload.text -isnot [string] -or [string]::IsNullOrWhiteSpace($payload.text)) {
        throw 'Request text must be a non-empty string.'
    }
    if ($payload.output -isnot [string] -or [string]::IsNullOrWhiteSpace($payload.output)) {
        throw 'Request output must be a WAV path.'
    }
    $outputPath = [IO.Path]::GetFullPath($payload.output)
    if ([IO.Path]::GetExtension($outputPath) -ine '.wav') {
        throw 'Request output must have the .wav extension.'
    }
    $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($outputPath))
    Add-Type -AssemblyName System.Speech
    $synthesizer = [System.Speech.Synthesis.SpeechSynthesizer]::new()
    $voices = @($synthesizer.GetInstalledVoices() | Where-Object {
        $_.Enabled -and $_.VoiceInfo.Culture.Name -like 'zh*'
    })
    $selected = $voices | Where-Object { $_.VoiceInfo.Name -like '*Huihui*Desktop*' } | Select-Object -First 1
    if ($null -eq $selected) {
        $selected = $voices | Select-Object -First 1
    }
    if ($null -eq $selected) {
        throw 'No installed Chinese Windows SAPI voice is available.'
    }
    $synthesizer.SelectVoice($selected.VoiceInfo.Name)
    $synthesizer.Volume = 100
    $format = [System.Speech.AudioFormat.SpeechAudioFormatInfo]::new(
        16000,
        [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
        [System.Speech.AudioFormat.AudioChannel]::Mono
    )
    $synthesizer.SetOutputToWaveFile($outputPath, $format)
    $synthesizer.Speak($payload.text)
    $synthesizer.SetOutputToNull()
    [Console]::Out.WriteLine((@{
        ok = $true
        wav = $outputPath
        voice = $selected.VoiceInfo.Name
        rate = 16000
        channels = 1
    } | ConvertTo-Json -Compress))
}
catch {
    [Console]::Error.WriteLine('SAPI WAV synthesis failed: ' + $_.Exception.Message)
    exit 1
}
finally {
    if ($null -ne $synthesizer) {
        $synthesizer.Dispose()
    }
}
