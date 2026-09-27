# Local AI Generation Environment

A fully local, free, self-hosted stack for LLM chat and image/video
generation. No paid subscriptions, no cloud APIs - everything runs on this
machine.

## Stack

| Component      | Role                                  | Port    |
|-----------------|----------------------------------------|---------|
| **Ollama**      | Runs local LLMs                       | `11434` |
| **Open WebUI**  | Browser chat UI for Ollama (Docker)   | `3000`  |
| **ComfyUI**     | Image/video generation (node-based UI)| `8188`  |
| **Studio**      | Toggle UI (Text/Image → Image/Video/Music) in front of ComfyUI | `8899`  |

## Quick start (daily use)

Easiest option: double-click **"Launch AI Chat"** on your Desktop. It starts
Ollama, starts Open WebUI, waits for it to come up, and opens your browser
to it automatically - no prompts, nothing to type.

That shortcut just runs this from the repo root:

```powershell
.\scripts\start-all.ps1
```

Which in turn runs `start-ollama.ps1` and `start-openwebui.ps1` individually
(both idempotent - safe to re-run any time, they detect what's already
running and skip it). Use those two directly instead of `start-all.ps1` if
you only want one piece running, or want to see each step's own output.

Requires Docker Desktop to be running in the background (it usually
auto-starts with Windows once installed; if the browser tab shows nothing,
open Docker Desktop first and give it a few seconds, then re-run the
shortcut).

For **ComfyUI** (image/video generation - a separate, parallel tool, not a
step after the chat stack): double-click **"Launch ComfyUI"** on the
Desktop, or run `.\scripts\start-comfyui.ps1`. See `scripts/comfyui-note.md`
for details.

For **Studio** (a simpler toggle UI - Text to Image, Image to Image, Text to
Video, Text to Music - in front of ComfyUI, instead of using ComfyUI's node
graph directly): double-click **"Launch Studio"** on the Desktop, or run
`.\scripts\start-studio.ps1`. This starts ComfyUI too if it isn't already
running, so you don't need to launch both separately. See `studio/README.md`
for how it works and which modes are wired up.

Note: on an 8GB VRAM card, running a loaded Ollama model and heavy ComfyUI
generation at the same time can be tight - if you hit out-of-memory errors,
close one while using the other.

## Repo layout

```
scripts/      Setup, detection, and launch scripts (tracked)
studio/       Toggle UI web app in front of ComfyUI (tracked) - see studio/README.md
workflows/    ComfyUI workflow JSON files (tracked)
prompts/      Saved prompts/prompt notes (tracked)
references/   Reference images/inputs for workflows (tracked)
docs/         Additional documentation (tracked)
models/       Model weights - EMPTY in git, see models/README.md
outputs/      Generated images/videos - EMPTY in git, see outputs/README.md
HARDWARE.md   Output of scripts/detect-hardware.ps1 (tracked)
```

Large binaries (model weights, generated media, Docker volumes, ComfyUI's
own portable install) are excluded via `.gitignore` so this repo stays small
and clonable. See `models/README.md` and `outputs/README.md` for how to
repopulate them locally.

## Install order

1. **Detect hardware first.** Run:
   ```powershell
   .\scripts\detect-hardware.ps1
   ```
   This writes `HARDWARE.md`. VRAM determines which model sizes/quantizations
   are realistic - don't install or download anything until you've checked it.

2. **Ollama** - install from https://ollama.com/download, then:
   ```powershell
   .\scripts\start-ollama.ps1
   ```
   This checks the install, starts the server, and optionally pulls one
   model you choose (nothing downloads automatically).

3. **Docker Desktop** - install from
   https://www.docker.com/products/docker-desktop/, enable WSL2 backend,
   make sure it's running.

4. **Open WebUI** (via Docker):
   ```powershell
   .\scripts\start-openwebui.ps1
   ```
   Wires up to Ollama automatically via `http://host.docker.internal:11434`.

