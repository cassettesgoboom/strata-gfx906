#!/usr/bin/env python3
"""CPU-only validator/comparator for explicit stage-ordered recurrent-state traces.

This checks supplied JSON only. It does not capture state or authenticate provenance.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

FORMAT = "native_recurrent_state_trace_v1"
REQUIRED_COMPONENTS = {"gdn_recurrent", "qsa_indexer_idx_block_pos", "ple_prev_token"}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def validate_trace(trace: Any, label: str = "trace") -> list[str]:
    errors: list[str] = []
    if not isinstance(trace, dict):
        return [f"{label}: expected object"]
    if trace.get("trace_format") != FORMAT:
        errors.append(f"{label}: trace_format must be {FORMAT}")
    if trace.get("evidence_class") not in {"synthetic_contract_only", "native_capture_unverified"}:
        errors.append(f"{label}: evidence_class must explicitly classify supplied evidence")
    if trace.get("mode") not in {"serial_off", "abcd_on"}:
        errors.append(f"{label}: mode must be serial_off or abcd_on")
    plan = trace.get("stage_plan")
    if (not isinstance(plan, list) or not plan or
            any(not isinstance(x, str) or not x for x in plan) or len(set(plan)) != len(plan)):
        errors.append(f"{label}: stage_plan must be a non-empty list of unique stage IDs")
        plan = []
    required = trace.get("required_components")
    if not isinstance(required, list) or set(required) != REQUIRED_COMPONENTS or len(required) != len(REQUIRED_COMPONENTS):
        errors.append(f"{label}: required_components must include exactly {sorted(REQUIRED_COMPONENTS)}")
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
    if not isinstance(checkpoints, list) or not checkpoints:
        errors.append(f"{label}: checkpoints must be a non-empty list")
        return errors
    actual_stages: list[str] = []
    for i, cp in enumerate(checkpoints):
        where = f"{label}: checkpoint {i}"
        if not isinstance(cp, dict):
            errors.append(f"{where} must be an object")
            continue
        if type(cp.get("stage_index")) is not int or cp["stage_index"] != i:
            errors.append(f"{where}: stage_index must be ordered and zero-based")
        sid = cp.get("stage_id")
        actual_stages.append(sid if isinstance(sid, str) else "")
        if not isinstance(cp.get("components"), list):
            errors.append(f"{where}: components must be a list")
            continue
        found: set[str] = set()
        for component in cp["components"]:
            if not isinstance(component, dict):
                errors.append(f"{where}: component must be an object")
                continue
            cid = component.get("component_id")
            if not isinstance(cid, str) or not cid:
                errors.append(f"{where}: component_id is required")
                continue
            if cid in found:
                errors.append(f"{where}: duplicate component {cid}")
            found.add(cid)
            for key in ("scope", "shape", "dtype", "byte_order", "serialization", "sha256"):
                if key not in component:
                    errors.append(f"{where}: {cid} missing component metadata {key}")
            scope = component.get("scope")
            if not isinstance(scope, dict) or "layer_index" not in scope or (scope["layer_index"] is not None and (type(scope["layer_index"]) is not int or scope["layer_index"] < 0)):
                errors.append(f"{where}: {cid} scope.layer_index must be a non-negative integer or null")
            shape = component.get("shape")
            if not isinstance(shape, list) or any(type(dim) is not int or dim < 0 for dim in shape):
                errors.append(f"{where}: {cid} shape must be a list of non-negative integers")
            if not isinstance(component.get("dtype"), str) or not component["dtype"]:
                errors.append(f"{where}: {cid} dtype is required")
            if component.get("byte_order") not in {"little", "big", "not_applicable"}:
                errors.append(f"{where}: {cid} byte_order is invalid")
            if not isinstance(component.get("serialization"), str) or not component["serialization"]:
                errors.append(f"{where}: {cid} serialization is required")
            if not isinstance(component.get("sha256"), str) or HEX64.fullmatch(component["sha256"]) is None:
                errors.append(f"{where}: {cid} sha256 must be lowercase SHA-256 hex")
        missing = REQUIRED_COMPONENTS - found
        if missing:
            errors.append(f"{where}: missing required components {sorted(missing)}")
    if actual_stages != plan:
        errors.append(f"{label}: checkpoint stage coverage/order must exactly match stage_plan")
    return errors


def compare(serial: Any, candidate: Any) -> dict[str, Any]:
    for label, trace in (("serial", serial), ("candidate", candidate)):
        errors = validate_trace(trace, label)
        if errors:
            return {"equal": False, "first_divergence": errors[0], "runtime_parity_claim": False}
    if serial["mode"] != "serial_off":
        return {"equal": False, "first_divergence": "serial.mode must be serial_off", "runtime_parity_claim": False}
    if candidate["mode"] != "abcd_on":
        return {"equal": False, "first_divergence": "candidate.mode must be abcd_on", "runtime_parity_claim": False}
    for key in ("source_commit", "binary_sha256", "model_sha256"):
        if serial["provenance"][key] != candidate["provenance"][key]:
            return {"equal": False, "first_divergence": f"provenance.{key} differs", "runtime_parity_claim": False}
    if serial["stage_plan"] != candidate["stage_plan"]:
        return {"equal": False, "first_divergence": "stage_plan differs", "runtime_parity_claim": False}
    for i, (left, right) in enumerate(zip(serial["checkpoints"], candidate["checkpoints"])):
        for component_id in sorted(REQUIRED_COMPONENTS):
            a = next(x for x in left["components"] if x["component_id"] == component_id)
            b = next(x for x in right["components"] if x["component_id"] == component_id)
            for key in ("scope", "shape", "dtype", "byte_order", "serialization"):
                if a[key] != b[key]:
                    return {"equal": False, "first_divergence": f"checkpoint {i} {component_id}: {key} differs", "runtime_parity_claim": False}
            if a["sha256"] != b["sha256"]:
                return {"equal": False, "first_divergence": f"checkpoint {i} {component_id}: sha256 differs", "runtime_parity_claim": False}
    return {"equal": True, "first_divergence": None, "runtime_parity_claim": False,
            "warning": "Equality compares supplied traces only; capture authenticity and runtime correctness require independent evidence."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("serial_off", type=Path)
    parser.add_argument("abcd_on", type=Path)
    args = parser.parse_args()
    try:
        result = compare(json.loads(args.serial_off.read_text()), json.loads(args.abcd_on.read_text()))
    except (OSError, json.JSONDecodeError) as exc:
        result = {"equal": False, "first_divergence": str(exc), "runtime_parity_claim": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
