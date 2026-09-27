<#
.SYNOPSIS
    Checks for Ollama and starts its local server. Optionally pulls ONE model,
    but only after you confirm - this script does not download anything by default.

.DESCRIPTION
    Ollama serves local LLMs on http://localhost:11434.
    Install Ollama yourself first from https://ollama.com/download (this script
    does not install software). This script just verifies the install, starts
    the background server if it's not already running, and offers to pull a
    single model of your choosing.

.USAGE
    .\scripts\start-ollama.ps1
#>

$ErrorActionPreference = 'Stop'

# --- 1. Check Ollama is installed ---
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollamaCmd) {
    Write-Host "Ollama is not installed or not on PATH." -ForegroundColor Red
    Write-Host "Install it from https://ollama.com/download, then re-run this script."
    exit 1
}

$version = ollama --version
Write-Host "Found: $version" -ForegroundColor Green

# --- 2. Start the Ollama server (idempotent - if already running, `ollama serve`
#        will simply fail to bind and we treat that as "already running") ---
$existing = Get-Process -Name "ollama" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Ollama server already running (PID $($existing.Id -join ','))." -ForegroundColor Yellow
} else {
    Write-Host "Starting Ollama server on http://localhost:11434 ..." -ForegroundColor Cyan
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Minimized
    Start-Sleep -Seconds 2
    Write-Host "Ollama server started." -ForegroundColor Green
}

# --- 3. Model pull - only offered if no models exist yet. If you already
#        have at least one model, this is skipped so the script can be used
#        as a silent, no-prompt daily launcher (see start-all.ps1). ---
$existingModels = ollama list 2>$null | Select-Object -Skip 1
if ($existingModels) {
    Write-Host "Existing models found - skipping pull prompt. Run 'ollama pull <model>' manually to add more." -ForegroundColor DarkGray
} else {
    Write-Host ""
    Write-Host "No models installed yet." -ForegroundColor Yellow
    Write-Host "Once you know your hardware budget (see HARDWARE.md), pull ONE small model to start, e.g.:"
    Write-Host "    ollama pull llama3.2:3b      # ~2GB, good on modest VRAM/RAM"
    Write-Host "    ollama pull phi3:mini        # ~2.3GB, small and capable"
    Write-Host "    ollama pull qwen2.5:7b       # ~4.7GB, needs more headroom"
    Write-Host ""
    $confirm = Read-Host "Pull a model now? Enter a model name (e.g. llama3.2:3b), or leave blank to skip"
    if ($confirm) {
        Write-Host "Pulling $confirm ..." -ForegroundColor Cyan
        ollama pull $confirm
    } else {
        Write-Host "Skipped model pull. Run 'ollama pull <model>' manually when ready." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Ollama is ready at http://localhost:11434" -ForegroundColor Green
