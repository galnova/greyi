# ComfyUI

ComfyUI portable is installed at:

```
D:\ComfyUI\ComfyUI_windows_portable\
```

It lives **outside this repo** on purpose - it's a multi-GB install with its
own embedded Python, and isn't tracked in git (see `.gitignore`).

## Launching it

Easiest: `.\scripts\start-comfyui.ps1` from the repo root, or double-click
the **"Launch ComfyUI"** shortcut on the Desktop. Both start
`run_nvidia_gpu.bat` and open http://localhost:8188 automatically.

Manually, you can also just double-click
`D:\ComfyUI\ComfyUI_windows_portable\run_nvidia_gpu.bat` directly.

If your GPU situation ever changes (e.g. troubleshooting), the portable
folder also ships `run_cpu.bat` for a CPU-only fallback.

## Model paths

ComfyUI is configured via
`D:\ComfyUI\ComfyUI_windows_portable\ComfyUI\extra_model_paths.yaml` to read
models directly from this repo's `models/` folder - no copying or
symlinking needed. Confirmed working (verified in the ComfyUI startup log,
"Adding extra search path ..." lines) for:

| ComfyUI key       | Repo folder            |
|--------------------|--------------------------|
| `checkpoints`      | `models/checkpoints/`   |
| `loras`            | `models/loras/`         |
| `vae`              | `models/vae/`           |
| `controlnet`       | `models/controlnet/`    |
| `upscale_models`   | `models/upscalers/`     |

`models/video/` in this repo is **not** wired up automatically - video
generation model packs (AnimateDiff, SVD, etc.) are usually installed as
custom nodes with their own expected model folder, which varies by node
pack. Follow that node pack's own instructions when you get there; you can
still keep source copies in `models/video/` for reference.

## Workflows

Save/export workflows as JSON into this repo's `workflows/` folder so they
stay tracked in git (workflow JSON is small text, unlike the models it
references).

## Reinstalling / upgrading

If you ever need to reinstall (e.g. a fresh machine, or the D:\ComfyUI
folder gets removed):

1. Download "ComfyUI portable" (NVIDIA build) from the official ComfyUI
   GitHub releases.
2. Extract it to `D:\ComfyUI\` (or wherever you prefer - it's not tracked in
   git, so the location is just a local choice, update `scripts/start-comfyui.ps1`
   if you move it).
3. Copy `extra_model_paths.yaml.example` inside the extracted
   `ComfyUI\` folder to `extra_model_paths.yaml` and set it up per the table
   above (or copy this repo's own `docs/extra_model_paths.yaml.reference`,
   see below).
