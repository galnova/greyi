<#
.SYNOPSIS
    Launches ComfyUI portable and opens it in the browser.

.DESCRIPTION
    ComfyUI portable lives OUTSIDE this repo (installed to D:\ComfyUI - see
    docs/comfyui-note.md) because it's a multi-GB install with its own
    embedded Python, and isn't tracked in git. This script just calls its
    own launcher (run_nvidia_gpu.bat) and waits for the server to come up.

    ComfyUI is configured (via its extra_model_paths.yaml) to read model
    files from this repo's models/ folder, so checkpoints/LoRAs/VAE/
    controlnet/upscalers placed in models/<subfolder> here are automatically
    visible inside ComfyUI - no copying required.

    Note: Ollama + Open WebUI and ComfyUI both use GPU VRAM. On an 8GB card,
    running heavy image/video generation at the same time as a loaded LLM
    can be tight - close one if the other runs out of memory.

.USAGE
    .\scripts\start-comfyui.ps1
#>

$ErrorActionPreference = 'Stop'

$comfyRoot = "D:\ComfyUI\ComfyUI_windows_portable"
$launcher = Join-Path $comfyRoot "run_nvidia_gpu.bat"

if (-not (Test-Path $launcher)) {
    Write-Host "ComfyUI not found at $launcher" -ForegroundColor Red
    Write-Host "See scripts/comfyui-note.md for install instructions."
    exit 1
}

Write-Host "Launching ComfyUI (first launch after a restart can take a minute)..." -ForegroundColor Cyan
Start-Process -FilePath $launcher -WorkingDirectory $comfyRoot -WindowStyle Minimized

Write-Host "Waiting for ComfyUI to respond on http://localhost:8188 ..." -ForegroundColor Cyan
$deadline = (Get-Date).AddSeconds(120)
$ok = $false
while ((Get-Date) -lt $deadline) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8188" -UseBasicParsing -TimeoutSec 5
        if ($resp.StatusCode -eq 200) { $ok = $true; break }
    } catch {}
    Start-Sleep -Seconds 3
}

if ($ok) {
    Write-Host "ComfyUI is up. Opening browser..." -ForegroundColor Green
    Start-Process "http://localhost:8188"
} else {
    Write-Host "ComfyUI didn't respond within 120s. Check the ComfyUI console window for errors." -ForegroundColor Red
}
