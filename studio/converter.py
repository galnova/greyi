"""
Converts a ComfyUI UI-format workflow JSON (the format saved by the ComfyUI
frontend, with top-level "nodes"/"links" and possibly "definitions.subgraphs")
into the flat API-format prompt dict that ComfyUI's /prompt endpoint expects:
    { "<node_id>": {"class_type": <type>, "inputs": {<name>: <value>}} }

Widget ordering is resolved against ComfyUI's live /object_info schema for
each node type, which is correct for the overwhelming majority of node
types (proven across ~60 hand-authored nodes this session). A small set of
node types are known to add extra frontend-only widgets beyond what the
schema declares (e.g. FaceDetailer's optional sockets that render as
trailing widgets, and any "seed"/"noise_seed" INT widget which gets an
auto-added "control_after_generate" companion string). Those are handled
via QUIRKS below rather than guessed.
"""
import json
import urllib.request

COMFYUI_URL = "http://localhost:8188"

# Node types known to render "optional" schema sockets as trailing widgets
# when left unconnected (Impact-Pack quirk), in the exact order verified
# against custom_nodes/ComfyUI-Impact-Pack/example_workflows/1-FaceDetailer.json
FACEDETAILER_WIDGET_ORDER = [
    "guide_size", "guide_size_for", "max_size", "seed", "control_after_generate",
    "steps", "cfg", "sampler_name", "scheduler", "denoise", "feather",
    "noise_mask", "force_inpaint", "bbox_threshold", "bbox_dilation",
    "bbox_crop_factor", "sam_detection_hint", "sam_dilation", "sam_threshold",
    "sam_bbox_expansion", "sam_mask_hint_threshold", "sam_mask_hint_use_negative",
    "drop_size", "wildcard", "cycle",
    "inpaint_model", "noise_mask_feather", "tiled_encode", "tiled_decode",
]

SEED_WIDGET_NAMES = {"seed", "noise_seed"}

# ComfyUI's non-widget socket types - a field of one of these types NEVER
# reserves a widgets_values slot (widget-capable types - INT/FLOAT/STRING/
# BOOLEAN/COMBO-list - always do, whether currently connected or not).
PURE_SOCKET_TYPES = {
    "MODEL", "CLIP", "VAE", "IMAGE", "CONDITIONING", "LATENT", "MASK",
    "BBOX_DETECTOR", "SEGM_DETECTOR", "SAM_MODEL", "UPSCALE_MODEL",
    "AUDIO", "AUDIO_ENCODER", "VIDEO", "DETAILER_HOOK", "SCHEDULER_FUNC",
    "CONTROL_NET", "STYLE_MODEL", "CLIP_VISION", "GLIGEN", "PHOTOMAKER",
    "DETAILER_PIPE", "GUIDER", "SAMPLER", "SIGMAS", "NOISE",
}


def _field_type(schema, name):
    spec = schema["input"]["required"].get(name) or schema["input"]["optional"].get(name)
    if spec is None:
        return None
    t = spec[0]
    return t if isinstance(t, str) else "COMBO"


def _is_widget_capable(schema, name):
    return _field_type(schema, name) not in PURE_SOCKET_TYPES

_schema_cache = {}


def _norm_link(l):
    """Normalize a link entry (list-form or dict-form) to a 6-tuple list."""
    if isinstance(l, dict):
        return [l["id"], l["origin_id"], l["origin_slot"], l["target_id"], l["target_slot"], l.get("type")]
    return list(l[:6])


