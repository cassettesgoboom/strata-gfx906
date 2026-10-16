#!/usr/bin/env python3
"""CPU-only comparator for serial OFF vs opt-in AB/CD ON native traces.

The input format is specified by benchmarks/gfx906/fixtures/abcd-parity-contract-v1.json.
It compares committed results at the same request/commit boundary, and reports the
first differing boundary. It deliberately does not treat host/API text as native proof.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PARITY_FIELDS = (
    "native_token_id",
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
    "mtp_sha256", "device_and_runtime",
)


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _index_run(run: dict[str, Any], label: str) -> tuple[dict[str, dict[str, Any]], str | None]:
    if run.get("trace_kind") != "native_commit_trace":
        return {}, f"{label}: trace_kind must be native_commit_trace"
    requests = run.get("requests")
    if not isinstance(requests, list) or not requests:
        return {}, f"{label}: requests must be a non-empty list"
    indexed: dict[str, dict[str, Any]] = {}
    for req in requests:
        if not isinstance(req, dict) or not isinstance(req.get("request_id"), str):
            return {}, f"{label}: every request needs a string request_id"
        rid = req["request_id"]
        if rid in indexed:
            return {}, f"{label}: duplicate request_id {rid}"
        steps = req.get("commits")
        if not isinstance(steps, list) or not steps:
            return {}, f"{label}: {rid}: commits must be a non-empty list"
        by_boundary: dict[int, dict[str, Any]] = {}
        for step in steps:
            if not isinstance(step, dict) or type(step.get("commit_index")) is not int:
                return {}, f"{label}: {rid}: commit needs integer commit_index"
            boundary = step["commit_index"]
            if boundary in by_boundary:
                return {}, f"{label}: {rid}: duplicate commit_index {boundary}"
            for field in PARITY_FIELDS:
                if field not in step:
                    return {}, f"{label}: {rid} commit {boundary}: missing {field}"
            by_boundary[boundary] = step
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
    for field in MATCHED_PROVENANCE_FIELDS:
        if serial["provenance"][field] != abcd["provenance"][field]:
            return {"equal": False, "first_divergence": f"provenance.{field} differs"}
    left, err = _index_run(serial, "serial")
    if err:
        return {"equal": False, "first_divergence": err}
    right, err = _index_run(abcd, "abcd")
    if err:
        return {"equal": False, "first_divergence": err}

    if set(left) != set(right):
        return {"equal": False, "first_divergence": "request_ids differ"}
    for rid in sorted(left):
        a, b = left[rid], right[rid]
        for field in ("cache_key_sha256", "cache_reused_tokens", "cache_fresh_tokens"):
            if a.get(field) != b.get(field):
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
