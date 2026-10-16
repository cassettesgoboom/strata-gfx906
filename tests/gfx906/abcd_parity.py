#!/usr/bin/env python3
"""CPU-only comparator for serial OFF vs opt-in AB/CD ON native traces.

The input format is specified by benchmarks/gfx906/fixtures/abcd-parity-contract-v2.json.
It compares committed results at the same request/commit boundary, and reports the
first differing boundary. It deliberately does not treat host/API text as native proof.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PARITY_FIELDS = (
    "native_token_ids",
    "mtp_offered_token_ids",
    "mtp_accepted_token_ids",
    "gdn_state_sha256",
    "recurrent_state_sha256",
)
PROVENANCE_FIELDS = (
    "source_commit", "binary_sha256", "model_sha256", "tokenizer_sha256",
    "mtp_sha256", "command_sha256", "device_and_runtime", "trace_capture_method",
)
MATCHED_PROVENANCE_FIELDS = (
    "source_commit", "binary_sha256", "model_sha256", "tokenizer_sha256",
    "mtp_sha256", "command_sha256", "device_and_runtime",
)
SHA256_FIELDS = {
    "binary_sha256", "model_sha256", "tokenizer_sha256", "mtp_sha256", "command_sha256",
}


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _index_run(run: dict[str, Any], label: str) -> tuple[dict[str, dict[str, Any]], str | None]:
    if run.get("trace_kind") != "native_transaction_trace_v2":
        return {}, f"{label}: trace_kind must be native_transaction_trace_v2"
    requests = run.get("requests")
    if not isinstance(requests, list) or not requests:
        return {}, f"{label}: requests must be a non-empty list"
    indexed: dict[str, dict[str, Any]] = {}
    for req in requests:
        if not isinstance(req, dict) or not isinstance(req.get("request_id"), str):
            return {}, f"{label}: every request needs a string request_id"
        rid = req["request_id"]
        if not rid:
            return {}, f"{label}: request_id must not be empty"
        if rid in indexed:
            return {}, f"{label}: duplicate request_id {rid}"
        for field in ("cache_key_sha256", "input_token_ids_sha256", "sampler_state_sha256"):
            if not _is_sha256(req.get(field)):
                return {}, f"{label}: {rid}: {field} must be a lowercase SHA-256 hex digest"
        for field in ("cache_reused_tokens", "cache_fresh_tokens"):
            if type(req.get(field)) is not int or req[field] < 0:
                return {}, f"{label}: {rid}: {field} must be a non-negative integer"
        steps = req.get("commits")
        if not isinstance(steps, list) or not steps:
            return {}, f"{label}: {rid}: commits must be a non-empty list"
        by_boundary: dict[int, dict[str, Any]] = {}
        seen_boundaries: list[int] = []
        for step in steps:
            if not isinstance(step, dict) or type(step.get("commit_index")) is not int:
                return {}, f"{label}: {rid}: commit needs integer commit_index"
            boundary = step["commit_index"]
            if boundary < 0:
                return {}, f"{label}: {rid}: commit_index must be non-negative"
            if boundary in by_boundary:
                return {}, f"{label}: {rid}: duplicate commit_index {boundary}"
            for field in PARITY_FIELDS:
                if field not in step:
                    return {}, f"{label}: {rid} commit {boundary}: missing {field}"
            token_ids = step["native_token_ids"]
            if (not isinstance(token_ids, list) or not token_ids or
                    any(type(token_id) is not int or token_id < 0 for token_id in token_ids)):
                return {}, f"{label}: {rid} commit {boundary}: native_token_ids must be a non-empty list of non-negative integer token IDs"
            for field in ("mtp_offered_token_ids", "mtp_accepted_token_ids"):
                ids = step[field]
                if not isinstance(ids, list) or any(type(token_id) is not int or token_id < 0 for token_id in ids):
                    return {}, f"{label}: {rid} commit {boundary}: {field} must be a list of non-negative integer token IDs"
            for field in ("gdn_state_sha256", "recurrent_state_sha256"):
                if not _is_sha256(step[field]):
                    return {}, f"{label}: {rid} commit {boundary}: {field} must be a lowercase SHA-256 hex digest"
            by_boundary[boundary] = step
            seen_boundaries.append(boundary)
        if seen_boundaries != list(range(len(steps))):
            return {}, f"{label}: {rid}: commit_index values must be ordered, zero-based, and contiguous"
        req_copy = dict(req)
        req_copy["_commits"] = by_boundary
        indexed[rid] = req_copy
    return indexed, None


def compare(serial: dict[str, Any], abcd: dict[str, Any]) -> dict[str, Any]:
    """Return {equal, first_divergence}; occupancy is reported but not parity-compared."""
    if serial.get("mode") != "serial_off":
        return {"equal": False, "first_divergence": "serial.mode must be serial_off"}
    if abcd.get("mode") != "abcd_on":
        return {"equal": False, "first_divergence": "abcd.mode must be abcd_on"}
    for label, run in (("serial", serial), ("abcd", abcd)):
        provenance = run.get("provenance")
        if not isinstance(provenance, dict):
            return {"equal": False, "first_divergence": f"{label}: provenance object is required"}
        for field in PROVENANCE_FIELDS:
            if not isinstance(provenance.get(field), str) or not provenance[field]:
                return {"equal": False, "first_divergence": f"{label}: provenance.{field} is required"}
            if field in SHA256_FIELDS and not _is_sha256(provenance[field]):
                return {"equal": False, "first_divergence": f"{label}: provenance.{field} must be a lowercase SHA-256 hex digest"}
    for field in MATCHED_PROVENANCE_FIELDS:
        if serial["provenance"][field] != abcd["provenance"][field]:
            return {"equal": False, "first_divergence": f"provenance.{field} differs"}
    left, err = _index_run(serial, "serial")
    if err:
        return {"equal": False, "first_divergence": err}
    right, err = _index_run(abcd, "abcd")
    if err:
        return {"equal": False, "first_divergence": err}

    if list(left) != list(right):
        return {"equal": False, "first_divergence": "request_ids differ"}
    for rid in left:
        a, b = left[rid], right[rid]
        for field in ("cache_key_sha256", "cache_reused_tokens", "cache_fresh_tokens",
                      "input_token_ids_sha256", "sampler_state_sha256"):
            if a[field] != b[field]:
                return {"equal": False, "first_divergence": f"request {rid}: {field} differs"}
        ca, cb = a["_commits"], b["_commits"]
        if set(ca) != set(cb):
            missing = sorted(set(ca) ^ set(cb))[0]
            return {"equal": False, "first_divergence": f"request {rid} commit {missing}: boundary missing on one side"}
        for boundary in sorted(ca):
            for field in PARITY_FIELDS:
                if ca[boundary][field] != cb[boundary][field]:
                    return {"equal": False, "first_divergence":
                            f"request {rid} commit {boundary}: {field} differs"}
    return {
        "equal": True,
        "synthetic_contract_only": bool(serial["provenance"].get("synthetic") or abcd["provenance"].get("synthetic")),
        "runtime_parity_claim": False,
        "warning": "Equality compares supplied traces only; capture/provenance authenticity and full correctness require independent evidence.",
        "state_comparison_boundary": "commit_window_end",
        "first_divergence": None,
        "occupancy": {
            "serial": serial.get("occupancy"),
            "abcd": abcd.get("occupancy"),
            "compared_for_parity": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("serial_off", type=Path)
    parser.add_argument("abcd_on", type=Path)
    args = parser.parse_args()
    try:
        result = compare(load(args.serial_off), load(args.abcd_on))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"equal": False, "first_divergence": str(exc)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["equal"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
