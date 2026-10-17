"""Clearly synthetic v3 contract fixtures; hashes here are labels, never captured state."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any

import runtime_parity_v3 as parity


SYNTHETIC_SHA = hashlib.sha256(b"native-runtime-parity-v3-synthetic-provenance").hexdigest()


def tiny_architecture() -> dict[str, Any]:
    return {
        "model_family": "synthetic-three-layer-contract-model",
        "layer_count": 3,
        "gdn_layers": [0, 2],
        "qsa_layers": [1],
        "gdn_geometry": {"state_size": 2, "value_heads": 2, "conv_channels": 3, "conv_kernel": 3},
        "qsa_geometry": {"idx_block": 2, "idx_dim": 4, "kv_heads": 1, "head_dim": 4, "page_size_cells": 2},
        "ple_geometry": {"history_rows": 2, "history_channels": 3, "previous_token_count": 2},
        "mtp_geometry": {"kv_heads": 1, "head_dim": 4, "ring_capacity_cells": 2, "page_size_cells": 2},
    }


def current_qwen38_architecture() -> dict[str, Any]:
    """Current-main geometry included only as a labelled synthetic inventory example."""
    qsa = list(range(3, 48, 4))
    return {
        "model_family": "Qwen3.8-Flash-Next synthetic inventory example",
        "layer_count": 48,
        "gdn_layers": [layer for layer in range(48) if layer not in qsa],
        "qsa_layers": qsa,
        "gdn_geometry": {"state_size": 128, "value_heads": 48, "conv_channels": 10240, "conv_kernel": 4},
        "qsa_geometry": {"idx_block": 4, "idx_dim": 128, "kv_heads": 2, "head_dim": 256, "page_size_cells": 4},
        "ple_geometry": {"history_rows": 9, "history_channels": 10240, "previous_token_count": 2},
        "mtp_geometry": {"kv_heads": 2, "head_dim": 256, "ring_capacity_cells": 4, "page_size_cells": 4},
    }


def _state_formats(arch: dict[str, Any], end: int, *, kv_format: str = "fp16") -> dict[str, Any]:
    rotation = "walsh_hadamard" if kv_format in {"q4_0", "hybrid_k8v4"} else "none"
    if kv_format == "hybrid_k8v4":
        key_rotation, value_rotation = "none", "walsh_hadamard"
    else:
        key_rotation = value_rotation = rotation
    qsa_state = {"kv_format": kv_format, "key_rotation": key_rotation, "value_rotation": value_rotation,
                 "kv_mode": "resident", "page_size_cells": arch["qsa_geometry"]["page_size_cells"],
                 "idx_block_pos_value": end - 1}
    ring_capacity = arch["mtp_geometry"]["ring_capacity_cells"]
    start = max(0, end - ring_capacity)
    mtp_state = {"kv_format": kv_format, "key_rotation": key_rotation, "value_rotation": value_rotation,
                 "kv_mode": "ring", "page_size_cells": arch["mtp_geometry"]["page_size_cells"],
                 "ring_slots_by_logical_position": [position % ring_capacity for position in range(start, end)]}
    return {"mtp": mtp_state, **{f"qsa_layer_{layer}": deepcopy(qsa_state) for layer in arch["qsa_layers"]}}


def _commit(index: int, start: int, ids: list[int], arch: dict[str, Any], kv_format: str = "fp16") -> dict[str, Any]:
    end = start + len(ids)
    boundary: dict[str, Any] = {
        "commit_index": index,
        "position_start": start,
        "position_end_exclusive": end,
        "committed_tokens": [{"position": start + i, "token_id": token_id} for i, token_id in enumerate(ids)],
        "native_token_ids": [700 + index, 710 + index],
        "mtp_offered_token_ids": [800 + index],
        "mtp_accepted_token_ids": [800 + index],
        "capture_point": {"after_verifier_commit": True, "mutating_streams_synchronized": True,
                          "mtp_draft_stream_synchronized": True, "copy_completion_synchronized": True},
        "ple_previous_token_ids": ids[-2:] if len(ids) >= 2 else [-1, ids[-1]],
        "state_formats": _state_formats(arch, end, kv_format=kv_format),
    }
    _, expected = parity._architecture({"architecture": arch}, "synthetic fixture")
    boundary["expected_component_counts"] = parity._expected_counts(expected)
    boundary["expected_component_inventory"] = [item[2] for item in expected]
    boundary["components"] = []
    for kind, layer, component_id in expected:
        component = parity._expected_component(kind, layer, boundary, arch, f"synthetic {component_id}")
        component["sha256"] = hashlib.sha256(f"synthetic-label:{end}:{component_id}".encode()).hexdigest()
        boundary["components"].append(component)
    return boundary


def _initial_checkpoint(arch: dict[str, Any], input_token_count: int, kv_format: str = "fp16") -> dict[str, Any]:
    boundary: dict[str, Any] = {
        "position_end_exclusive": input_token_count,
        "capture_point": {"after_prompt_cache_boundary": True, "mutating_streams_synchronized": True,
                          "mtp_draft_stream_synchronized": True, "copy_completion_synchronized": True},
        "ple_previous_token_ids": [199, 200],
        "state_formats": _state_formats(arch, input_token_count, kv_format=kv_format),
    }
    _, expected = parity._architecture({"architecture": arch}, "synthetic fixture initial state")
    boundary["expected_component_counts"] = parity._expected_counts(expected)
    boundary["expected_component_inventory"] = [item[2] for item in expected]
    boundary["components"] = []
    for kind, layer, component_id in expected:
        component = parity._expected_component(kind, layer, boundary, arch, f"synthetic initial {component_id}")
        component["sha256"] = hashlib.sha256(f"synthetic-label:initial:{input_token_count}:{component_id}".encode()).hexdigest()
        boundary["components"].append(component)
    return boundary


def make_trace(mode: str, arch: dict[str, Any] | None = None, kv_format: str = "fp16") -> dict[str, Any]:
    arch = deepcopy(arch or tiny_architecture())
    input_token_count = 4
    commits = [_commit(0, input_token_count, [201, 202], arch, kv_format),
               _commit(1, input_token_count + 2, [203, 204], arch, kv_format)]
    return {
        "contract_version": 3,
        "trace_kind": "native_runtime_parity_trace_v3",
        "mode": mode,
        "evidence_class": "synthetic_contract_only",
        "runtime_parity_claim": False,
        "provenance": {
            "source_commit": "synthetic-fixture-only",
            "binary_sha256": SYNTHETIC_SHA,
            "model_sha256": SYNTHETIC_SHA,
            "tokenizer_sha256": SYNTHETIC_SHA,
            "mtp_sha256": SYNTHETIC_SHA,
            "command_sha256": SYNTHETIC_SHA,
            "device_and_runtime": "synthetic fixture; no device accessed",
            "trace_capture_method": "synthetic labels; no runtime capture",
            "synthetic": True,
        },
        "architecture": arch,
        "requests": [{
            "request_id": "synthetic-r-01",
            "cache_key_sha256": SYNTHETIC_SHA,
            "cache_reused_tokens": 2,
            "cache_fresh_tokens": 2,
            "input_token_count": input_token_count,
            "input_token_tail_ids": [199, 200],
            "input_token_ids_sha256": SYNTHETIC_SHA,
            "sampler_state_sha256": SYNTHETIC_SHA,
            "initial_checkpoint": _initial_checkpoint(arch, input_token_count, kv_format),
            "commits": commits,
        }],
    }


def current_inventory_fixture() -> dict[str, Any]:
    """One fully enumerated, clearly synthetic current-main inventory; no captured bytes."""
    arch = current_qwen38_architecture()
    trace = make_trace("serial_off", arch)
    trace["requests"][0]["commits"] = [_commit(0, 4, [201, 202], arch)]
    trace["requests"][0]["commits"][0]["native_token_ids"] = [700]
    trace["requests"][0]["commits"][0]["mtp_offered_token_ids"] = []
    trace["requests"][0]["commits"][0]["mtp_accepted_token_ids"] = []
    trace["requests"][0]["commits"][0]["expected_component_counts"] = parity._expected_counts(
        parity._architecture({"architecture": arch}, "synthetic current inventory")[1])
    return trace
