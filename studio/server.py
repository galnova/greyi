"""
Studio - a small local web app that gives you a Grok-Imagine-style toggle
UI (Text/Image -> Image/Video/Music) in front of your existing ComfyUI
workflows, driving them through ComfyUI's own /prompt API rather than
hand-editing workflow JSON each time.

Run: python studio/server.py   (see scripts/start-studio.ps1)
"""
import json
import pathlib
import shutil
import time
import urllib.request
import urllib.error
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import converter

ROOT = pathlib.Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / "workflows"
OUTPUTS = ROOT / "outputs"
COMFYUI_URL = "http://localhost:8188"
OLLAMA_URL = "http://localhost:11434"
CHAT_NUM_CTX = 8192  # explicit context window so token-remaining has a real ceiling to measure against

app = FastAPI(title="Studio")

# --- per-mode config -------------------------------------------------
# node ids are stable identifiers baked into each workflow file (searched
# across top-level nodes AND any nested subgraphs by find_node_by_id).
MODES = {
    "text2image": {
        "label": "Text to Image",
        "workflow": WORKFLOWS / "text2img_dreamshaper.json",
        "positive_nodes": [6, 15],
        "negative_nodes": [7, 16],
        "image_node": None,
        "output_kind": "image",
    },
    "image2image": {
        "label": "Image to Image",
        "workflow": WORKFLOWS / "img2img_dreamshaper.json",
        "positive_nodes": [6, 15],
        "negative_nodes": [7, 16],
        "image_node": 26,
        "output_kind": "image",
    },
    "text2video": {
        "label": "Text to Video",
        "workflow": WORKFLOWS / "wan22_t2v_gguf.json",
        "positive_nodes": [89],
        "negative_nodes": [72],
        "image_node": None,
        "output_kind": "video",
    },
    "text2music": {
        "label": "Text to Music",
        "workflow": WORKFLOWS / "ace_step_audio.json",
        "positive_nodes": [94],  # widgets_values[0] = tags/style description
        "negative_nodes": [],
        "image_node": None,
        "output_kind": "audio",
    },
    "image2video": {
        "label": "Image to Video",
        "workflow": None,  # not wired yet - see studio/README.md
        "positive_nodes": [],
        "negative_nodes": [],
        "image_node": None,
        "output_kind": "video",
        "disabled": True,
        "disabled_reason": "Not wired up yet - the S2V workflow's nested "
                            "'extend' subgraphs need more converter work.",
    },
    "text2text": {
        "label": "Chat",
        "ollama_models": ["qwen2.5-coder:7b", "llama3.2:3b"],
        "image_node": None,
        "output_kind": "text",
    },
}

jobs = {}  # job_id -> {prompt_id, mode, status, ...}


def _set_text(node, index, value):
    while len(node["widgets_values"]) <= index:
        node["widgets_values"].append("")
    node["widgets_values"][index] = value


def build_prompt(mode_key, prompt_text, negative_text, image_filename):
    cfg = MODES[mode_key]
    if cfg.get("disabled"):
        raise HTTPException(400, cfg.get("disabled_reason", "This mode isn't available yet."))

    data = converter.load_workflow(cfg["workflow"])

    for nid in cfg["positive_nodes"]:
        node = converter.find_node_by_id(data, nid)
        _set_text(node, 0, prompt_text)

    for nid in cfg["negative_nodes"]:
        node = converter.find_node_by_id(data, nid)
        _set_text(node, 0, negative_text or "")

    if cfg["image_node"] is not None:
        if not image_filename:
            raise HTTPException(400, f"{cfg['label']} requires an uploaded image.")
        node = converter.find_node_by_id(data, cfg["image_node"])
        _set_text(node, 0, image_filename)

    return converter.convert_data(data)


