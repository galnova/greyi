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

5. **ComfyUI** - see `scripts/comfyui-note.md`. Uses its own portable
   Windows launcher (`run_nvidia_gpu.bat`), not a script in this repo.

## Starting / stopping

| Component      | Start                                   | Stop                                      |
|-----------------|-------------------------------------------|---------------------------------------------|
| Ollama          | `.\scripts\start-ollama.ps1`             | `Stop-Process -Name ollama`                 |
| Open WebUI      | `.\scripts\start-openwebui.ps1`          | `docker stop open-webui`                    |
| ComfyUI         | `run_nvidia_gpu.bat` (in its own folder) | Close the console window / Ctrl+C            |

## Where models go

Place downloaded model files into the matching `models/` subfolder
(`checkpoints`, `loras`, `vae`, `controlnet`, `upscalers`, `video`) - see
`models/README.md` for details and re-fetch instructions. Ollama manages its
own model store separately (`ollama list`, `ollama pull <model>`).

## Status checklist

- [ ] Ran `scripts/detect-hardware.ps1`, reviewed `HARDWARE.md`
- [ ] Ollama installed, `ollama --version` works
- [ ] Ollama server running (`scripts/start-ollama.ps1`)
- [ ] Picked and pulled one small LLM to start
- [ ] Docker Desktop installed and running
- [ ] Open WebUI running (`scripts/start-openwebui.ps1`), reachable at http://localhost:3000
- [ ] Open WebUI shows the Ollama model in its model picker
- [ ] ComfyUI portable downloaded and extracted (outside git tracking)
- [ ] ComfyUI running via `run_nvidia_gpu.bat`, reachable at http://localhost:8188
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
