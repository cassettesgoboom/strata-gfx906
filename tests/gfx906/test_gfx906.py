import importlib.util
import json
import io
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("gfx906", ROOT / "tools/gfx906.py")
gfx906 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gfx906)


def record():
    return {
        "schema_version": 1,
        "run_id": "local-run",
        "provenance": {
            "repository": "Niko1221/Strata", "commit": "296b59d2", "engine_version": "0.1.44.1",
            "source": "upstream", "build_id": "local-build", "command": "strata generate ..."
        },
        "hardware": {"gpu_model": "MI50", "architecture": "gfx906", "rocm_version": "10.1", "vram_gib": 32, "ram_gib": 64},
        "workload": {"model": "Qwen3.8", "quant": "IQ3_XXS", "mode": "batch", "context_tokens": 8192,
                     "prompt_tokens": 1024, "output_tokens": 64, "batch": 4},
        "outcome": {"category": "performance", "status": "PASS", "output_complete": True,
                    "cache_state": "warm", "actual_output_tokens": 64, "finish_reason": "length",
                    "category_statuses": {"capacity": "NOT_RUN", "performance": "PASS", "correctness": "NOT_RUN"}},
        "cache_evidence": {"prompt_identity_sha256": "a" * 64, "reused_tokens": 512, "fresh_tokens": 512,
                           "source_ref": "cache.log:prompt-cache"},
        "measurements": {"decode": {"value": 42.0, "unit": "tokens/s"}}
    }


def with_strict_overlap(record_value):
    record_value["concurrency"] = {
        "strict_overlap_claim": True,
        "token_output_envelopes_ms": [
            {"request_id": "a", "start_ms": 10, "end_ms": 30, "emitted_tokens": 64, "native_emitted_tokens": 64},
            {"request_id": "b", "start_ms": 20, "end_ms": 40, "emitted_tokens": 64, "native_emitted_tokens": 64},
        ],
        "native_occupancy": {"evidence_kind": "native_window_counter", "source_ref": "engine.log:batch_slots",
                             "offered_slots": 4, "active_slots_peak": 2, "window_start_ms": 10, "window_end_ms": 40,
                             "samples_ms": [{"time_ms": 25, "active_slots": 2}]},
    }
    return record_value


