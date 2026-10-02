param(
    [string]$PythonCommand = "python",
    [int]$StartupSeconds = 8,
    [switch]$RequireWindows11
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$entryPoint = Join-Path $repoRoot "src\main.py"

function Get-ExternalToolVersion {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments
    )

    $command = Get-Command $Executable -ErrorAction Stop
    $output = & $command.Source @Arguments 2>&1
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        $details = $output -join [Environment]::NewLine
        throw "$Executable version check failed with exit code $exitCode.$([Environment]::NewLine)$details"
    }

    $firstLine = $output | Select-Object -First 1
    if (-not $firstLine) {
        throw "$Executable version check returned no output."
    }

    return $firstLine.ToString().Trim()
}

$os = Get-CimInstance Win32_OperatingSystem

if ($RequireWindows11 -and $os.Caption -notmatch "Windows 11") {
    throw "Expected a Windows 11 runner, got '$($os.Caption)' ($($os.Version))."
}

$python = Get-Command $PythonCommand -ErrorAction Stop
$pythonVersion = (
    & $python.Source --version 2>&1 |
    Select-Object -First 1
).ToString().Trim()

$ytDlpVersion = Get-ExternalToolVersion `
    -Executable "yt-dlp" `
    -Arguments @("--version")

$ffmpegVersion = Get-ExternalToolVersion `
    -Executable "ffmpeg" `
    -Arguments @("-version")

Write-Host "OS: $($os.Caption) $($os.Version) [$env:PROCESSOR_ARCHITECTURE]"
Write-Host "Python: $pythonVersion"
Write-Host "yt-dlp: $ytDlpVersion"
Write-Host "FFmpeg: $ffmpegVersion"

$process = Start-Process `
    -FilePath $python.Source `
    -ArgumentList @($entryPoint) `
    -WorkingDirectory $repoRoot `
    -PassThru

try {
    Start-Sleep -Seconds $StartupSeconds
    $process.Refresh()

    if ($process.HasExited) {
        throw "Application exited during startup with code $($process.ExitCode)."
    }

    Write-Host "Application remained alive for $StartupSeconds seconds, including the splash-to-main-window handover."
}
finally {
    $process.Refresh()

    if (-not $process.HasExited) {
        Stop-Process -Id $process.Id -Force
    }
}