<#
.SYNOPSIS
    Launches SillyTavern (chat/roleplay frontend for Ollama) and opens it
    in the browser.

.DESCRIPTION
    SillyTavern is installed at D:\SillyTavern (outside this repo, same
    pattern as ComfyUI - it's a large Node.js app with its own
    node_modules, not something that belongs in this git repo).

    It connects to your existing Ollama models (qwen2.5-coder:7b,
    llama3.2:3b) the same way Open WebUI does, through a different,
    more roleplay/character-persona-oriented interface.

    First time setup: open http://localhost:8000, go to the API
    Connections panel (plug icon), choose "Text Completion" as the API,
    then "Ollama" as the source, and point it at
    http://localhost:11434 - then pick a model from the dropdown that
    appears. This only needs to be done once; SillyTavern remembers it.

.USAGE
    .\scripts\start-sillytavern.ps1
#>

$ErrorActionPreference = 'Stop'

function Test-Url($url) {
    try {
        $resp = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
        return $resp.StatusCode -eq 200
    } catch { return $false }
}

Write-Host "=== Ollama ===" -ForegroundColor Cyan
if (Test-Url "http://localhost:11434/api/version") {
    Write-Host "Already running." -ForegroundColor Green
} else {
    Write-Host "Ollama isn't running - start it first (scripts/start-ollama.ps1)." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=== SillyTavern ===" -ForegroundColor Cyan
if (Test-Url "http://localhost:8000") {
    Write-Host "Already running." -ForegroundColor Green
} else {
    Write-Host "Launching SillyTavern..." -ForegroundColor Cyan
    Start-Process -FilePath "D:\SillyTavern\Start.bat" -WorkingDirectory "D:\SillyTavern" -WindowStyle Minimized

    $deadline = (Get-Date).AddSeconds(90)
    $ok = $false
    while ((Get-Date) -lt $deadline) {
        if (Test-Url "http://localhost:8000") { $ok = $true; break }
        Start-Sleep -Seconds 3
    }
    if (-not $ok) {
        Write-Host "Didn't respond within 90s - first launch can take longer. Check its console window." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Opening SillyTavern..." -ForegroundColor Green
Start-Process "http://localhost:8000"