def comfy_post(path, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(f"{COMFYUI_URL}{path}", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8")
        raise HTTPException(400, detail)


def comfy_get(path):
    with urllib.request.urlopen(f"{COMFYUI_URL}{path}", timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ollama_generate(model, prompt):
    body = json.dumps({
        "model": model, "prompt": prompt, "stream": False,
        "options": {"num_ctx": CHAT_NUM_CTX},
    }).encode("utf-8")
    req = urllib.request.Request(f"{OLLAMA_URL}/api/generate", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            prompt_tokens = data.get("prompt_eval_count", 0)
            response_tokens = data.get("eval_count", 0)
            used = prompt_tokens + response_tokens
            return {
                "text": data["response"],
                "tokens_used": used,
                "tokens_remaining": max(CHAT_NUM_CTX - used, 0),
                "num_ctx": CHAT_NUM_CTX,
            }
    except TimeoutError:
        raise HTTPException(504, "Ollama took over 5 minutes to respond - it's likely starved for GPU "
                                  "by a heavy ComfyUI job running at the same time. Wait for that to "
                                  "finish (or clear its queue) and try again.")
    except (urllib.error.URLError, OSError) as e:
        raise HTTPException(502, f"Ollama not reachable ({e}). Is it running? See scripts/start-ollama.ps1.")


@app.get("/api/modes")
def api_modes():
    return {
        key: {
            "label": cfg["label"],
            "output_kind": cfg["output_kind"],
            "needs_image": cfg["image_node"] is not None,
            "disabled": cfg.get("disabled", False),
            "disabled_reason": cfg.get("disabled_reason"),
            "models": cfg.get("ollama_models"),
        }
        for key, cfg in MODES.items()
    }


@app.post("/api/upload")
async def api_upload(file: UploadFile = File(...)):
    contents = await file.read()
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{file.filename}\"\r\n"
        f"Content-Type: {file.content_type}\r\n\r\n"
    ).encode() + contents + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result


@app.post("/api/generate")
def api_generate(
    mode: str = Form(...),
    prompt: str = Form(...),
    negative: str = Form(""),
    image_filename: str = Form(None),
    model: str = Form(None),
):
    if mode not in MODES:
        raise HTTPException(404, f"unknown mode {mode}")
    cfg = MODES[mode]
    job_id = uuid.uuid4().hex

    if cfg.get("ollama_models"):
        # Text modes bypass ComfyUI entirely - call Ollama directly and
        # store the finished result right away (no queue/poll needed).
        chosen = model if model in cfg["ollama_models"] else cfg["ollama_models"][0]
        result = ollama_generate(chosen, prompt)
        jobs[job_id] = {"mode": mode, "created": time.time(), "status": "success", **result}
        return {"job_id": job_id}

    prompt_json, _included = build_prompt(mode, prompt, negative, image_filename)
    client_id = uuid.uuid4().hex
    result = comfy_post("/prompt", {"prompt": prompt_json, "client_id": client_id})
    prompt_id = result["prompt_id"]

    jobs[job_id] = {"prompt_id": prompt_id, "mode": mode, "created": time.time()}
    return {"job_id": job_id, "prompt_id": prompt_id}


@app.get("/api/status/{job_id}")
def api_status(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(404, "unknown job")

    if job.get("status") == "success" and "text" in job:
        return {
            "status": "success", "text": job["text"],
            "tokens_used": job.get("tokens_used"),
            "tokens_remaining": job.get("tokens_remaining"),
            "num_ctx": job.get("num_ctx"),
        }

    hist = comfy_get(f"/history/{job['prompt_id']}")
    entry = hist.get(job["prompt_id"])
    if entry is None:
        queue = comfy_get("/queue")
        running_ids = {q[1] for q in queue.get("queue_running", [])}
        pending_ids = {q[1] for q in queue.get("queue_pending", [])}
        if job["prompt_id"] in running_ids:
            return {"status": "running"}
        if job["prompt_id"] in pending_ids:
            return {"status": "pending"}
        return {"status": "unknown"}

    status = entry.get("status", {})
    if not status.get("completed"):
        return {"status": "running"}
    if status.get("status_str") != "success":
        return {"status": "error", "detail": status}

    outputs = []
    kind = MODES[job["mode"]]["output_kind"]
    for node_id, out in entry.get("outputs", {}).items():
        for media_key in ("images", "videos", "audio", "gifs"):
            for item in out.get(media_key, []) or []:
                outputs.append({
                    "filename": item["filename"],
                    "subfolder": item.get("subfolder", ""),
                    "type": item.get("type", "output"),
                    "url": f"{COMFYUI_URL}/view?filename={item['filename']}&subfolder={item.get('subfolder','')}&type={item.get('type','output')}",
                })

    _save_copies(outputs, kind)
    return {"status": "success", "outputs": outputs}


def _save_copies(outputs, kind):
    dest_dir = {"image": OUTPUTS / "images", "video": OUTPUTS / "videos", "audio": OUTPUTS / "audio"}.get(kind)
    if dest_dir is None:
        return
    dest_dir.mkdir(parents=True, exist_ok=True)
    comfy_output_dir = pathlib.Path("D:/ComfyUI/ComfyUI_windows_portable/ComfyUI/output")
    for o in outputs:
        src = comfy_output_dir / o["subfolder"] / o["filename"]
        if src.exists():
            dst = dest_dir / o["filename"]
            if not dst.exists():
                try:
                    shutil.copy2(src, dst)
                except OSError:
                    pass


app.mount("/", StaticFiles(directory=str(pathlib.Path(__file__).parent / "static"), html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8899)
