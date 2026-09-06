# ComfyUI

ComfyUI is **not** launched by a script in this repo. Use the official
portable Windows build's own launcher instead:

1. Download "ComfyUI portable" for Windows from the official ComfyUI GitHub
   releases (NVIDIA GPU build) - this is a self-contained folder with its own
   embedded Python, so it doesn't need a separate Python install.
2. Extract it **outside this repo** (or inside, but it's gitignored either
   way - see `.gitignore`: `ComfyUI_windows_portable/`, `python_embeded/`).
3. Start it by double-clicking (or running from a terminal):
       run_nvidia_gpu.bat
   This launches ComfyUI's own server, by default at http://localhost:8188.
4. Point ComfyUI's `models/` folders at (or symlink/copy into) this repo's
   `models/checkpoints`, `models/loras`, `models/vae`, `models/controlnet`,
   `models/upscalers`, `models/video` so model organization stays consistent
   with what's documented here.
5. Save/export workflows as JSON into this repo's `workflows/` folder so they
   stay tracked in git (workflow JSON is small text, unlike the models it
   references).

If your GPU isn't NVIDIA (e.g. no dedicated GPU, or AMD), use the
corresponding launcher ComfyUI ships (`run_cpu.bat`, DirectML build, etc.) -
check `HARDWARE.md` first to know what you're working with.
