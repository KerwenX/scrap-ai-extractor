param(
    [switch]$Stop,
    [switch]$Status,
    [int]$Port = 8000,
    [string]$BindHost = "127.0.0.1"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$logsDir = Join-Path $projectRoot "logs"
$runnerScript = Join-Path $PSScriptRoot "run_ui_server.py"
$pidFile = Join-Path $logsDir "ui-server-$Port.pid"
$outLog = Join-Path $logsDir "ui-server-$Port.out.log"
$errLog = Join-Path $logsDir "ui-server-$Port.err.log"

if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

function Get-PythonPath {
    if (Test-Path "C:\Python314\python.exe") {
        return "C:\Python314\python.exe"
    }
    return "python"
}

function Get-TrackedProcess {
    if (-not (Test-Path $pidFile)) {
        return $null
    }

    $rawPid = (Get-Content -Path $pidFile -ErrorAction SilentlyContinue | Select-Object -First 1).Trim()
    if (-not $rawPid) {
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
        return $null
    }

    try {
        $proc = Get-Process -Id ([int]$rawPid) -ErrorAction Stop
        return $proc
    } catch {
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
        return $null
    }
}

function Get-ListeningProcess {
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        if ($null -eq $connection) {
            return $null
        }
        return Get-Process -Id $connection.OwningProcess -ErrorAction Stop
    } catch {
        return $null
    }
}

function Stop-UiProcess {
    $tracked = Get-TrackedProcess
    if ($tracked) {
        Stop-Process -Id $tracked.Id -Force
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped UI server process $($tracked.Id)."
        return
    }

    $listening = Get-ListeningProcess
    if ($listening) {
        Stop-Process -Id $listening.Id -Force
        Remove-Item -LiteralPath $pidFile -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped UI server process $($listening.Id) on port $Port."
        return
    }

    Write-Host "UI server is not running on port $Port."
}

function Show-UiStatus {
    $tracked = Get-TrackedProcess
    $listening = Get-ListeningProcess

    if ($tracked) {
        Write-Host "UI server is running in background."
        Write-Host "PID: $($tracked.Id)"
        Write-Host "URL: http://$BindHost`:$Port/"
        Write-Host "STDOUT: $outLog"
        Write-Host "STDERR: $errLog"
        return
    }

    if ($listening) {
        Write-Host "Port $Port is occupied by PID $($listening.Id) ($($listening.ProcessName))."
        Write-Host "URL: http://$BindHost`:$Port/"
        return
    }

    Write-Host "UI server is not running."
}

if ($Stop) {
    Stop-UiProcess
    exit 0
}

if ($Status) {
    Show-UiStatus
    exit 0
}

$tracked = Get-TrackedProcess
if ($tracked) {
    Write-Host "UI server is already running in background. PID: $($tracked.Id)"
    Write-Host "URL: http://$BindHost`:$Port/"
    exit 0
}

$listening = Get-ListeningProcess
if ($listening) {
    throw "Port $Port is already occupied by PID $($listening.Id) ($($listening.ProcessName)). Run .\scripts\run_ui.ps1 -Stop first."
}

$python = Get-PythonPath
$pythonArgs = @($runnerScript)

Write-Host "Starting UI server in foreground at http://$BindHost`:$Port/"
Write-Host "Press Ctrl+C to stop."
Push-Location $projectRoot
if ($Port -ne 8000 -or $BindHost -ne "127.0.0.1") {
    $env:HYBRID_UI_HOST = $BindHost
    $env:HYBRID_UI_PORT = "$Port"
}
try {
    & $python @pythonArgs
} finally {
    Remove-Item Env:\HYBRID_UI_HOST -ErrorAction SilentlyContinue
    Remove-Item Env:\HYBRID_UI_PORT -ErrorAction SilentlyContinue
    Pop-Location
}