5. **ComfyUI** - installed at `D:\ComfyUI\ComfyUI_windows_portable\`. Launch
   via `.\scripts\start-comfyui.ps1` or the "Launch ComfyUI" Desktop
   shortcut. See `scripts/comfyui-note.md` for the full setup, including how
   it's wired to read models from this repo's `models/` folder.

6. **Studio** (optional, built on top of ComfyUI) - no separate install;
   launch via `.\scripts\start-studio.ps1` or the "Launch Studio" Desktop
   shortcut. See `studio/README.md`.

## Starting / stopping

| Component         | Start                                                            | Stop                                                    |
|--------------------|--------------------------------------------------------------------|------------------------------------------------------------|
| Ollama + Open WebUI (one-click) | Desktop shortcut "Launch AI Chat", or `.\scripts\start-all.ps1` | Close Docker Desktop, or the two "Stop" commands below |
| Ollama             | `.\scripts\start-ollama.ps1`                                      | `Stop-Process -Name ollama`                               |
| Open WebUI         | `.\scripts\start-openwebui.ps1`                                   | `docker stop open-webui`                                  |
| ComfyUI            | Desktop shortcut "Launch ComfyUI", or `.\scripts\start-comfyui.ps1` | Close the ComfyUI console window                        |
| Studio (+ ComfyUI if needed) | Desktop shortcut "Launch Studio", or `.\scripts\start-studio.ps1` | Close its console window (and ComfyUI's, if you want both down) |

## Where models go

Place downloaded model files into the matching `models/` subfolder
(`checkpoints`, `loras`, `vae`, `controlnet`, `upscalers`, `video`) - see
`models/README.md` for details and re-fetch instructions. Ollama manages its
own model store separately (`ollama list`, `ollama pull <model>`).

## Setting up on a fresh clone

Cloning this repo gets you scripts, docs, and workflow JSON - none of the
actual model weights (they're gitignored on purpose, see `models/README.md`).
To get a fully working setup again, run Ollama/Docker/ComfyUI install steps
above first, then hand your AI assistant this prompt to re-fetch everything
else:

```
Set up all the assets this repo needs that aren't tracked in git. Read
models/README.md and studio/README.md first for context, then:

1. Ollama models (`ollama pull <name>`):
   - llama3.2:3b
   - qwen2.5-coder:7b

2. ComfyUI custom nodes - git clone each into
   <ComfyUI portable>/ComfyUI/custom_nodes/, then run
   `python_embeded/python.exe -m pip install -r requirements.txt` inside
   each cloned folder if it has one, then restart ComfyUI:
   - https://github.com/Comfy-Org/ComfyUI-Manager
   - https://github.com/city96/ComfyUI-GGUF
   - ComfyUI-Impact-Pack and ComfyUI-Impact-Subpack (search these two names
     via ComfyUI Manager once it's installed, rather than a raw git clone -
     they have install-time setup steps Manager handles for you)

3. Download these into the matching models/ subfolder. Verify each file's
   size with a HEAD request before saving (don't trust a filename alone -
   confirm content-length matches what's expected, retry on connection
   resets, they're common with Hugging Face). For any file below marked
   "search by filename" rather than given a direct URL, look it up on
   Hugging Face (huggingface.co/models) or Civitai (civitai.com) by that
   exact filename, confirm it's the right one from context (uploader,
   file size in the ballpark of similar quantizations), and use that
   source instead of guessing a URL.

   models/checkpoints/
   - sd_xl_base_1.0.safetensors <- https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors (~6.46GB)
   - sd_xl_refiner_1.0.safetensors <- https://huggingface.co/stabilityai/stable-diffusion-xl-refiner-1.0/resolve/main/sd_xl_refiner_1.0.safetensors (~5.66GB)
   - dreamshaperXL_alpha2Xl10.safetensors <- Civitai model id 112902 ("DreamShaper XL"), version "alpha2 (xl1.0)" (~6.46GB)

   models/unet/  (diffusion/UNET models)
   - flux1-dev-Q4_K_S.gguf <- https://huggingface.co/city96/FLUX.1-dev-gguf/resolve/main/flux1-dev-Q4_K_S.gguf (~6.34GB)
   - acestep_v1.5_turbo.safetensors <- https://huggingface.co/Comfy-Org/ace_step_1.5_ComfyUI_files/resolve/main/split_files/diffusion_models/acestep_v1.5_turbo.safetensors (~4.46GB)
   - Wan2.2-T2V-A14B-HighNoise-Q4_K_M.gguf <- search by filename (~9GB)
   - Wan2.2-T2V-A14B-LowNoise-Q4_K_M.gguf <- search by filename (~9GB)
   - Wan2.2-S2V-14B-Q4_K_M.gguf <- search by filename (~13GB) - only needed
     if pursuing the not-yet-working Image to Video mode, otherwise skip

   models/clip/  (text encoders)
   - clip_l.safetensors <- https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors (~0.25GB)
   - t5xxl_fp8_e4m3fn.safetensors <- https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors (~4.9GB)
   - umt5_xxl_fp8_e4m3fn_scaled.safetensors <- https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors (~6.3GB)
   - qwen_0.6b_ace15.safetensors <- https://huggingface.co/Comfy-Org/ace_step_1.5_ComfyUI_files/resolve/main/split_files/text_encoders/qwen_0.6b_ace15.safetensors (~1.1GB)
   - qwen_1.7b_ace15.safetensors <- https://huggingface.co/Comfy-Org/ace_step_1.5_ComfyUI_files/resolve/main/split_files/text_encoders/qwen_1.7b_ace15.safetensors (~3.45GB)
   - qwen_4b_ace15.safetensors <- https://huggingface.co/Comfy-Org/ace_step_1.5_ComfyUI_files/resolve/main/split_files/text_encoders/qwen_4b_ace15.safetensors (~7.8GB) - larger/optional ACE-Step text encoder

   models/vae/
   - flux_ae.safetensors <- search by filename "ae.safetensors" in a Flux
     VAE mirror repo (the official black-forest-labs one is gated/needs
     login; several ungated mirrors exist) (~0.31GB)
   - wan_2.1_vae.safetensors <- https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors (~0.24GB)
   - ace_1.5_vae.safetensors <- https://huggingface.co/Comfy-Org/ace_step_1.5_ComfyUI_files/resolve/main/split_files/vae/ace_1.5_vae.safetensors (~0.31GB)

   models/loras/
   - anime_lora_comfy_converted.safetensors, art_lora_comfy_converted.safetensors,
     disney_lora_comfy_converted.safetensors, mjv6_lora_comfy_converted.safetensors,
     realism_lora_comfy_converted.safetensors, scenery_lora_comfy_converted.safetensors
     <- all from https://huggingface.co/XLabs-AI/flux-lora-collection/resolve/main/<filename>
   - wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors,
     wan2.2_t2v_lightx2v_4steps_lora_v1.1_low_noise.safetensors
     <- search by filename (~1.15GB each) - 4-step speed LoRAs for Wan2.2 T2V

   models/upscalers/
   - 4x-UltraSharp.pth <- search by filename (~65MB) - a widely-mirrored
     standard ESRGAN upscaler, any legitimate source matching that size is fine

