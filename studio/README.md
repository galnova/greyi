# Studio

A small local web app that gives you a Grok-Imagine-style toggle UI (mode
pills, prompt box, optional image upload, Generate) in front of ComfyUI,
instead of hand-editing workflow JSON or navigating the node graph each
time you want to generate something.

It doesn't run its own models - it drives your existing ComfyUI install
through its `/prompt` API, using the workflow files in `../workflows/` as
templates. ComfyUI must already be running (`scripts/start-comfyui.ps1`).

## Running it

```
.\scripts\start-studio.ps1
```

Opens on http://localhost:8899.

## How it works

- `converter.py` converts a saved ComfyUI workflow JSON (the graph format
  the frontend saves) into the flat "API prompt" format `/prompt` expects.
  This includes flattening ComfyUI's newer "subgraph" nodes (used by the
  video/audio templates) and correctly resolving widget values against
  ComfyUI's live `/object_info` schema - see the module docstring for the
  quirks this handles (promoted-widget proxies, the seed/
  control_after_generate pairing, PrimitiveNode inlining).
- `server.py` is a thin FastAPI app: for each mode it knows which node
  ids in the workflow hold the positive/negative prompt text and (for
  image-input modes) which node is the `LoadImage`. It mutates those,
  converts, submits to ComfyUI, and polls `/history` for the result.
- `static/index.html` is the UI.

## Modes

| Mode | Workflow | Status |
|---|---|---|
| Text to Image | `text2img_dreamshaper.json` | working |
| Image to Image | `img2img_dreamshaper.json` (new, single-image) | working |
| Text to Video | `wan22_t2v_gguf.json` | working |
| Text to Music | `ace_step_audio.json` | working |
| Image to Video | `wan22_i2v_gguf.json` | working |

Each mode's `models` entries become the UI's Model dropdown. Both Wan modes
offer a fast 4-step option (lightx2v LoRAs, CFG 1 - the negative prompt has
no effect) and a quality 20-step option (CFG 3.5). Image to Video is a flat
graph with no subgraphs; Studio sizes it to the uploaded image's aspect ratio
at about 640x640 pixels so portrait/landscape shots aren't center-cropped.

Before every ComfyUI job Studio unloads any Ollama chat model still sitting
in VRAM - on an 8GB card a resident chat model pushes Wan into RAM offload
(hours per clip instead of minutes).

## Adding a mode later

Add an entry to `MODES` in `server.py`: point `workflow` at a file in
`../workflows/`, and set `positive_nodes` / `negative_nodes` / `image_node`
to the relevant node ids (find them by opening the workflow JSON - ids are
stable and unique across the whole file, including inside subgraphs).
