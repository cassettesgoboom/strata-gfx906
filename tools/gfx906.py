#!/usr/bin/env python3
"""Portable CPU-only helpers for gfx906 build and benchmark evidence."""
from __future__ import annotations

import argparse
import json
import platform
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "benchmarks/gfx906/schema-v1.json"
BENCH_CLIENTS = {"bench-p2": 2, "bench-p3": 3, "bench-p4": 4}
VALID_CATEGORIES = {"capacity", "performance", "correctness"}
UNITS = {"tokens/s", "ms", "s", "tokens", "GiB", "MiB", "C", "%", "count", "bool"}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: {exc}") from exc


def validate(record: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(record, dict):
        return ["record must be a JSON object"]
    required = ("schema_version", "run_id", "provenance", "hardware", "workload", "outcome", "measurements")
    for key in required:
        if key not in record:
            errors.append(f"missing required field: {key}")
    if errors:
        return errors
    if record["schema_version"] != 1:
        errors.append("schema_version must be 1")
    if not isinstance(record["run_id"], str) or not record["run_id"].strip():
        errors.append("run_id must be a non-empty string")

    provenance = record["provenance"]
    if not isinstance(provenance, dict):
        errors.append("provenance must be an object")
        provenance = {}
    for key in ("repository", "commit", "engine_version", "source", "build_id", "command"):
        if not isinstance(provenance.get(key), str) or not provenance[key].strip():
            errors.append(f"missing provenance.{key}")
    commit = provenance.get("commit", "")
    if commit and not re.fullmatch(r"[0-9a-fA-F]{7,64}", commit):
        errors.append("provenance.commit must be a hexadecimal commit SHA")
    if provenance.get("synthetic"):
        errors.append("synthetic fixture cannot be reported as run evidence")

    hardware = record["hardware"]
    if not isinstance(hardware, dict):
        errors.append("hardware must be an object")
        hardware = {}
    for key in ("gpu_model", "architecture", "rocm_version"):
        if not isinstance(hardware.get(key), str) or not hardware[key].strip():
            errors.append(f"missing hardware.{key}")
    if hardware.get("architecture") and hardware["architecture"].lower() != "gfx906":
        errors.append("hardware.architecture must be gfx906")
    for key in ("vram_gib", "ram_gib"):
        if not isinstance(hardware.get(key), (int, float)) or hardware[key] <= 0:
            errors.append(f"hardware.{key} must be a positive number in GiB")

    workload = record["workload"]
    if not isinstance(workload, dict):
        errors.append("workload must be an object")
        workload = {}
    for key in ("model", "quant", "mode"):
        if not isinstance(workload.get(key), str) or not workload[key].strip():
            errors.append(f"missing workload.{key}")
    for key in ("context_tokens", "prompt_tokens", "output_tokens", "batch"):
        if not isinstance(workload.get(key), int) or workload[key] <= 0:
            errors.append(f"workload.{key} must be a positive integer count of tokens/slots")

    outcome = record["outcome"]
    if not isinstance(outcome, dict):
        errors.append("outcome must be an object")
        outcome = {}
    category = outcome.get("category")
    if category not in VALID_CATEGORIES:
        errors.append("outcome.category must be capacity, performance, or correctness")
    if outcome.get("status") not in {"PASS", "FAIL", "NOT_RUN"}:
        errors.append("outcome.status must be PASS, FAIL, or NOT_RUN")
    finish_reason = outcome.get("finish_reason")
    if finish_reason not in {"eos", "length", "stop", "cancel", "error"}:
        errors.append("outcome.finish_reason must be eos, length, stop, cancel, or error")
    actual = outcome.get("actual_output_tokens")
    requested = workload.get("output_tokens")
    if not isinstance(actual, int) or actual < 0:
        errors.append("outcome.actual_output_tokens must be a non-negative integer")
    elif isinstance(requested, int) and actual > requested:
        errors.append("actual_output_tokens cannot exceed requested output_tokens")
    if outcome.get("status") == "PASS" and (outcome.get("output_complete") is not True or not isinstance(actual, int) or actual < 1):
        errors.append("PASS requires a non-empty output complete for its finish reason")
    if finish_reason == "length" and isinstance(actual, int) and isinstance(requested, int) and actual != requested:
        errors.append("finish_reason=length requires actual_output_tokens to equal the requested cap")
    sustained = outcome.get("sustained_tokens_min")
    if sustained is not None and (not isinstance(sustained, int) or sustained < 1 or not isinstance(actual, int) or actual < sustained):
        errors.append("sustained_tokens_min claim exceeds measured actual_output_tokens")
    if sustained is not None:
        native_count = outcome.get("native_output_tokens")
        native_source = outcome.get("native_output_source_ref")
        if native_count != actual or not isinstance(native_source, str) or not native_source.strip():
            errors.append("sustained output claim requires matching native_output_tokens and native_output_source_ref")
    category_statuses = outcome.get("category_statuses")
    if not isinstance(category_statuses, dict) or set(category_statuses) != VALID_CATEGORIES:
        errors.append("outcome.category_statuses must separately specify capacity, performance, and correctness")
    elif any(status not in {"PASS", "FAIL", "NOT_RUN"} for status in category_statuses.values()):
        errors.append("each category_statuses value must be PASS, FAIL, or NOT_RUN")
    elif category in VALID_CATEGORIES and category_statuses[category] != outcome.get("status"):
        errors.append("outcome.status must match category_statuses for the selected category")

    cache_state = outcome.get("cache_state")
    cache_evidence = record.get("cache_evidence")
    if cache_state not in {"cold", "warm", "cached", "unknown"}:
        errors.append("outcome.cache_state must be cold, warm, cached, or unknown")
    if cache_state in {"warm", "cached", "cold"}:
        if not isinstance(cache_evidence, dict):
            errors.append("cache_evidence required when cache_state is known")
        else:
            prompt_id = cache_evidence.get("prompt_identity_sha256")
            reused = cache_evidence.get("reused_tokens")
            fresh = cache_evidence.get("fresh_tokens")
            if not isinstance(prompt_id, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", prompt_id):
                errors.append("cache_evidence.prompt_identity_sha256 must be a SHA-256 hex digest")
            source_ref = cache_evidence.get("source_ref")
            if not isinstance(source_ref, str) or not source_ref.strip():
                errors.append("cache_evidence.source_ref is required")
            if not isinstance(reused, int) or reused < 0 or not isinstance(fresh, int) or fresh < 0:
                errors.append("cache_evidence reused_tokens and fresh_tokens must be non-negative integers")
            elif isinstance(workload.get("prompt_tokens"), int) and reused + fresh != workload["prompt_tokens"]:
                errors.append("cache reused_tokens + fresh_tokens must equal prompt_tokens")
            if cache_state == "cold" and isinstance(reused, int) and reused != 0:
                errors.append("cold cache claim requires reused_tokens=0")
            if cache_state in {"warm", "cached"} and isinstance(reused, int) and reused < 1:
                errors.append("warm/cached claim requires reused_tokens > 0")
            if cache_state == "cached" and isinstance(reused, int) and isinstance(workload.get("prompt_tokens"), int):
                if reused / workload["prompt_tokens"] < 0.98:
                    errors.append("cache_state=cached requires at least 98% reused prompt tokens")
    elif cache_evidence is not None:
        errors.append("cache_evidence requires a known cold, warm, or cached cache_state")
    elif cache_state == "unknown" and category == "performance" and outcome.get("status") == "PASS":
        errors.append("performance PASS requires a known cache state")

    measurements = record["measurements"]
    if not isinstance(measurements, dict):
        errors.append("measurements must be an object")
        measurements = {}
    elif not measurements:
        errors.append("measurements must contain at least one measured value")
    for name, measurement in measurements.items():
        if not isinstance(measurement, dict) or not isinstance(measurement.get("value"), (int, float)):
            errors.append(f"measurement {name!r} requires a numeric value")
            continue
        if measurement.get("unit") not in UNITS:
            errors.append(f"measurement {name!r} has unknown unit {measurement.get('unit')!r}")

    concurrency = record.get("concurrency")
    if concurrency is not None:
        if not isinstance(concurrency, dict):
            errors.append("concurrency must be an object")
        else:
            strict_claim = concurrency.get("strict_overlap_claim") is True
            intervals = concurrency.get("token_output_envelopes_ms", [])
            if not isinstance(intervals, list):
                errors.append("concurrency.token_output_envelopes_ms must be a list")
                intervals = []
            parsed: list[tuple[float, float]] = []
            for i, interval in enumerate(intervals):
                if (not isinstance(interval, dict) or not isinstance(interval.get("start_ms"), (int, float))
                        or not isinstance(interval.get("end_ms"), (int, float)) or interval["end_ms"] <= interval["start_ms"]
                        or not isinstance(interval.get("emitted_tokens"), int) or interval["emitted_tokens"] < 1
                        or not isinstance(interval.get("request_id"), str) or not interval["request_id"]):
                    errors.append(f"token output envelope {i} needs request_id, start_ms < end_ms, and emitted_tokens > 0")
                else:
                    parsed.append((interval["start_ms"], interval["end_ms"]))
                    if interval.get("native_emitted_tokens") != interval["emitted_tokens"]:
                        errors.append(f"token output envelope {i} client/native emitted token counts disagree")
            if strict_claim:
                if len(parsed) < 2:
                    errors.append("strict overlap claim requires at least two token output envelopes")
                request_ids = [item.get("request_id") for item in intervals if isinstance(item, dict)]
                if len(request_ids) != len(set(request_ids)):
                    errors.append("strict overlap claim requires a unique request_id per token output envelope")
                expected_lanes = len(set(request_ids))
                overlap_start = max((start for start, _ in parsed), default=0)
                overlap_end = min((end for _, end in parsed), default=0)
                if len(parsed) >= 2 and overlap_start >= overlap_end:
                    errors.append("strict overlap claim requires a common token-output intersection greater than zero")
                occupancy = concurrency.get("native_occupancy")
                if not isinstance(occupancy, dict):
                    errors.append("strict overlap claim requires explicit native occupancy evidence")
                else:
                    source_ref = occupancy.get("source_ref")
                    if not isinstance(source_ref, str) or not source_ref.strip():
                        errors.append("native occupancy requires source_ref")
                    peak = occupancy.get("active_slots_peak")
                    offered = occupancy.get("offered_slots")
                    if not isinstance(peak, int) or not isinstance(offered, int) or peak < expected_lanes or peak > offered or offered < expected_lanes:
                        errors.append(f"native occupancy must prove {expected_lanes} active lanes <= offered_slots")
                    if occupancy.get("evidence_kind") not in {"native_window_counter", "native_slot_intervals"}:
                        errors.append("native occupancy evidence_kind must be native_window_counter or native_slot_intervals")
                    if occupancy.get("evidence_kind") == "native_window_counter":
                        wstart, wend = occupancy.get("window_start_ms"), occupancy.get("window_end_ms")
                        if (not isinstance(wstart, (int, float)) or not isinstance(wend, (int, float)) or wend <= wstart
                                or wstart > overlap_start or wend < overlap_end):
                            errors.append("native counter window must cover the common token-output intersection")
                        samples = occupancy.get("samples_ms", [])
                        if not isinstance(samples, list):
                            errors.append("native counter samples_ms must be a list")
                            samples = []
                        valid_samples = []
                        for sample in samples:
                            if (not isinstance(sample, dict) or not isinstance(sample.get("time_ms"), (int, float))
                                    or not isinstance(sample.get("active_slots"), int) or sample["active_slots"] < 0):
                                errors.append("native counter sample needs numeric time_ms and non-negative active_slots")
                            else:
                                valid_samples.append(sample)
                                if isinstance(offered, int) and sample["active_slots"] > offered:
                                    errors.append("native counter active_slots exceeds offered_slots")
                                if (isinstance(wstart, (int, float)) and isinstance(wend, (int, float))
                                        and not wstart <= sample["time_ms"] <= wend):
                                    errors.append("native counter sample falls outside its declared window")
                        if valid_samples and isinstance(peak, int) and max(s["active_slots"] for s in valid_samples) != peak:
                            errors.append("native active_slots_peak does not match native counter samples")
                        if not any(overlap_start <= s["time_ms"] <= overlap_end and s["active_slots"] >= expected_lanes
                                   for s in valid_samples):
                            errors.append(f"native counter samples do not prove {expected_lanes} active lanes during token overlap")
                    if occupancy.get("evidence_kind") == "native_slot_intervals":
                        slot_intervals = occupancy.get("slot_intervals_ms", [])
                        if not isinstance(slot_intervals, list):
                            errors.append("native slot intervals must be a list")
                        else:
                            native = []
                            for si in slot_intervals:
                                if (not isinstance(si, dict) or not isinstance(si.get("start_ms"), (int, float))
                                        or not isinstance(si.get("end_ms"), (int, float)) or si["end_ms"] <= si["start_ms"]):
                                    errors.append("native slot interval requires numeric start_ms < end_ms")
                                else:
                                    native.append((si["start_ms"], si["end_ms"]))
                            events = [(start, 1) for start, _ in native] + [(end, -1) for _, end in native]
                            active = native_peak = 0
                            for _, delta in sorted(events, key=lambda event: (event[0], event[1])):
                                active += delta
                                native_peak = max(native_peak, active)
                            if isinstance(peak, int) and native_peak != peak:
                                errors.append(f"native occupancy peak {peak} does not match native interval evidence {native_peak}")
                            events_clipped = []
                            for start, end in native:
                                left, right = max(start, overlap_start), min(end, overlap_end)
                                if left < right:
                                    events_clipped.extend(((left, 1), (right, -1)))
                            active = intersection_peak = 0
                            for _, delta in sorted(events_clipped, key=lambda event: (event[0], event[1])):
                                active += delta
                                intersection_peak = max(intersection_peak, active)
                            if intersection_peak < expected_lanes:
                                errors.append(f"native slot intervals do not prove {expected_lanes} active lanes during token overlap")
    return errors


def cmd_doctor(_: argparse.Namespace) -> int:
    print(f"Python: {platform.python_version()} ({sys.executable})")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Repository: {ROOT}")
    print(f"Schema: {'present' if SCHEMA.is_file() else 'missing'} ({SCHEMA})")
    for tool in ("git", "cmake", "hipcc", "ctest"):
        print(f"{tool}: {shutil.which(tool) or 'not installed'}")
    return 0 if SCHEMA.is_file() else 1


def cmd_test_cpu(_: argparse.Namespace) -> int:
    command = [sys.executable, "-m", "unittest", "discover", "-s", "tests/gfx906", "-v"]
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def cmd_bench_validate(args: argparse.Namespace) -> int:
    paths = sorted(args.paths or [str(p) for p in (ROOT / "benchmarks/gfx906/fixtures").glob("*.json")])
    if not paths:
        print("No benchmark records found", file=sys.stderr)
        return 2
    failed = False
    for name in paths:
        try:
            record = load_json(Path(name))
            problems = validate(record)
        except ValueError as exc:
            problems = [str(exc)]
            record = {}
        status = "INVALID" if problems else "VALID"
        print(f"{status}: {name}")
        for problem in problems:
            print(f"  - {problem}")
        if problems:
            failed = True
        elif record.get("outcome", {}).get("status") == "PASS":
            print(f"  category: {record['outcome']['category']}; record structure accepted (raw evidence not independently verified)")
    return 1 if failed else 0


def cmd_report(args: argparse.Namespace) -> int:
    try:
        record = load_json(Path(args.record))
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    problems = validate(record)
    if problems:
        print("Report withheld: record is invalid", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1
    hw, work, outcome = record["hardware"], record["workload"], record["outcome"]
    print(f"Run: {record['run_id']} | {outcome['category']} | {outcome['status']}")
    print(f"GPU: {hw['gpu_model']} ({hw['architecture']}); ROCm {hw['rocm_version']}")
    print(f"Model: {work['model']} {work['quant']}; prompt {work['prompt_tokens']} tokens; context {work['context_tokens']}; batch {work['batch']}")
    print(f"Output: {outcome.get('actual_output_tokens')} tokens; cache={outcome.get('cache_state')}; complete={outcome.get('output_complete')}")
    print(f"Source: {record['provenance']['repository']}@{record['provenance']['commit']} ({record['provenance']['build_id']})")
    conc = record.get("concurrency")
    if conc:
        native = conc.get("native_occupancy")
        if native:
            print(f"Native occupancy: {native['active_slots_peak']}/{native['offered_slots']} ({native['evidence_kind']}; {native['source_ref']})")
        envelopes = conc.get("token_output_envelopes_ms", [])
        if conc.get("strict_overlap_claim") and envelopes:
            start = max(item["start_ms"] for item in envelopes)
            end = min(item["end_ms"] for item in envelopes)
            emitted = sum(item["emitted_tokens"] for item in envelopes)
            print(f"Strict token overlap: {max(0, end - start):g} ms common intersection; {emitted} emitted tokens measured")
    for name, metric in record["measurements"].items():
        print(f"{name}: {metric['value']} {metric['unit']}")
    return 0


def cmake_build_commands(rocm_root: str, ggml_dir: str, build_dir: str) -> list[list[str]]:
    return [
        ["cmake", "-S", ".", "-B", build_dir, "-G", "Ninja", "-DSTRATA_HIP_GFX906=ON",
         "-DCMAKE_HIP_ARCHITECTURES=gfx906", f"-DSTRATA_GGML_DIR={ggml_dir}",
         f"-DCMAKE_C_COMPILER={rocm_root}/llvm/bin/clang",
         f"-DCMAKE_CXX_COMPILER={rocm_root}/llvm/bin/clang++"],
        ["ninja", "-C", build_dir, "strata"],
    ]


def checkout_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def cmd_build_gfx906(args: argparse.Namespace) -> int:
    build_path = Path(args.build_dir)
    resolved_build = checkout_path(args.build_dir).resolve()
    if (build_path.is_absolute() or ".." in build_path.parts or str(build_path) in {"", "."}
            or not resolved_build.is_relative_to(ROOT.resolve())):
        print("--build-dir must be a relative path inside this checkout", file=sys.stderr)
        return 2
    commands = cmake_build_commands(args.rocm_root.rstrip("/"), args.ggml_dir, args.build_dir)
    print("Dry-run only unless --apply is supplied. No GPU or privileged host action is performed.")
    print("Dependencies: CMake, Ninja, git, Python 3, C/C++ build tools, a compatible gfx906 HIP/hipBLAS toolchain, ROCm clang/clang++, and a llama.cpp checkout with ggml.")
    print("Source recipe: docs/AMD_HIP.md gfx906 section; upstream marks gfx906 community-tested and opt-in.")
    for command in commands:
        print(shlex.join(command))
    if not args.apply:
        return 0
    if not (checkout_path(args.ggml_dir) / "ggml").is_dir():
        print("--ggml-dir must name an existing llama.cpp checkout containing ggml/", file=sys.stderr)
        return 2
    rocm = checkout_path(args.rocm_root)
    for tool in (rocm / "llvm/bin/clang", rocm / "llvm/bin/clang++"):
        if not tool.is_file():
            print(f"required ROCm compiler not found: {tool}", file=sys.stderr)
            return 2
    for name in ("cmake", "ninja", "git", "python3", "cc", "c++"):
        if not shutil.which(name):
            print(f"required build dependency not found on PATH: {name}", file=sys.stderr)
            return 2
    for command in commands:
        rc = subprocess.run(command, cwd=ROOT, check=False).returncode
        if rc:
            return rc
    return 0


def valid_target_url(value: str) -> bool:
    from urllib.parse import urlsplit
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname) and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment


def cmd_bench_plan(args: argparse.Namespace) -> int:
    clients = BENCH_CLIENTS[args.command]
    print("Dry-run only unless --apply and --target-url are supplied. This sends real prompts to an already-running server; it never starts one.")
    print("This upstream client reports HTTP burst totals only; it does not prove native slot occupancy or strict token-level overlap.")
    if not args.apply:
        target = args.target_url or "<TARGET_URL>"
        out = args.json_out or "<RESULT_JSON>"
        save_dir = args.save_dir or "<RESPONSE_DIR>"
    else:
        if args.rounds < 1 or args.max_tokens < 1:
            print("--rounds and --max-tokens must be positive", file=sys.stderr)
            return 2
        if not args.target_url or not valid_target_url(args.target_url):
            print("--apply requires --target-url with an http(s) URL without embedded credentials/query", file=sys.stderr)
            return 2
        if not args.json_out or not args.save_dir:
            print("--apply requires --json-out and --save-dir so results and raw answers use explicit paths", file=sys.stderr)
            return 2
        if checkout_path(args.json_out).exists() or checkout_path(args.save_dir).exists():
            print("--json-out and --save-dir must not already exist; refusing to overwrite", file=sys.stderr)
            return 2
        if not checkout_path(args.json_out).parent.is_dir():
            print("the --json-out parent directory must already exist", file=sys.stderr)
            return 2
        target, out, save_dir = args.target_url, args.json_out, args.save_dir
    command = [sys.executable, "tools/serve_load.py", target, "--clients", str(clients),
               "--rounds", str(args.rounds), "--max-tokens", str(args.max_tokens), "--json", out, "--save", save_dir]
    print(shlex.join(command))
    if not args.apply:
        return 0
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("doctor", help="inspect CPU-side tool availability; never accesses GPUs")
    p.set_defaults(func=cmd_doctor)
    p = sub.add_parser("test-cpu", help="run stdlib CPU-only tests")
    p.set_defaults(func=cmd_test_cpu)
    p = sub.add_parser("bench-validate", help="validate benchmark evidence JSON")
    p.add_argument("paths", nargs="*", help="JSON record paths")
    p.set_defaults(func=cmd_bench_validate)
    p = sub.add_parser("report", help="render a validated benchmark record")
    p.add_argument("record", help="benchmark record JSON")
    p.set_defaults(func=cmd_report)
    p = sub.add_parser("build-gfx906", help="plan or explicitly configure/build the inherited gfx906 target")
    p.add_argument("--rocm-root", required=True, help="ROCm install root, e.g. /opt/rocm")
    p.add_argument("--ggml-dir", required=True, help="llama.cpp checkout used by STRATA_GGML_DIR")
    p.add_argument("--build-dir", default="build-906", help="relative build directory inside this checkout")
    p.add_argument("--apply", action="store_true", help="run cmake and ninja; no GPU/privileged action")
    p.set_defaults(func=cmd_build_gfx906)
    for name in BENCH_CLIENTS:
        p = sub.add_parser(name, help=f"plan or run the upstream HTTP load client at {BENCH_CLIENTS[name]} clients")
        p.add_argument("--target-url", help="already-running Strata server URL; never starts a server")
        p.add_argument("--rounds", type=int, default=3)
        p.add_argument("--max-tokens", type=int, default=512)
        p.add_argument("--json-out", help="required with --apply; exact JSON output path")
        p.add_argument("--save-dir", help="required with --apply; new directory for raw response text")
        p.add_argument("--apply", action="store_true", help="send requests to the supplied live server")
        p.set_defaults(func=cmd_bench_plan)
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))
