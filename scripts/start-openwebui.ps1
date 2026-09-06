<#
.SYNOPSIS
    Starts Open WebUI in Docker, wired to a locally running Ollama instance.

.DESCRIPTION
    Open WebUI is a browser-based chat UI (like ChatGPT's interface) that talks
    to Ollama for inference. It runs in a Docker container and reaches Ollama
    on the Windows host via the special DNS name `host.docker.internal`.

    Prerequisites (not installed by this script):
      - Docker Desktop, running, with WSL2 backend enabled.
      - Ollama running locally (see scripts/start-ollama.ps1) - Open WebUI
        just needs Ollama reachable at http://host.docker.internal:11434.

.USAGE
    .\scripts\start-openwebui.ps1
#>

$ErrorActionPreference = 'Stop'

# --- 1. Check Docker is installed and running ---
$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Host "Docker is not installed or not on PATH." -ForegroundColor Red
    Write-Host "Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    exit 1
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is installed but the daemon isn't running. Start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# --- 2. Check if the container already exists ---
$containerName = "open-webui"
$existing = docker ps -a --filter "name=^/$containerName$" --format "{{.Names}}"

if ($existing -eq $containerName) {
    $running = docker ps --filter "name=^/$containerName$" --format "{{.Names}}"
    if ($running -eq $containerName) {
        Write-Host "Open WebUI container already running." -ForegroundColor Yellow
    } else {
        Write-Host "Open WebUI container exists but is stopped. Starting it..." -ForegroundColor Cyan
        docker start $containerName
    }
} else {
    Write-Host "Creating and starting Open WebUI container..." -ForegroundColor Cyan
    # -d              detached
    # -p 3000:8080    Open WebUI listens on 8080 inside the container; exposed on host port 3000
    # --add-host      lets the container resolve host.docker.internal on Windows/WSL2
    # -e OLLAMA_BASE_URL  points Open WebUI at the host's Ollama server
    # -v open-webui-data:/app/backend/data   persistent volume for chats/settings (gitignored, lives in Docker, not this repo)
    # --restart unless-stopped   survives Docker restarts, but not a reboot unless Docker Desktop autostarts
    docker run -d `
        --name $containerName `
        -p 3000:8080 `
        --add-host=host.docker.internal:host-gateway `
        -e OLLAMA_BASE_URL=http://host.docker.internal:11434 `
        -v open-webui-data:/app/backend/data `
        --restart unless-stopped `
        ghcr.io/open-webui/open-webui:main
}

Write-Host ""
Write-Host "Open WebUI available at http://localhost:3000" -ForegroundColor Green
Write-Host "(First load may take a few seconds while the container finishes starting.)"
Write-Host "Make sure Ollama is running (scripts/start-ollama.ps1) or the model list will be empty."
