param(
    [Parameter(Mandatory = $true)][string]$SegmentsJson,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech

$segments = Get-Content -LiteralPath $SegmentsJson -Raw -Encoding UTF8 | ConvertFrom-Json
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
$voice = $synthesizer.GetInstalledVoices() |
    Where-Object { $_.VoiceInfo.Culture.Name -eq 'zh-CN' } |
    Select-Object -First 1

if (-not $voice) {
    throw 'No zh-CN Windows speech voice is installed.'
}

$synthesizer.SelectVoice($voice.VoiceInfo.Name)
$synthesizer.Rate = -1
$synthesizer.Volume = 95

try {
    foreach ($segment in $segments) {
        $path = Join-Path $OutputDirectory ('scene_{0:D2}.wav' -f [int]$segment.id)
        $synthesizer.SetOutputToWaveFile($path)
        $synthesizer.Speak([string]$segment.text)
        $synthesizer.SetOutputToNull()
    }
}
finally {
    $synthesizer.Dispose()
}

Write-Output ('Chinese narration generated with voice: ' + $voice.VoiceInfo.Name)