# models/

This directory is intentionally **empty in git**. Model weights are large
(hundreds of MB to tens of GB each) and are excluded via `.gitignore` so the
repo stays small and clonable. Only the folder structure (via `.gitkeep`) and
this README are tracked.

## Layout

| Folder         | Contents                                                    |
|----------------|--------------------------------------------------------------|
| `checkpoints/` | Base Stable Diffusion / SDXL / video-gen checkpoints         |
| `loras/`       | LoRA fine-tune weights                                       |
| `vae/`         | Standalone VAE files                                         |
| `controlnet/`  | ControlNet models                                             |
| `upscalers/`   | ESRGAN / upscale models                                       |
| `video/`       | Video generation models (e.g. AnimateDiff, SVD)               |

Ollama's LLM weights are **not** stored here — Ollama manages its own model
store separately (see `scripts/start-ollama.ps1` and `ollama list`).

## Re-fetching models after a clone

Nothing here downloads automatically. To repopulate:

1. Run `scripts/detect-hardware.ps1` and check `HARDWARE.md` to confirm your
   VRAM budget.
2. Pick models sized appropriately for that VRAM (see `docs/` once model
   choices are made).
3. Download checkpoints/LoRAs/VAEs manually from their source (e.g.
   Civitai, Hugging Face) and place them in the matching subfolder above.
4. For Ollama models, use `ollama pull <model>` — see
   `scripts/start-ollama.ps1`.

Workflow JSON files in `workflows/` reference model **filenames**, so once a
model is placed in the right folder with the expected filename, existing
workflows should pick it up without edits.
