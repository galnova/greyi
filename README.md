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

Note: on an 8GB VRAM card, running a loaded Ollama model and heavy ComfyUI
generation at the same time can be tight - if you hit out-of-memory errors,
close one while using the other.

## Repo layout

```
scripts/      Setup, detection, and launch scripts (tracked)
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

## Starting / stopping

| Component         | Start                                                            | Stop                                                    |
|--------------------|--------------------------------------------------------------------|------------------------------------------------------------|
| Ollama + Open WebUI (one-click) | Desktop shortcut "Launch AI Chat", or `.\scripts\start-all.ps1` | Close Docker Desktop, or the two "Stop" commands below |
| Ollama             | `.\scripts\start-ollama.ps1`                                      | `Stop-Process -Name ollama`                               |
| Open WebUI         | `.\scripts\start-openwebui.ps1`                                   | `docker stop open-webui`                                  |
| ComfyUI            | Desktop shortcut "Launch ComfyUI", or `.\scripts\start-comfyui.ps1` | Close the ComfyUI console window                        |

## Where models go

Place downloaded model files into the matching `models/` subfolder
(`checkpoints`, `loras`, `vae`, `controlnet`, `upscalers`, `video`) - see
`models/README.md` for details and re-fetch instructions. Ollama manages its
own model store separately (`ollama list`, `ollama pull <model>`).

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
- [ ] First checkpoint model placed in `models/checkpoints/`
- [ ] First image generated successfully in ComfyUI
- [ ] First workflow exported as JSON into `workflows/`

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