4. Studio's Python dependencies (uses the system Python, not ComfyUI's
   embedded one):
   ```
   python -m pip install -r studio/requirements.txt
   ```

Skip anything you don't actually plan to use - Wan2.2 alone is ~30GB and
the biggest chunk of this list. Check free disk space and VRAM (see
HARDWARE.md) before pulling all of it at once.
```

This prompt is a point-in-time snapshot of what's been downloaded during
this project - if you've added more since, extend it yourself so it stays
accurate for the next fresh clone.

## Status checklist

- [x] Ran `scripts/detect-hardware.ps1`, reviewed `HARDWARE.md` (RTX 3070 Ti Laptop, 8GB VRAM, 64GB RAM)
- [x] Ollama installed, `ollama --version` works
- [x] Ollama server running (models stored on `D:\ollama-models`)
- [x] Picked and pulled one small LLM to start (`llama3.2:3b`)
- [x] Docker Desktop installed and running (via WSL2)
- [x] Open WebUI running, reachable at http://localhost:3000
- [x] Open WebUI shows the Ollama model in its model picker
- [x] ComfyUI portable downloaded and extracted to `D:\ComfyUI\ComfyUI_windows_portable\`
- [x] ComfyUI running via `scripts/start-comfyui.ps1`, reachable at http://localhost:8188
- [x] ComfyUI wired to read models from this repo's `models/` folder (`extra_model_paths.yaml`)
- [x] First checkpoint model placed in `models/checkpoints/`
- [x] First image generated successfully in ComfyUI
- [x] First workflow exported as JSON into `workflows/`
- [x] Studio built and running, reachable at http://localhost:8899
- [x] Text to Image, Image to Image, Text to Video, and Text to Music modes wired up and validated in Studio
- [ ] Image to Video mode in Studio (blocked on converter support for nested subgraphs - see `studio/README.md`)

## Commit message convention

This repo uses a lightweight [Conventional Commits](https://www.conventionalcommits.org/)
style:

```
<type>: <short summary>

[optional body]
```

Types used here:
- `scaffold` - repo structure, gitignore, folder setup
- `docs` - README/HARDWARE.md/docs changes
- `scripts` - launch/setup/detection script changes
- `workflow` - adding/editing a ComfyUI workflow JSON
- `prompts` - adding/editing saved prompts
- `chore` - misc maintenance with no functional change

Examples: `scaffold: initial repo layout and gitignore`,
`workflow: add SDXL txt2img base workflow`,
`docs: update status checklist after ComfyUI setup`.

Never commit model weights or generated media - if `git status` shows a
`.safetensors`, `.ckpt`, or files under `outputs/`, check `.gitignore` before
committing.
