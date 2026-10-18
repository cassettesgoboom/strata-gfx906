#!/usr/bin/env python3
"""CPU-only validator/comparator for the model-declared native state trace v3 contract.

The comparator checks supplied descriptors and digests. It cannot authenticate capture,
provenance, device synchronization, or the bytes from which a producer computed a digest.
"""

from __future__ import annotations

import argparse
import os
import json
import re
import stat
from pathlib import Path
from typing import Any

try:
    import jsonschema
except ImportError:  # Fail closed with a useful message when run outside the pinned CI environment.
    jsonschema = None


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "benchmarks/gfx906/fixtures/native-runtime-parity-trace-v3.schema.json"
CONTRACT = ROOT / "benchmarks/gfx906/fixtures/native-runtime-parity-contract-v3.json"
MAX_REQUESTS = 128
MAX_COMMITS = 100_000
MAX_TOTAL_COMMITS = 4_096
MAX_TOTAL_COMPONENTS = 262_144
MAX_TRACE_BYTES = 64 * 1024 * 1024
MAX_TOKEN_IDS = 4_096
MAX_CONTEXT = 262_144
MAX_RING = 65_536
MAX_COMPONENTS = 160
MAX_COMPONENT_BYTES = 2_147_483_648
CANONICAL_SERIALIZATION = "strata_component_payload_v1"
COMPONENT_KINDS = (
    "gdn_recurrence", "gdn_conv_history", "qsa_kv_key", "qsa_kv_value",
    "qsa_idx_tail", "qsa_idx_dead", "qsa_idx_pooled", "qsa_idx_block_pos",
    "ple_history", "ple_previous_token_ids", "mtp_kv_key", "mtp_kv_value",
    "mtp_ring_mapping",
)
PROVENANCE_FIELDS = (
    "source_commit", "binary_sha256", "model_sha256", "tokenizer_sha256",
    "mtp_sha256", "command_sha256", "device_and_runtime", "trace_capture_method",
)
REQUEST_FIELDS = (
    "cache_key_sha256", "cache_reused_tokens", "cache_fresh_tokens",
    "input_token_count", "input_token_tail_ids", "input_token_ids_sha256", "sampler_state_sha256", "initial_checkpoint",
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class TraceError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise TraceError(message)


def _is_int(value: Any) -> bool:
    return type(value) is int


def _sha(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def load(path: Path) -> dict[str, Any]:
    fd = None
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
        file_stat = os.fstat(fd)
        if not stat.S_ISREG(file_stat.st_mode):
            raise TraceError(f"{path}: trace input must be a regular file")
        size = file_stat.st_size
        if size > MAX_TRACE_BYTES:
            raise TraceError(f"{path}: trace document exceeds {MAX_TRACE_BYTES} byte limit")
        with os.fdopen(fd, "rb") as stream:
            fd = None
            raw = stream.read(MAX_TRACE_BYTES + 1)
        if len(raw) > MAX_TRACE_BYTES:
            raise TraceError(f"{path}: trace document exceeds {MAX_TRACE_BYTES} byte limit")
        value = json.loads(raw)
    except TraceError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TraceError(f"{path}: {exc}") from exc
    finally:
        if fd is not None:
            os.close(fd)
    _need(isinstance(value, dict), f"{path}: expected JSON object")
    return value


def _validate_schema(trace: dict[str, Any], label: str) -> None:
    if jsonschema is None:
        raise TraceError("jsonschema is required; install tests/gfx906/requirements-schema.txt")
    try:
        schema = json.loads(SCHEMA.read_text())
        jsonschema.Draft202012Validator.check_schema(schema)
        error = next(iter(jsonschema.Draft202012Validator(schema).iter_errors(trace)), None)
    except (OSError, json.JSONDecodeError, jsonschema.SchemaError) as exc:
        raise TraceError(f"{label}: cannot load v3 schema: {exc}") from exc
    if error is not None:
        path = ".".join(str(part) for part in error.absolute_path) or "$"
        raise TraceError(f"{label}: schema {path}: {error.message}")


def _preflight_trace_bounds(trace: dict[str, Any], label: str) -> None:
    """Reject aggregate fan-out before JSON Schema walks every nested component."""
    requests = trace.get("requests")
    if not isinstance(requests, list):
        return  # The schema will produce the structural error.
    _need(len(requests) <= MAX_REQUESTS, f"{label}: request count exceeds {MAX_REQUESTS}")
    total_commits = 0
    total_components = 0
    for request in requests:
        if not isinstance(request, dict):
            continue
        initial = request.get("initial_checkpoint")
        if isinstance(initial, dict) and isinstance(initial.get("components"), list):
            total_components += len(initial["components"])
        commits = request.get("commits")
        if not isinstance(commits, list):
            continue
        total_commits += len(commits)
        _need(total_commits <= MAX_TOTAL_COMMITS,
              f"{label}: total commit count exceeds {MAX_TOTAL_COMMITS}")
        for commit in commits:
            if isinstance(commit, dict) and isinstance(commit.get("components"), list):
                total_components += len(commit["components"])
            _need(total_components <= MAX_TOTAL_COMPONENTS,
                  f"{label}: total component count exceeds {MAX_TOTAL_COMPONENTS}")
    _need(total_components <= MAX_TOTAL_COMPONENTS,
          f"{label}: total component count exceeds {MAX_TOTAL_COMPONENTS}")


def _architecture(trace: dict[str, Any], label: str) -> tuple[dict[str, Any], list[tuple[str, int | None, str]]]:
    arch = trace["architecture"]
    layers = arch["layer_count"]
    _need(_is_int(layers) and 1 <= layers <= 512, f"{label}: architecture.layer_count is out of bounds")
    gdn = arch["gdn_layers"]
    qsa = arch["qsa_layers"]
    _need(gdn == sorted(gdn) and qsa == sorted(qsa), f"{label}: architecture layer lists must be ordered")
    _need(set(gdn).isdisjoint(qsa) and sorted(gdn + qsa) == list(range(layers)),
          f"{label}: GDN and QSA layer lists must partition every model layer exactly once")

    gg, qg, pg, mg = (arch[name] for name in ("gdn_geometry", "qsa_geometry", "ple_geometry", "mtp_geometry"))
    _need(qg["head_dim"] <= 16384 and qg["idx_dim"] <= 16384 and qg["kv_heads"] <= 256,
          f"{label}: QSA geometry exceeds bounds")
    _need(gg["state_size"] <= 16384 and gg["value_heads"] <= 4096 and gg["conv_channels"] <= 1_000_000,
          f"{label}: GDN geometry exceeds bounds")
    _need(pg["history_rows"] <= MAX_CONTEXT and pg["history_channels"] <= 1_000_000 and pg["previous_token_count"] == 2,
          f"{label}: PLE geometry exceeds bounds or must retain exactly two predecessor IDs")
    _need(mg["head_dim"] <= 16384 and mg["kv_heads"] <= 256 and 1 <= mg["ring_capacity_cells"] <= MAX_RING,
          f"{label}: MTP geometry exceeds bounds")
    expected: list[tuple[str, int | None, str]] = []
    for layer in range(layers):
        if layer in gdn:
            expected.extend((("gdn_recurrence", layer, f"gdn_recurrence@{layer}"),
                             ("gdn_conv_history", layer, f"gdn_conv_history@{layer}")))
        else:
            for kind in ("qsa_kv_key", "qsa_kv_value", "qsa_idx_tail", "qsa_idx_dead", "qsa_idx_pooled", "qsa_idx_block_pos"):
                expected.append((kind, layer, f"{kind}@{layer}"))
    expected.extend((kind, None, kind) for kind in ("ple_history", "ple_previous_token_ids",
                                                     "mtp_kv_key", "mtp_kv_value", "mtp_ring_mapping"))
    _need(len(expected) <= MAX_COMPONENTS, f"{label}: model requires more than {MAX_COMPONENTS} state components")
    return arch, expected


def _expected_counts(expected: list[tuple[str, int | None, str]]) -> dict[str, int]:
    return {kind: sum(1 for item_kind, _, _ in expected if item_kind == kind) for kind in COMPONENT_KINDS}


def _validate_state_formats(commit: dict[str, Any], arch: dict[str, Any], label: str) -> None:
    formats = commit["state_formats"]
    qsa_layers = arch["qsa_layers"]
    expected_keys = {"mtp", *(f"qsa_layer_{layer}" for layer in qsa_layers)}
    _need(set(formats) == expected_keys, f"{label}: state_formats must declare MTP and every QSA layer exactly once")
    common_fields = {"kv_format", "key_rotation", "value_rotation", "kv_mode", "page_size_cells"}
    for key, state in formats.items():
        is_mtp = key == "mtp"
        expected_fields = common_fields | ({"ring_slots_by_logical_position"} if is_mtp else {"idx_block_pos_value"})
        _need(set(state) == expected_fields,
              f"{label}: {key}: format fields must be exactly {sorted(expected_fields)}")
        geom = arch["mtp_geometry"] if is_mtp else arch["qsa_geometry"]
        _need(state["page_size_cells"] == geom["page_size_cells"], f"{label}: {key}: page size differs from declared architecture")
        fmt = state["kv_format"]
        rotations = (state["key_rotation"], state["value_rotation"])
        allowed = {
            "fp16": {("none", "none")},
            "int8": {("none", "none"), ("walsh_hadamard", "walsh_hadamard")},
            "q4_0": {("walsh_hadamard", "walsh_hadamard")},
            "hybrid_k8v4": {("none", "walsh_hadamard")},
        }
        _need(rotations in allowed[fmt], f"{label}: {key}: rotation does not match KV encoding")
        _need(state["kv_mode"] == "ring" if is_mtp else state["kv_mode"] in {"resident", "streamed"},
              f"{label}: {key}: invalid KV mode")
        if not is_mtp:
            _need(_is_int(state.get("idx_block_pos_value")) and 0 <= state["idx_block_pos_value"] < MAX_CONTEXT,
                  f"{label}: {key}: idx_block_pos_value is required and out of bounds")
    mtp_state = formats["mtp"]
    mapping = mtp_state.get("ring_slots_by_logical_position")
    _need(isinstance(mapping, list), f"{label}: MTP ring mapping metadata is required")


def _prod(shape: list[int]) -> int:
    result = 1
    for dim in shape:
        result *= dim
        _need(result <= MAX_COMPONENT_BYTES, "component dimensions exceed the byte bound")
    return result


def _expected_component(kind: str, layer: int | None, boundary: dict[str, Any], arch: dict[str, Any],
                        label: str) -> dict[str, Any]:
    end = boundary["position_end_exclusive"]
    gg, qg, pg, mg = (arch[name] for name in ("gdn_geometry", "qsa_geometry", "ple_geometry", "mtp_geometry"))
    base: dict[str, Any] = {
        "component_id": f"{kind}@{layer}" if layer is not None else kind,
        "kind": kind,
        "layer_index": layer,
        "byte_order": "little",
        "canonical_serialization": CANONICAL_SERIALIZATION,
    }
    meta: dict[str, Any]
    dtype: str
    layout: str
    shape: list[int]
    byte_length: int

    if kind == "gdn_recurrence":
        shape, dtype, layout = [gg["state_size"], gg["value_heads"], gg["state_size"]], "fp32", "key_width,value_head,key_width"
        meta = {"position_end_exclusive": end}
        byte_length = _prod(shape) * 4
    elif kind == "gdn_conv_history":
        shape, dtype, layout = [gg["conv_channels"], gg["conv_kernel"] - 1], "fp32", "channel,history_oldest_first"
        meta = {"position_end_exclusive": end}
        byte_length = _prod(shape) * 4
    elif kind in ("qsa_kv_key", "qsa_kv_value", "mtp_kv_key", "mtp_kv_value"):
        is_mtp = kind.startswith("mtp_")
        geom = mg if is_mtp else qg
        state = boundary["state_formats"]["mtp" if is_mtp else f"qsa_layer_{layer}"]
        fmt = state["kv_format"]
        role = "key" if kind.endswith("key") else "value"
        dtype = {"fp16": "fp16", "int8": "int8", "q4_0": "q4_0", "hybrid_k8v4": "int8" if role == "key" else "q4_0"}[fmt]
        if fmt == "hybrid_k8v4" and role == "value":
            dtype = "q4_0"
        start = 0 if not is_mtp else max(0, end - geom["ring_capacity_cells"])
        live = end - start
        shape = [live, geom["kv_heads"], geom["head_dim"]]
        layout = "logical_position,kv_head,head_dim"
        rotations = state["key_rotation"], state["value_rotation"]
        mode = state["kv_mode"]
        page = state["page_size_cells"]
        meta = {"kv_format": fmt, "kv_role": role, "key_rotation": rotations[0], "value_rotation": rotations[1],
                "kv_mode": mode, "page_size_cells": page, "logical_live_position_start": start,
                "logical_live_position_end_exclusive": end}
        cells = live * geom["kv_heads"]
        if fmt == "fp16":
            byte_length = cells * geom["head_dim"] * 2
            meta["payload_segments"] = [{"name": "values_fp16_le", "offset_bytes": 0, "byte_length": byte_length,
                                         "logical_order": "logical_position,kv_head,head_dim"}]
        elif fmt == "int8":
            _need(geom["head_dim"] % 64 == 0, f"{label}: int8 KV head_dim must be divisible by 64")
            code_bytes = cells * geom["head_dim"]
            scale_bytes = cells * (geom["head_dim"] // 64) * 2
            byte_length = code_bytes + scale_bytes
            meta["payload_segments"] = [
                {"name": "codes_int8", "offset_bytes": 0, "byte_length": code_bytes,
                 "logical_order": "logical_position,kv_head,head_dim"},
                {"name": "scales_fp16_le", "offset_bytes": code_bytes, "byte_length": scale_bytes,
                 "logical_order": "logical_position,kv_head,scale_group_of_64"},
            ]
        elif fmt == "q4_0":
            _need(geom["head_dim"] % 32 == 0, f"{label}: q4_0 KV head_dim must be divisible by 32")
            byte_length = cells * (geom["head_dim"] // 32) * 18
            meta["payload_segments"] = [{"name": "q4_0_blocks", "offset_bytes": 0, "byte_length": byte_length,
                                         "logical_order": "logical_position,kv_head,head_dim_block",
                                         "block_layout": "18 bytes: fp16_scale_le then 16 packed code bytes; element j is low nibble and element j+16 is high nibble"}]
        else:  # K8V4 stores INT8+FP16 scales for K and rotated Q4_0 for V.
            if role == "key":
                _need(geom["head_dim"] % 64 == 0, f"{label}: hybrid K head_dim must be divisible by 64")
                code_bytes = cells * geom["head_dim"]
                scale_bytes = cells * (geom["head_dim"] // 64) * 2
                byte_length = code_bytes + scale_bytes
                meta["payload_segments"] = [
                    {"name": "codes_int8", "offset_bytes": 0, "byte_length": code_bytes,
                     "logical_order": "logical_position,kv_head,head_dim"},
                    {"name": "scales_fp16_le", "offset_bytes": code_bytes, "byte_length": scale_bytes,
                     "logical_order": "logical_position,kv_head,scale_group_of_64"},
                ]
            else:
                _need(geom["head_dim"] % 32 == 0, f"{label}: hybrid V head_dim must be divisible by 32")
                byte_length = cells * (geom["head_dim"] // 32) * 18
                meta["payload_segments"] = [{"name": "q4_0_blocks", "offset_bytes": 0, "byte_length": byte_length,
                                             "logical_order": "logical_position,kv_head,head_dim_block",
                                             "block_layout": "18 bytes: fp16_scale_le then 16 packed code bytes; element j is low nibble and element j+16 is high nibble"}]
    elif kind.startswith("qsa_idx_"):
        qsa = boundary["state_formats"][f"qsa_layer_{layer}"]
        rows = end // qg["idx_block"] + 1
        common = {"position_end_exclusive": end, "idx_block": qg["idx_block"], "idx_dim": qg["idx_dim"],
                  "idx_pooled_rows": rows}
        dtype = "int32" if kind == "qsa_idx_block_pos" else "fp32"
        if kind == "qsa_idx_tail":
            shape, layout = [qg["idx_block"] - 1, qg["idx_dim"]], "tail_position,idx_dimension"
        elif kind == "qsa_idx_dead":
            shape, layout = [qg["idx_dim"]], "dead_key_dimension"
        elif kind == "qsa_idx_pooled":
            shape, layout = [rows, qg["idx_dim"]], "logical_pooled_row,idx_dimension"
        else:
            value = qsa["idx_block_pos_value"]
            _need(_is_int(value) and 0 <= value < MAX_CONTEXT, f"{label}: invalid idx_block_pos value")
            shape, layout = [1], "scalar"
            common["idx_block_pos_value"] = value
        meta = common
        byte_length = _prod(shape) * (4 if dtype in ("fp32", "int32") else 0)
    elif kind == "ple_history":
        shape, dtype, layout = [pg["history_channels"], pg["history_rows"]], "fp32", "channel,history_oldest_first"
        meta = {"position_end_exclusive": end}
        byte_length = _prod(shape) * 4
    elif kind == "ple_previous_token_ids":
        values = boundary["ple_previous_token_ids"]
        _need(isinstance(values, list) and len(values) == 2 and all(_is_int(v) and -1 <= v <= 2147483647 for v in values),
              f"{label}: PLE predecessor IDs must contain two int32 token IDs (or -1 sentinels)")
        shape, dtype, layout = [2], "int32", "oldest_to_newest"
        meta = {"position_end_exclusive": end, "token_ids": values}
        byte_length = 8
    elif kind in ("mtp_ring_mapping",):
        state = boundary["state_formats"]["mtp"]
        start = max(0, end - mg["ring_capacity_cells"])
        live = end - start
        mapping = state["ring_slots_by_logical_position"]
        _need(isinstance(mapping, list) and len(mapping) == live and all(_is_int(v) for v in mapping),
              f"{label}: MTP ring mapping must enumerate every live logical position")
        _need(len(set(mapping)) == live and all(0 <= slot < mg["ring_capacity_cells"] for slot in mapping),
              f"{label}: MTP ring mapping has duplicate or out-of-range physical slots")
        shape, dtype, layout = [live], "int32", "logical_position_to_physical_cell_slot"
        meta = {"ring_capacity_cells": mg["ring_capacity_cells"], "page_size_cells": state["page_size_cells"],
                "logical_live_position_start": start, "logical_live_position_end_exclusive": end,
                "ring_slots_by_logical_position": mapping}
        byte_length = live * 4
    else:
        raise TraceError(f"{label}: unexpected component kind {kind}")

    _need(0 < byte_length <= MAX_COMPONENT_BYTES, f"{label}: component byte_length is out of bounds")
    base.update({"shape": shape, "dtype": dtype, "layout": layout, "byte_length": byte_length, "format_metadata": meta})
    return base


def _validate_commit(commit: dict[str, Any], arch: dict[str, Any], expected: list[tuple[str, int | None, str]],
                     label: str) -> None:
    start, end = commit["position_start"], commit["position_end_exclusive"]
    _need(_is_int(start) and _is_int(end) and 0 <= start < end <= MAX_CONTEXT,
          f"{label}: commit position interval is invalid or exceeds bounds")
    committed = commit["committed_tokens"]
    _need(len(committed) == end - start, f"{label}: committed token list length does not match the absolute position interval")
    for offset, token in enumerate(committed):
        _need(token["position"] == start + offset, f"{label}: committed token positions must be contiguous and ordered")
    _need(1 <= len(commit["native_token_ids"]) <= MAX_TOKEN_IDS,
          f"{label}: native_token_ids must be a bounded non-empty list")
    _need(len(commit["mtp_accepted_token_ids"]) <= len(commit["mtp_offered_token_ids"]),
          f"{label}: accepted MTP proposals cannot exceed offered proposals")
    _need(commit["mtp_offered_token_ids"][:len(commit["mtp_accepted_token_ids"])] == commit["mtp_accepted_token_ids"],
          f"{label}: accepted MTP token IDs must be an exact prefix of offered IDs")
    capture = commit["capture_point"]
    _need(all(capture[field] is True for field in ("after_verifier_commit", "mutating_streams_synchronized",
                                                   "mtp_draft_stream_synchronized", "copy_completion_synchronized")),
          f"{label}: state capture must follow commit and verifier, MTP/draft, and copy stream completion")
    _validate_state_snapshot(commit, arch, expected, label)


def _validate_state_snapshot(snapshot: dict[str, Any], arch: dict[str, Any],
                             expected: list[tuple[str, int | None, str]], label: str) -> None:
    _validate_state_formats(snapshot, arch, label)
    counts = _expected_counts(expected)
    _need(snapshot["expected_component_counts"] == counts, f"{label}: declared component counts do not match architecture-derived inventory")
    inventory = [item[2] for item in expected]
    _need(snapshot["expected_component_inventory"] == inventory,
          f"{label}: declared component inventory is incomplete, extra, or not canonical-order")
    components = snapshot["components"]
    _need(len(components) == len(expected) and len(components) <= MAX_COMPONENTS,
          f"{label}: component count is truncated or out of bounds")
    actual_ids = [c.get("component_id") for c in components]
    _need(actual_ids == inventory, f"{label}: component IDs must match the complete ordered inventory exactly")
    for component, (kind, layer, component_id) in zip(components, expected):
        _need(component["kind"] == kind and component["layer_index"] == layer,
              f"{label}: {component_id}: kind/layer does not match inventory")
        _need(_sha(component["sha256"]), f"{label}: {component_id}: SHA-256 digest must be lowercase hexadecimal")
        wanted = _expected_component(kind, layer, snapshot, arch, f"{label} {component_id}")
        for field, value in wanted.items():
            _need(component.get(field) == value, f"{label}: {component_id}: {field} does not match canonical inventory/serialization")


def _index_trace(trace: dict[str, Any], label: str) -> tuple[dict[str, Any], str | None]:
    _preflight_trace_bounds(trace, label)
    _validate_schema(trace, label)
    _need(trace["contract_version"] == 3 and trace["trace_kind"] == "native_runtime_parity_trace_v3",
          f"{label}: only native_runtime_parity_trace_v3 is accepted; v2 requires recapture")
    _need(trace["runtime_parity_claim"] is False, f"{label}: runtime parity claim must remain false")
    provenance = trace["provenance"]
    _need(provenance["synthetic"] is (trace["evidence_class"] == "synthetic_contract_only"),
          f"{label}: synthetic marker and evidence_class disagree")
    for field in PROVENANCE_FIELDS:
        if field.endswith("_sha256"):
            _need(_sha(provenance[field]), f"{label}: provenance.{field} must be lowercase SHA-256 hex")
    arch, expected = _architecture(trace, label)
    requests = trace["requests"]
    _need(1 <= len(requests) <= MAX_REQUESTS, f"{label}: request count is out of bounds")
    indexed: dict[str, dict[str, Any]] = {}
    for req in requests:
        rid = req["request_id"]
        _need(isinstance(rid, str) and rid and rid not in indexed, f"{label}: request_id is empty or duplicated")
        for field in ("cache_key_sha256", "input_token_ids_sha256", "sampler_state_sha256"):
            _need(_sha(req[field]), f"{label}: request {rid}: {field} must be lowercase SHA-256 hex")
        _need(req["cache_reused_tokens"] + req["cache_fresh_tokens"] == req["input_token_count"],
              f"{label}: request {rid}: cache reused+fresh counts must equal input_token_count")
        prompt_tail = req["input_token_tail_ids"]
        _need(len(prompt_tail) == min(2, req["input_token_count"]),
              f"{label}: request {rid}: input_token_tail_ids must contain the last one or two prompt IDs")
        expected_previous = [-1] * (2 - len(prompt_tail)) + prompt_tail
        initial = req["initial_checkpoint"]
        _need(initial["position_end_exclusive"] == req["input_token_count"],
              f"{label}: request {rid}: initial checkpoint must end at input_token_count")
        initial_capture = initial["capture_point"]
        _need(all(initial_capture[field] is True for field in ("after_prompt_cache_boundary", "mutating_streams_synchronized",
                                                               "mtp_draft_stream_synchronized", "copy_completion_synchronized")),
              f"{label}: request {rid}: initial checkpoint requires prompt/cache, mutating, MTP/draft, and copy synchronization")
        _need(initial["ple_previous_token_ids"] == expected_previous,
              f"{label}: request {rid}: initial PLE predecessor IDs must equal the prompt tail with -1 padding")
        _validate_state_snapshot(initial, arch, expected, f"{label}: request {rid} initial checkpoint")
        commits = req["commits"]
        _need(1 <= len(commits) <= MAX_COMMITS, f"{label}: request {rid}: commit count is out of bounds")
        previous_end = req["input_token_count"]
        for index, commit in enumerate(commits):
            _need(commit["commit_index"] == index, f"{label}: request {rid}: commit_index must be zero-based, ordered, and contiguous")
            if previous_end is not None:
                _need(commit["position_start"] == previous_end,
                      f"{label}: request {rid}: commit intervals must be contiguous without omitted boundaries")
            _validate_commit(commit, arch, expected, f"{label}: request {rid} commit {index}")
            for token in commit["committed_tokens"]:
                expected_previous = [expected_previous[1], token["token_id"]]
            _need(commit["ple_previous_token_ids"] == expected_previous,
                  f"{label}: request {rid} commit {index}: PLE predecessor IDs do not match prompt plus committed-token history")
            previous_end = commit["position_end_exclusive"]
        indexed[rid] = req
    return {"trace": trace, "provenance": provenance, "architecture": arch, "requests": indexed, "expected": expected}, None


def compare(serial: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    """Compare complete supplied v3 traces and return the first exact divergence."""
    try:
        left, _ = _index_trace(serial, "serial")
        right, _ = _index_trace(candidate, "candidate")
        _need(serial["mode"] == "serial_off", "serial.mode must be serial_off")
        _need(candidate["mode"] == "abcd_on", "candidate.mode must be abcd_on")
        _need(serial["evidence_class"] == candidate["evidence_class"],
              "evidence_class differs; synthetic fixtures cannot be paired with unverified native captures")
        for field in PROVENANCE_FIELDS:
            _need(left["provenance"][field] == right["provenance"][field], f"provenance.{field} differs")
        _need(left["architecture"] == right["architecture"], "architecture/model-declared inventory differs")
        _need(list(left["requests"]) == list(right["requests"]), "request order or request IDs differ")
        for rid in left["requests"]:
            a, b = left["requests"][rid], right["requests"][rid]
            for field in REQUEST_FIELDS:
                _need(a[field] == b[field], f"request {rid}: {field} differs")
            ca, cb = a["commits"], b["commits"]
            _need(len(ca) == len(cb), f"request {rid}: commit count differs")
            for index, (ac, bc) in enumerate(zip(ca, cb)):
                boundary = (ac["position_start"], ac["position_end_exclusive"])
                _need(boundary == (bc["position_start"], bc["position_end_exclusive"]),
                      f"request {rid} commit {index}: absolute position boundary differs")
                for field in ("committed_tokens", "native_token_ids", "mtp_offered_token_ids", "mtp_accepted_token_ids"):
                    _need(ac[field] == bc[field], f"request {rid} commit {index}: {field} differs")
                for field in ("state_formats", "expected_component_counts", "expected_component_inventory", "components"):
                    _need(ac[field] == bc[field], f"request {rid} commit {index}: {field} differs")
        return {"equal": True, "runtime_parity_claim": False,
                "evidence_class": serial["evidence_class"], "capture_authenticated": False,
                "synthetic_contract_only": serial["provenance"]["synthetic"] or candidate["provenance"]["synthetic"],
                "state_comparison_boundary": "absolute_committed_position_interval_end",
                "warning": "Equality compares supplied descriptors and SHA-256 digests only. It cannot authenticate capture, synchronization, provenance, or the source bytes; independent native evidence is required.",
                "first_divergence": None}
    except (TraceError, KeyError, TypeError) as exc:
        return {"equal": False, "runtime_parity_claim": False, "first_divergence": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("serial_off", type=Path)
    parser.add_argument("candidate_on", type=Path)
    args = parser.parse_args()
    result = compare(load(args.serial_off), load(args.candidate_on))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