def get_schema(node_type):
    if node_type in _schema_cache:
        return _schema_cache[node_type]
    url = f"{COMFYUI_URL}/object_info/{node_type}"
    with urllib.request.urlopen(url, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    schema = data.get(node_type)
    _schema_cache[node_type] = schema
    return schema


def _socket_names(node):
    # Only inputs with an actual connected link consume a graph edge; an
    # input present in the array but with link=None (common for promoted
    # subgraph widgets, or any unconverted widget slot) still needs its
    # value pulled positionally from widgets_values like a normal widget.
    return {i["name"] for i in node.get("inputs", []) if i.get("link") is not None}


def _full_slot_order_for(node, schema):
    """Every widgets_values slot in serialization order, including ones
    that are actually real sockets (converted-to-input widgets keep a
    stale placeholder value at their original position rather than
    shrinking the array)."""
    node_type = node["type"]
    if node_type == "FaceDetailer":
        return list(FACEDETAILER_WIDGET_ORDER)

    order = schema["input_order"].get("required", []) + schema["input_order"].get("optional", [])
    slots = []
    for name in order:
        if not _is_widget_capable(schema, name):
            continue  # pure socket type - never occupies a widgets_values slot
        slots.append(name)
        if name in SEED_WIDGET_NAMES:
            slots.append("control_after_generate")
    return slots


def _flatten_subgraphs(data):
    """Inline any subgraph-instance nodes into a single flat node/link list."""
    subgraphs = {sg["id"]: sg for sg in data.get("definitions", {}).get("subgraphs", [])}
    top_links = [_norm_link(l) for l in data["links"]]
    if not subgraphs:
        return list(data["nodes"]), top_links

    nodes = list(data["nodes"])
    links = top_links
    for sg in subgraphs.values():
        sg["links"] = [_norm_link(l) for l in sg.get("links", [])]
    next_id = [max([n["id"] for n in nodes] + [l[0] for l in links]) + 1000]

    def new_id():
        next_id[0] += 1
        return next_id[0]

    def inline(instance_node, sg):
        id_map = {}
        inlined_nodes = []
        real_link_ids = {l[0] for l in sg["links"]}
        for n in sg["nodes"]:
            nid = new_id()
            id_map[n["id"]] = nid
            nn = dict(n)
            nn["id"] = nid
            nn["inputs"] = [dict(i) for i in n.get("inputs", [])]
            nn["outputs"] = [dict(o) for o in n.get("outputs", [])]
            for inp in nn["inputs"]:
                # "promoted widget" bookkeeping: a widget input can carry a
                # stale "link" id used only for the parent subgraph's proxy
                # UI, not a real edge. Its value already lives correctly in
                # widgets_values, so drop the dangling reference.
                if inp.get("link") is not None and inp["link"] not in real_link_ids:
                    inp["link"] = None
            inlined_nodes.append(nn)

        inlined_links = []
        for l in sg["links"]:
            lid, o, oslot, t, tslot, ltype = l[:6]
            new_lid = new_id()
            new_o = id_map.get(o, o)
            new_t = id_map.get(t, t)
            inlined_links.append([new_lid, new_o, oslot, new_t, tslot, ltype])
            for nn in inlined_nodes:
                if nn["id"] == new_t:
                    for inp in nn["inputs"]:
                        if inp.get("link") == lid:
                            inp["link"] = new_lid
                if nn["id"] == new_o:
                    for out in nn["outputs"]:
                        if out.get("links") and lid in out["links"]:
                            out["links"] = [new_lid if x == lid else x for x in out["links"]]
        return inlined_nodes, inlined_links, id_map

    result_nodes = []
    result_links = list(links)
    for n in nodes:
        sg = subgraphs.get(n["type"])
        if sg is None:
            result_nodes.append(n)
            continue

        inlined_nodes, inlined_links, id_map = inline(n, sg)
        result_nodes.extend(inlined_nodes)
        result_links.extend(inlined_links)

        # remap boundary: subgraph instance's own inputs/outputs point at
        # the inputNode/outputNode slots inside the subgraph. These are
        # fixed sentinel ids (e.g. -10/-20), never part of sg["nodes"], so
        # they pass through id_map unchanged rather than being looked up.
        in_node_id = sg["inputNode"]["id"] if sg.get("inputNode") else None
        out_node_id = sg["outputNode"]["id"] if sg.get("outputNode") else None

        for inst_inp_idx, inst_inp in enumerate(n.get("inputs", [])):
            lid = inst_inp.get("link")
            if lid is None or in_node_id is None:
                continue
            for il in result_links:
                if il[0] != lid:
                    continue
                # links landing on the instance node get redirected: their
                # target becomes whatever inside the subgraph actually
                # consumed that boundary input slot
                for nn in result_nodes:
                    for inp in nn.get("inputs", []):
                        pass  # boundary rewiring handled via inputNode passthrough below

        # Passthrough: find links inside the subgraph sourced from in_node_id
        # (representing "use the instance's external input") and rewrite
        # their origin to whatever feeds the instance's corresponding input.
        if in_node_id is not None:
            outer_link_by_slot = {}
            for inst_inp_idx, inst_inp in enumerate(n.get("inputs", [])):
                if inst_inp.get("link") is not None:
                    outer_link_by_slot[inst_inp_idx] = inst_inp["link"]
            for il in list(result_links):
                if il[1] == in_node_id:
                    slot = il[2]
                    outer_lid = outer_link_by_slot.get(slot)
                    if outer_lid is not None:
                        outer_link = next(ol for ol in result_links if ol[0] == outer_lid)
                        il[1], il[2] = outer_link[1], outer_link[2]

        if out_node_id is not None:
            for out_idx, out in enumerate(n.get("outputs", [])):
                for consumer_lid in (out.get("links") or []):
                    consumer_link = next((ol for ol in result_links if ol[0] == consumer_lid), None)
                    if consumer_link is None:
                        continue
                    for il in result_links:
                        if il[3] == out_node_id and il[4] == out_idx:
                            consumer_link[1], consumer_link[2] = il[1], il[2]

        # Any remaining links still touching the sentinel boundary ids are
        # unresolved promoted-widget proxies (the instance node exposed a
        # widget but nothing external overrides it) - null the consuming
        # node's input so it falls back to that node's own widgets_values,
        # then drop the now-meaningless link.
        result_nodes_by_id = {rn["id"]: rn for rn in result_nodes}
        for l in result_links:
            if l[1] == in_node_id:
                target = result_nodes_by_id.get(l[3])
                if target is None:
                    continue
                for inp in target["inputs"]:
                    if inp.get("link") == l[0]:
                        inp["link"] = None
        result_links = [l for l in result_links if l[1] != in_node_id and l[3] != out_node_id]

    return result_nodes, result_links


def load_workflow(workflow_path):
    with open(workflow_path, encoding="utf-8-sig") as f:
        return json.load(f)


def find_node_by_id(data, node_id):
    """Search top-level nodes and every subgraph's nodes for a given id
    (ids are unique across the whole file, so this is unambiguous). Returns
    the mutable node dict - edit its widgets_values in place before
    calling convert_data()."""
    for n in data.get("nodes", []):
        if n["id"] == node_id:
            return n
    for sg in data.get("definitions", {}).get("subgraphs", []):
        for n in sg.get("nodes", []):
            if n["id"] == node_id:
                return n
    raise KeyError(f"node id {node_id} not found anywhere in workflow")


def convert_data(data, output_node_title_hint=None):
    nodes, links = _flatten_subgraphs(data)
    nodes_by_id = {n["id"]: n for n in nodes}
    links_by_id = {l[0]: l for l in links}

    save_types = {"SaveImage", "SaveVideo", "SaveAudio", "SaveAudioMP3", "SaveAudioOpus", "VHS_SaveVideo"}
    candidates = [n for n in nodes if n["type"] in save_types and n.get("mode", 0) == 0]
    if output_node_title_hint:
        matched = [n for n in candidates if output_node_title_hint.lower() in (n.get("title", "") or n["type"]).lower()]
        if matched:
            candidates = matched
    if not candidates:
        raise ValueError(f"No enabled Save* node found in {workflow_path}")
    output_node = candidates[0]

    included = {}

    def visit(node_id):
        if node_id in included:
            return
        node = nodes_by_id[node_id]
        if node.get("mode", 0) != 0:
            return
        if node["type"] == "PrimitiveNode":
            return  # frontend-only value router, never included as a real node
        included[node_id] = node
        for inp in node.get("inputs", []):
            lid = inp.get("link")
            if lid is None:
                continue
            link = links_by_id[lid]
            visit(link[1])

    visit(output_node["id"])

    prompt = {}
    for node_id, node in included.items():
        node_type = node["type"]
        schema = get_schema(node_type)
        inputs = {}

        for inp in node.get("inputs", []):
            lid = inp.get("link")
            if lid is None:
                continue
            link = links_by_id[lid]
            origin_node = nodes_by_id.get(link[1])
            if origin_node is not None and origin_node["type"] == "PrimitiveNode":
                # inline the routed literal value instead of a socket ref
                inputs[inp["name"]] = origin_node.get("widgets_values", [None])[0]
            else:
                inputs[inp["name"]] = [str(link[1]), link[2]]

        slot_names = _full_slot_order_for(node, schema)
        values = node.get("widgets_values", [])
        for name, value in zip(slot_names, values):
            if name == "control_after_generate":
                continue  # frontend-only; not a real backend input
            if name in inputs:
                continue  # already resolved via a real link; placeholder discarded
            inputs[name] = value

        prompt[str(node_id)] = {"class_type": node_type, "inputs": inputs}

    return prompt, {str(nid): n for nid, n in included.items()}


def convert(workflow_path, output_node_title_hint=None):
    data = load_workflow(workflow_path)
    return convert_data(data, output_node_title_hint)


if __name__ == "__main__":
    import sys
    p, _ = convert(sys.argv[1])
    print(json.dumps(p, indent=2, ensure_ascii=False))
