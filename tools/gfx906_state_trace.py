#!/usr/bin/env python3
"""CPU-only validator/comparator for explicit stage-ordered recurrent-state traces.

Equality covers only the supplied window identity and enumerated state digest inventory.
It does not capture state, prove that an inventory is complete, or authenticate provenance.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

FORMAT = "native_recurrent_state_trace_v1"
COMPONENT_KINDS = {"gdn_recurrent", "qsa_indexer_idx_block_pos", "ple_prev_token"}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
META_FIELDS = ("component_id", "ordinal", "layer_index", "shape", "dtype", "byte_order", "serialization")


def _key(component: dict[str, Any]) -> tuple[str, int]:
    return component["component_id"], component["ordinal"]


def validate_trace(trace: Any, label: str = "trace") -> list[str]:
    errors: list[str] = []
    if not isinstance(trace, dict):
        return [f"{label}: expected object"]
    if trace.get("trace_format") != FORMAT:
        errors.append(f"{label}: trace_format must be {FORMAT}")
    evidence_class = trace.get("evidence_class")
    if not isinstance(evidence_class, str) or evidence_class not in {"synthetic_contract_only", "native_capture_unverified"}:
        errors.append(f"{label}: evidence_class must explicitly classify supplied evidence")
    mode = trace.get("mode")
    if not isinstance(mode, str) or mode not in {"serial_off", "abcd_on"}:
        errors.append(f"{label}: mode must be serial_off or abcd_on")
    identity = trace.get("window_identity")
    if not isinstance(identity, dict):
        errors.append(f"{label}: window_identity is required")
    else:
        if not isinstance(identity.get("request_id"), str) or not identity["request_id"].strip():
            errors.append(f"{label}: window_identity.request_id is required")
        if type(identity.get("commit_window_index")) is not int or identity["commit_window_index"] < 0:
            errors.append(f"{label}: window_identity.commit_window_index must be a non-negative integer")
        ids = identity.get("committed_token_ids")
        if not isinstance(ids, list) or not ids or any(type(token) is not int or token < 0 for token in ids):
            errors.append(f"{label}: window_identity.committed_token_ids must be a non-empty list of token IDs")
        if type(identity.get("committed_token_count")) is not int or identity["committed_token_count"] != (len(ids) if isinstance(ids, list) else -1):
            errors.append(f"{label}: committed_token_count must equal the number of committed_token_ids")

    ranges = trace.get("layer_ranges")
    inventory: dict[tuple[str, int], dict[str, Any]] = {}
    range_counts: dict[str, int] = {}
    if not isinstance(ranges, list) or not ranges:
        errors.append(f"{label}: layer_ranges must be a non-empty explicit inventory")
        ranges = []
    for ri, item in enumerate(ranges):
        where = f"{label}: layer_ranges[{ri}]"
        if not isinstance(item, dict):
            errors.append(f"{where} must be an object")
            continue
        cid = item.get("component_id")
        start, count = item.get("ordinal_start"), item.get("count")
        layer_start = item.get("layer_index_start")
        if not isinstance(cid, str) or cid not in COMPONENT_KINDS:
            errors.append(f"{where}: unknown component_id {cid!r}")
            continue
        if type(start) is not int or start != 0 or type(count) is not int or count < 1:
            errors.append(f"{where}: ordinal_start must be zero and count positive")
            continue
        if cid in range_counts:
            errors.append(f"{where}: duplicate layer range for {cid}")
            continue
        if cid == "ple_prev_token":
            if count != 1 or layer_start is not None:
                errors.append(f"{where}: PLE token inventory must be one non-layer component")
        elif type(layer_start) is not int or layer_start < 0:
            errors.append(f"{where}: layer_index_start must be non-negative for layer state")
            continue
        range_counts[cid] = count
        shape = item.get("shape")
        if not isinstance(shape, list) or any(type(x) is not int or x < 0 for x in shape):
            errors.append(f"{where}: shape must be a list of non-negative integers")
        if not isinstance(item.get("dtype"), str) or not item["dtype"]:
            errors.append(f"{where}: dtype is required")
        byte_order = item.get("byte_order")
        if not isinstance(byte_order, str) or byte_order not in {"little", "big", "not_applicable"}:
            errors.append(f"{where}: byte_order is invalid")
        if not isinstance(item.get("serialization"), str) or not item["serialization"]:
            errors.append(f"{where}: serialization is required")
        for ordinal in range(start, start + count):
            entry = {"component_id": cid, "ordinal": ordinal,
                     "layer_index": None if cid == "ple_prev_token" else layer_start + ordinal,
                     "shape": shape, "dtype": item.get("dtype"),
                     "byte_order": item.get("byte_order"), "serialization": item.get("serialization")}
            inventory[(cid, ordinal)] = entry
    if set(range_counts) != COMPONENT_KINDS:
        errors.append(f"{label}: layer_ranges must declare each required component kind exactly once")

    plan = trace.get("stage_plan")
    if not isinstance(plan, list) or not plan:
        errors.append(f"{label}: stage_plan must be a non-empty list")
        plan = []
    stage_ids: list[str] = []
    expected_keys = set(inventory)
    for i, stage in enumerate(plan):
        where = f"{label}: stage_plan[{i}]"
        if not isinstance(stage, dict):
            errors.append(f"{where} must be an object")
            continue
        sid = stage.get("stage_id")
        stage_ids.append(sid if isinstance(sid, str) else "")
        refs = stage.get("owned_components")
        if not isinstance(refs, list):
            errors.append(f"{where}: owned_components must be a list of component ordinals")
            continue
        keys: list[tuple[str, int]] = []
        for ref in refs:
            if (not isinstance(ref, dict) or not isinstance(ref.get("component_id"), str)
                    or ref["component_id"] not in COMPONENT_KINDS or type(ref.get("ordinal")) is not int):
                errors.append(f"{where}: invalid component ordinal reference")
                continue
            keys.append((ref["component_id"], ref["ordinal"]))
        if len(keys) != len(set(keys)):
            errors.append(f"{where}: duplicate owned component ordinal")
        if keys != list(inventory):
            errors.append(f"{where}: owned component ordinals and order must exactly match layer_ranges inventory")
    if any(not sid for sid in stage_ids) or len(set(stage_ids)) != len(stage_ids):
        errors.append(f"{label}: stage IDs must be non-empty and unique")

    provenance = trace.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{label}: provenance object is required")
    else:
        for key in ("source_commit", "trace_capture_method"):
            if not isinstance(provenance.get(key), str) or not provenance[key].strip():
                errors.append(f"{label}: provenance.{key} is required")
        for key in ("binary_sha256", "model_sha256"):
            if not isinstance(provenance.get(key), str) or HEX64.fullmatch(provenance[key]) is None:
                errors.append(f"{label}: provenance.{key} must be lowercase SHA-256 hex")

    checkpoints = trace.get("checkpoints")
    if not isinstance(checkpoints, list) or len(checkpoints) != len(plan):
        errors.append(f"{label}: checkpoint stage coverage must exactly match stage_plan")
        checkpoints = checkpoints if isinstance(checkpoints, list) else []
    for i, cp in enumerate(checkpoints):
        where = f"{label}: checkpoint {i}"
        if not isinstance(cp, dict):
            errors.append(f"{where} must be an object")
            continue
        if type(cp.get("stage_index")) is not int or cp["stage_index"] != i:
            errors.append(f"{where}: stage_index must be ordered and zero-based")
        if i < len(plan) and isinstance(plan[i], dict) and cp.get("stage_id") != plan[i].get("stage_id"):
            errors.append(f"{where}: stage_id must match stage_plan order")
        components = cp.get("components")
        if not isinstance(components, list):
            errors.append(f"{where}: components must be a list")
            continue
        found: dict[tuple[str, int], dict[str, Any]] = {}
        component_order: list[tuple[str, int]] = []
        for component in components:
            if not isinstance(component, dict):
                errors.append(f"{where}: component must be an object")
                continue
            if (type(component.get("ordinal")) is not int or not isinstance(component.get("component_id"), str)
                    or component["component_id"] not in COMPONENT_KINDS):
                errors.append(f"{where}: component_id and integer ordinal are required")
                continue
            key = _key(component)
            component_order.append(key)
            if key in found:
                errors.append(f"{where}: duplicate component ordinal {key}")
            found[key] = component
            if key not in inventory:
                errors.append(f"{where}: unknown component ordinal {key}")
                continue
            for field in META_FIELDS:
                if field not in component:
                    errors.append(f"{where}: {key} missing metadata {field}")
                elif component[field] != inventory[key][field]:
                    errors.append(f"{where}: {key} metadata {field} differs from layer_ranges")
            if not isinstance(component.get("sha256"), str) or HEX64.fullmatch(component["sha256"]) is None:
                errors.append(f"{where}: {key} sha256 must be lowercase SHA-256 hex")
        if set(found) != expected_keys:
            missing = sorted(expected_keys - set(found))
            extra = sorted(set(found) - expected_keys)
            errors.append(f"{where}: component ordinals differ from inventory; missing={missing} extra={extra}")
        if component_order != list(inventory):
            errors.append(f"{where}: component order must exactly match layer_ranges inventory")
    return errors


def compare(serial: Any, candidate: Any) -> dict[str, Any]:
    for label, trace in (("serial", serial), ("candidate", candidate)):
        errors = validate_trace(trace, label)
        if errors:
            return {"diagnostic_records_equal": False, "first_divergence": errors[0], "runtime_parity_claim": False}
    if serial["mode"] != "serial_off":
        return {"diagnostic_records_equal": False, "first_divergence": "serial.mode must be serial_off", "runtime_parity_claim": False}
    if candidate["mode"] != "abcd_on":
        return {"diagnostic_records_equal": False, "first_divergence": "candidate.mode must be abcd_on", "runtime_parity_claim": False}
    for key in ("source_commit", "binary_sha256", "model_sha256", "trace_capture_method"):
        if serial["provenance"][key] != candidate["provenance"][key]:
            return {"diagnostic_records_equal": False, "first_divergence": f"provenance.{key} differs", "runtime_parity_claim": False}
    if serial["window_identity"] != candidate["window_identity"]:
        return {"diagnostic_records_equal": False, "first_divergence": "window_identity differs", "runtime_parity_claim": False}
    if serial["layer_ranges"] != candidate["layer_ranges"]:
        return {"diagnostic_records_equal": False, "first_divergence": "layer_ranges differs", "runtime_parity_claim": False}
    if serial["stage_plan"] != candidate["stage_plan"]:
        return {"diagnostic_records_equal": False, "first_divergence": "stage_plan differs", "runtime_parity_claim": False}
    for i, (left, right) in enumerate(zip(serial["checkpoints"], candidate["checkpoints"])):
        lm = left["components"]
        rm = right["components"]
        if [_key(c) for c in lm] != [_key(c) for c in rm]:
            return {"diagnostic_records_equal": False, "first_divergence": f"checkpoint {i}: component ordinals differ", "runtime_parity_claim": False}
        for a, b in zip(lm, rm):
            key = _key(a)
            for field in META_FIELDS:
                if a[field] != b[field]:
                    return {"diagnostic_records_equal": False, "first_divergence": f"checkpoint {i} {key}: {field} differs", "runtime_parity_claim": False}
            if a["sha256"] != b["sha256"]:
                return {"diagnostic_records_equal": False, "first_divergence": f"checkpoint {i} {key}: sha256 differs", "runtime_parity_claim": False}
    return {"diagnostic_records_equal": True, "comparison_scope": "supplied_declared_checkpoints_only",
            "first_divergence": None, "runtime_parity_claim": False,
            "warning": "This reports equality of supplied declared checkpoints only. It cannot prove that the stage plan, layer ranges, or capture are complete; no runtime parity claim is made."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("serial_off", type=Path)
    parser.add_argument("abcd_on", type=Path)
    args = parser.parse_args()
    try:
        result = compare(json.loads(args.serial_off.read_text()), json.loads(args.abcd_on.read_text()))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"diagnostic_records_equal": False, "first_divergence": str(exc), "runtime_parity_claim": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["diagnostic_records_equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
