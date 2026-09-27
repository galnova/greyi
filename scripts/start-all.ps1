<#
.SYNOPSIS
    One-click launcher for the local AI chat stack: starts Ollama, starts
    Open WebUI, waits for it to come up, then opens it in the browser.

.DESCRIPTION
    Runs start-ollama.ps1 and start-openwebui.ps1 (both idempotent - safe to
    re-run any time), then polls http://localhost:3000 until it responds and
    opens it automatically. This is the everyday "just launch it" entry point.

    Does NOT touch ComfyUI - that's a separate tool with its own launcher,
    see scripts/comfyui-note.md.

.USAGE
    .\scripts\start-all.ps1
#>

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot

Write-Host "=== Starting Ollama ===" -ForegroundColor Cyan
& (Join-Path $repoRoot "scripts\start-ollama.ps1")

Write-Host ""
Write-Host "=== Starting Open WebUI ===" -ForegroundColor Cyan
& (Join-Path $repoRoot "scripts\start-openwebui.ps1")

Write-Host ""
Write-Host "Waiting for Open WebUI to respond..." -ForegroundColor Cyan
$deadline = (Get-Date).AddSeconds(60)
$ok = $false
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 5
        if ($resp.StatusCode -eq 200) { $ok = $true; break }
    } catch {}
    Start-Sleep -Seconds 2
}

if ($ok) {
    Write-Host "Open WebUI is up. Opening browser..." -ForegroundColor Green
    Start-Process "http://localhost:3000"
} else {
    Write-Host "Open WebUI didn't respond within 60s." -ForegroundColor Red
    Write-Host "Check Docker Desktop is running, then try: docker logs open-webui"
}
