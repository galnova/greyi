<#
.SYNOPSIS
    Detects local hardware relevant to running local AI models (LLM + image/video gen)
    and writes a summary to HARDWARE.md at the repo root.

.DESCRIPTION
    Run this FIRST, before choosing or downloading any models. VRAM in particular
    determines which LLM quantizations and which Stable Diffusion / video models
    will actually run well on this machine.

.USAGE
    From repo root:
        powershell -ExecutionPolicy Bypass -File scripts\detect-hardware.ps1
    or from inside PowerShell / VS Code terminal:
        .\scripts\detect-hardware.ps1
#>

$ErrorActionPreference = 'SilentlyContinue'

Write-Host "Detecting hardware..." -ForegroundColor Cyan

# --- GPU info (name + dedicated VRAM) ---
# CIM/WMI reports AdapterRAM which is often capped at 4GB (32-bit field) on newer
# drivers, so we also try nvidia-smi for accurate VRAM on NVIDIA cards.
$gpus = Get-CimInstance Win32_VideoController | Where-Object { $_.Name -notmatch 'Basic Display|Remote Display' }

$gpuLines = @()
foreach ($gpu in $gpus) {
    $vramGB = if ($gpu.AdapterRAM) { [math]::Round($gpu.AdapterRAM / 1GB, 2) } else { $null }
    $gpuLines += [PSCustomObject]@{
        Name       = $gpu.Name
        DriverVram = $vramGB
    }
}

$nvidiaSmiVram = $null
$nvidiaSmiName = $null
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    $smiOut = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null
    if ($smiOut) {
        $parts = $smiOut -split ','
        $nvidiaSmiName = $parts[0].Trim()
        $nvidiaSmiVram = $parts[1].Trim()
    }
}

# --- RAM ---
$cs = Get-CimInstance Win32_ComputerSystem
$totalRamGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)

# --- CPU ---
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$cpuName = $cpu.Name
$cpuCores = $cpu.NumberOfCores
$cpuThreads = $cpu.NumberOfLogicalProcessors

# --- Windows version ---
$os = Get-CimInstance Win32_OperatingSystem
$osCaption = $os.Caption
$osVersion = $os.Version
$osBuild = $os.BuildNumber

# --- Free disk space (system drive + any drive with notable free space) ---
$drives = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3"
$diskLines = @()
foreach ($d in $drives) {
    $freeGB = [math]::Round($d.FreeSpace / 1GB, 2)
    $totalGB = [math]::Round($d.Size / 1GB, 2)
    $diskLines += [PSCustomObject]@{
        Drive = $d.DeviceID
        FreeGB = $freeGB
        TotalGB = $totalGB
    }
}

# --- Build report ---
$reportLines = @()
$reportLines += "# Hardware Report"
$reportLines += ""
$reportLines += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$reportLines += ""
$reportLines += "## GPU"
if ($nvidiaSmiName) {
    $reportLines += "- Name (nvidia-smi): $nvidiaSmiName"
    $reportLines += "- Dedicated VRAM (nvidia-smi): $nvidiaSmiVram"
}
foreach ($g in $gpuLines) {
    $vramNote = if ($g.DriverVram) { "$($g.DriverVram) GB (WMI-reported, may be capped/inaccurate on NVIDIA)" } else { "unknown (WMI did not report a value)" }
    $reportLines += "- Name (WMI): $($g.Name)"
    $reportLines += "- VRAM (WMI): $vramNote"
}
if (-not $gpuLines -and -not $nvidiaSmiName) {
    $reportLines += "- No discrete/display GPU detected via WMI or nvidia-smi."
}
$reportLines += ""
$reportLines += "## RAM"
$reportLines += "- Total physical RAM: $totalRamGB GB"
$reportLines += ""
$reportLines += "## CPU"
$reportLines += "- Name: $cpuName"
$reportLines += "- Cores: $cpuCores"
$reportLines += "- Logical processors (threads): $cpuThreads"
$reportLines += ""
$reportLines += "## Windows"
$reportLines += "- Caption: $osCaption"
$reportLines += "- Version: $osVersion (Build $osBuild)"
$reportLines += ""
$reportLines += "## Disk (free space)"
foreach ($d in $diskLines) {
    $reportLines += "- $($d.Drive) $($d.FreeGB) GB free / $($d.TotalGB) GB total"
}
$reportLines += ""
$reportLines += "---"
$reportLines += ""
$reportLines += "**Do not pick or download models until this report has been reviewed.** VRAM is the"
$reportLines += "primary constraint: it determines which LLM quantization sizes (Ollama) and which"
$reportLines += "Stable Diffusion / video model families and resolutions (ComfyUI) will run acceptably."

$report = $reportLines -join "`r`n"

# Write to HARDWARE.md at repo root (one level up from scripts/)
$repoRoot = Split-Path -Parent $PSScriptRoot
$outPath = Join-Path $repoRoot "HARDWARE.md"
$report | Out-File -FilePath $outPath -Encoding utf8

# Also print to console
Write-Host ""
Write-Host $report
Write-Host ""
Write-Host "Written to $outPath" -ForegroundColor Green