class EvidenceValidationTests(unittest.TestCase):
    def test_minimal_complete_record(self):
        self.assertEqual(gfx906.validate(record()), [])

    def test_unknown_properties_are_rejected_for_fixed_schema_objects(self):
        cases = []
        item = record(); item["extra"] = 1; cases.append(item)
        item = record(); item["provenance"]["extra"] = 1; cases.append(item)
        item = record(); item["hardware"]["extra"] = 1; cases.append(item)
        item = record(); item["workload"]["extra"] = 1; cases.append(item)
        item = record(); item["outcome"]["extra"] = 1; cases.append(item)
        item = record(); item["outcome"]["category_statuses"]["extra"] = "PASS"; cases.append(item)
        item = record(); item["cache_evidence"]["extra"] = 1; cases.append(item)
        item = record(); item["measurements"]["decode"]["extra"] = 1; cases.append(item)
        item = with_strict_overlap(record()); item["concurrency"]["extra"] = 1; cases.append(item)
        item = with_strict_overlap(record()); item["concurrency"]["token_output_envelopes_ms"][0]["extra"] = 1; cases.append(item)
        item = with_strict_overlap(record()); item["concurrency"]["native_occupancy"]["extra"] = 1; cases.append(item)
        item = with_strict_overlap(record()); item["concurrency"]["native_occupancy"]["samples_ms"][0]["extra"] = 1; cases.append(item)
        for item in cases:
            with self.subTest(item=item):
                self.assertTrue(any("unknown property" in error for error in gfx906.validate(item)))

    def test_cli_object_boundaries_match_schema_additional_properties(self):
        schema = json.loads((ROOT / "benchmarks/gfx906/schema-v1.json").read_text())

        def walk(node):
            if isinstance(node, dict):
                if node.get("type") == "object" and "properties" in node:
                    self.assertIs(node.get("additionalProperties"), False)
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(schema)

    def test_exact_architecture_and_json_numeric_types(self):
        item = record(); item["hardware"]["architecture"] = "GFX906"
        self.assertTrue(any("equal gfx906 exactly" in error for error in gfx906.validate(item)))
        item = record(); item["workload"]["batch"] = True
        self.assertTrue(any("workload.batch" in error for error in gfx906.validate(item)))
        item = record(); item["hardware"]["vram_gib"] = True
        self.assertTrue(any("hardware.vram_gib" in error for error in gfx906.validate(item)))
        item = record(); item["measurements"]["decode"]["value"] = True
        self.assertTrue(any("requires a numeric value" in error for error in gfx906.validate(item)))

    def test_non_finite_numbers_are_rejected(self):
        for value in (float("nan"), float("inf"), float("-inf")):
            item = record(); item["measurements"]["decode"]["value"] = value
            self.assertTrue(any("requires a numeric value" in error for error in gfx906.validate(item)))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nan.json"
            path.write_text('{"value": NaN}')
            with self.assertRaises(ValueError):
                gfx906.load_json(path)

    def test_missing_provenance_is_rejected(self):
        item = record()
        del item["provenance"]["commit"]
        self.assertTrue(any("provenance.commit" in e for e in gfx906.validate(item)))

    def test_partial_output_and_cold_cached_claim_cannot_pass(self):
        for key, value in (("output_complete", False), ("actual_output_tokens", 2)):
            with self.subTest(key=key):
                item = record()
                item["outcome"][key] = value
                self.assertTrue(gfx906.validate(item))
        item = record()
        item["outcome"]["cache_state"] = "cold"
        self.assertTrue(gfx906.validate(item))

    def test_unknown_units_are_rejected(self):
        item = record()
        item["measurements"]["decode"]["unit"] = "widgets/s"
        self.assertTrue(any("unknown unit" in e for e in gfx906.validate(item)))

    def test_http_only_overlap_cannot_claim_native_batch(self):
        item = with_strict_overlap(record())
        del item["concurrency"]["native_occupancy"]
        self.assertTrue(any("explicit native occupancy" in e for e in gfx906.validate(item)))

    def test_missing_native_occupancy_is_rejected(self):
        item = with_strict_overlap(record())
        item["concurrency"]["native_occupancy"] = {"evidence_kind": "native_window_counter", "source_ref": "engine.log",
                                                      "offered_slots": 4, "active_slots_peak": 1}
        self.assertTrue(any("native occupancy must prove 2 active lanes" in e for e in gfx906.validate(item)))

    def test_p4_requires_four_native_active_lanes(self):
        item = with_strict_overlap(record())
        item["concurrency"]["token_output_envelopes_ms"] = [
            {"request_id": str(i), "start_ms": 10, "end_ms": 30, "emitted_tokens": 64, "native_emitted_tokens": 64}
            for i in range(4)
        ]
        self.assertTrue(any("4 active lanes" in e for e in gfx906.validate(item)))

    def test_duplicate_request_ids_are_rejected(self):
        item = with_strict_overlap(record())
        item["concurrency"]["token_output_envelopes_ms"][1]["request_id"] = "a"
        self.assertTrue(any("unique request_id" in e for e in gfx906.validate(item)))

    def test_token_envelopes_need_positive_common_intersection(self):
        item = with_strict_overlap(record())
        item["concurrency"]["token_output_envelopes_ms"][1]["start_ms"] = 30
        self.assertTrue(any("common token-output intersection" in e for e in gfx906.validate(item)))

    def test_native_window_counter_must_cover_token_overlap(self):
        item = with_strict_overlap(record())
        item["concurrency"]["native_occupancy"]["window_start_ms"] = 21
        self.assertTrue(any("must cover the common token-output intersection" in e for e in gfx906.validate(item)))

    def test_mismatched_actual_token_count_is_rejected(self):
        item = record()
        item["outcome"]["actual_output_tokens"] = 65
        self.assertTrue(any("cannot exceed" in e for e in gfx906.validate(item)))

    def test_short_natural_eos_is_valid(self):
        item = record()
        item["outcome"].update(finish_reason="eos", actual_output_tokens=23)
        self.assertEqual(gfx906.validate(item), [])

    def test_sustained_512_claim_requires_512_emitted(self):
        item = record()
        item["workload"]["output_tokens"] = 512
        item["outcome"].update(finish_reason="eos", actual_output_tokens=511, sustained_tokens_min=512)
        item["cache_evidence"]["fresh_tokens"] = 0
        self.assertTrue(any("sustained_tokens_min" in e for e in gfx906.validate(item)))

    def test_envelope_token_count_must_match_native_output_count(self):
        item = with_strict_overlap(record())
        item["concurrency"]["token_output_envelopes_ms"][0]["native_emitted_tokens"] = 63
        self.assertTrue(any("client/native emitted token counts disagree" in e for e in gfx906.validate(item)))

    def test_cached_claim_requires_98_percent_prompt_reuse(self):
        item = record()
        item["outcome"]["cache_state"] = "cached"
        self.assertTrue(any("at least 98%" in e for e in gfx906.validate(item)))
        item["cache_evidence"].update(reused_tokens=1008, fresh_tokens=16)
        self.assertEqual(gfx906.validate(item), [])

    def test_cached_claim_requires_source_reference(self):
        item = record()
        item["outcome"]["cache_state"] = "cached"
        item["cache_evidence"].update(reused_tokens=1008, fresh_tokens=16)
        del item["cache_evidence"]["source_ref"]
        self.assertTrue(any("source_ref" in e for e in gfx906.validate(item)))

    def test_category_statuses_remain_separate(self):
        item = record()
        item["outcome"]["category_statuses"]["performance"] = "NOT_RUN"
        self.assertTrue(any("must match category_statuses" in e for e in gfx906.validate(item)))

    def test_planners_are_dry_run_by_default(self):
        args = Namespace(command="bench-p2", target_url=None, json_out=None, save_dir=None, apply=False, rounds=3, max_tokens=512)
        with patch.object(gfx906.subprocess, "run") as run, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(gfx906.cmd_bench_plan(args), 0)
        run.assert_not_called()
        self.assertIn("<TARGET_URL>", output.getvalue())

    def test_bench_apply_requires_explicit_target_and_output(self):
        args = Namespace(command="bench-p2", target_url=None, json_out=None, save_dir=None, apply=True, rounds=3, max_tokens=512)
        self.assertEqual(gfx906.cmd_bench_plan(args), 2)

    def test_bench_apply_refuses_existing_output(self):
        args = Namespace(command="bench-p2", target_url="http://127.0.0.1:8080", json_out=str(Path(__file__)),
                         save_dir="new-answer-dir", apply=True, rounds=3, max_tokens=512)
        with patch.object(gfx906.subprocess, "run") as run:
            self.assertEqual(gfx906.cmd_bench_plan(args), 2)
        run.assert_not_called()

    def test_bench_apply_refuses_resolved_equivalent_output_paths(self):
        args = Namespace(command="bench-p2", target_url="http://127.0.0.1:8080",
                         json_out="new-dir/../same-output.json", save_dir="same-output.json",
                         apply=True, rounds=3, max_tokens=512)
        with patch.object(gfx906.subprocess, "run") as run:
            self.assertEqual(gfx906.cmd_bench_plan(args), 2)
        run.assert_not_called()

    def test_bench_apply_prints_exact_command_without_secret(self):
        args = Namespace(command="bench-p3", target_url="http://127.0.0.1:8080", json_out="results.json", save_dir="answers-new",
                         apply=True, rounds=2, max_tokens=512)
        with patch.object(gfx906.subprocess, "run", return_value=Namespace(returncode=0)) as run, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(gfx906.cmd_bench_plan(args), 0)
        command = run.call_args.args[0]
        self.assertIn("--clients 3", output.getvalue())
        self.assertEqual(command[1:3], ["tools/serve_load.py", "http://127.0.0.1:8080"])
        self.assertIn("--save", command)
        self.assertNotIn("STRATA_KEY", output.getvalue())

    def test_build_gfx906_dry_run_never_invokes_commands(self):
        args = Namespace(rocm_root="/opt/rocm", ggml_dir="third_party/llama.cpp", build_dir="build-906", apply=False)
        with patch.object(gfx906.subprocess, "run") as run, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(gfx906.cmd_build_gfx906(args), 0)
        run.assert_not_called()
        self.assertIn("-DSTRATA_HIP_GFX906=ON", output.getvalue())

    def test_build_path_must_stay_inside_checkout(self):
        args = Namespace(rocm_root="/opt/rocm", ggml_dir="third_party/llama.cpp", build_dir="../outside", apply=False)
        self.assertEqual(gfx906.cmd_build_gfx906(args), 2)

    def test_synthetic_fixture_cannot_be_reported_as_run(self):
        item = record()
        item["provenance"]["synthetic"] = True
        self.assertTrue(any("synthetic fixture" in e for e in gfx906.validate(item)))

    def test_synthetic_fixtures_are_parseable_and_explicit(self):
        folder = ROOT / "tests/gfx906/fixtures"
        paths = list(folder.glob("*.json"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.name):
                fixture = json.loads(path.read_text())
                self.assertTrue(fixture["provenance"]["synthetic"])
                self.assertEqual(gfx906.validate(fixture), ["synthetic fixture cannot be reported as run evidence"])


if __name__ == "__main__":
    unittest.main()
