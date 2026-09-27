<#
.SYNOPSIS
    One-click launcher for Studio - starts ComfyUI if it isn't already
    running, starts the Studio server, and opens it in the browser.

.DESCRIPTION
    Studio (studio/server.py) is a small local web app that gives you a
    Grok-Imagine-style toggle UI (Text to Image, Image to Image, Text to
    Video, Text to Music) in front of ComfyUI, driving your existing
    workflows in workflows/ through ComfyUI's own /prompt API.

    This is the everyday "just launch it" entry point - safe to re-run
    any time; it detects what's already running and skips relaunching it.

.USAGE
    .\scripts\start-studio.ps1
#>

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

function Test-Url($url) {
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
        return $resp.StatusCode -eq 200
    } catch { return $false }
}

Write-Host "=== ComfyUI ===" -ForegroundColor Cyan
if (Test-Url "http://localhost:8188") {
    Write-Host "Already running." -ForegroundColor Green
} else {
    & (Join-Path $repoRoot "scripts\start-comfyui.ps1")
}

Write-Host ""
Write-Host "=== Studio ===" -ForegroundColor Cyan
if (Test-Url "http://localhost:8899") {
    Write-Host "Already running." -ForegroundColor Green
} else {
    Write-Host "Launching Studio server..." -ForegroundColor Cyan
    $studioDir = Join-Path $repoRoot "studio"
    Start-Process -FilePath "python" -ArgumentList "server.py" -WorkingDirectory $studioDir -WindowStyle Minimized

    Write-Host "Waiting for Studio to respond on http://localhost:8899 ..." -ForegroundColor Cyan
    $deadline = (Get-Date).AddSeconds(30)
    $ok = $false
    while ((Get-Date) -lt $deadline) {
        if (Test-Url "http://localhost:8899") { $ok = $true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $ok) {
        Write-Host "Studio didn't respond within 30s - check for a Python error in its window." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Opening Studio..." -ForegroundColor Green
Start-Process "http://localhost:8899"
