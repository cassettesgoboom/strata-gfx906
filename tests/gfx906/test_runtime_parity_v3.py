import json
import os
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "benchmarks/gfx906/fixtures"
sys.path.insert(0, str(Path(__file__).parent))
import runtime_parity_v3 as parity
import runtime_parity_v3_fixtures as fixtures


class RuntimeParityV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serial = json.loads((FIXTURES / "native-runtime-parity-serial-synthetic.json").read_text())
        cls.candidate = json.loads((FIXTURES / "native-runtime-parity-abcd-synthetic.json").read_text())
        cls.current_inventory = json.loads((FIXTURES / "native-runtime-parity-current-qwen38-inventory-synthetic.json").read_text())

    def test_bounded_synthetic_pair_matches_without_runtime_claim(self):
        result = parity.compare(self.serial, self.candidate)
        self.assertTrue(result["equal"], result)
        self.assertTrue(result["synthetic_contract_only"])
        self.assertFalse(result["runtime_parity_claim"])
        self.assertEqual(result["evidence_class"], "synthetic_contract_only")
        self.assertFalse(result["capture_authenticated"])
        self.assertEqual(result["state_comparison_boundary"], "absolute_committed_position_interval_end")
        self.assertIn("cannot authenticate capture", result["warning"])

    def test_synthetic_fixture_cannot_compare_equal_to_unverified_capture(self):
        unverified = deepcopy(self.candidate)
        unverified["evidence_class"] = "native_capture_unverified"
        unverified["provenance"]["synthetic"] = False
        result = parity.compare(self.serial, unverified)
        self.assertFalse(result["equal"])
        self.assertIn("evidence_class differs", result["first_divergence"])
        self.assertFalse(result["runtime_parity_claim"])

    def test_command_digest_mismatch_is_rejected(self):
        changed = deepcopy(self.candidate)
        changed["provenance"]["command_sha256"] = "f" * 64
        self.assertIn("provenance.command_sha256 differs",
                      parity.compare(self.serial, changed)["first_divergence"])

    def test_absolute_positions_and_committed_ids_are_exact(self):
        changed = deepcopy(self.candidate)
        commit = changed["requests"][0]["commits"][1]
        commit["committed_tokens"][0]["token_id"] += 1
        commit["ple_previous_token_ids"] = [204, 204]
        ple_component = next(c for c in commit["components"] if c["kind"] == "ple_previous_token_ids")
        ple_component["format_metadata"]["token_ids"] = [204, 204]
        self.assertIn("committed_tokens differs", parity.compare(self.serial, changed)["first_divergence"])

        changed = deepcopy(self.candidate)
        changed["requests"][0]["commits"][1]["position_start"] += 1
        self.assertIn("contiguous", parity.compare(self.serial, changed)["first_divergence"])

    def test_initial_prompt_cache_state_and_input_token_count_are_compared(self):
        changed = deepcopy(self.candidate)
        changed["requests"][0]["initial_checkpoint"]["components"][0]["sha256"] = "f" * 64
        self.assertIn("initial_checkpoint differs", parity.compare(self.serial, changed)["first_divergence"])

        changed = deepcopy(self.candidate)
        changed["requests"][0]["input_token_count"] += 1
        self.assertIn("cache reused+fresh", parity.compare(self.serial, changed)["first_divergence"])

    def test_native_ids_mtp_and_state_digests_are_compared_at_each_boundary(self):
        for field, component_kind in (("native_token_ids", None), ("mtp_accepted_token_ids", None), (None, "qsa_kv_key@1")):
            with self.subTest(field=field, component_kind=component_kind):
                changed = deepcopy(self.candidate)
                left = self.serial
                commit = changed["requests"][0]["commits"][0]
                if field:
                    if field == "mtp_accepted_token_ids":
                        left = deepcopy(self.serial)
                        left_commit = left["requests"][0]["commits"][0]
                        for trace_commit in (left_commit, commit):
                            trace_commit["mtp_offered_token_ids"].append(801)
                        commit[field].append(801)
                    else:
                        commit[field][0] += 5
                    expected = field + " differs"
                else:
                    entry = next(c for c in commit["components"] if c["component_id"] == component_kind)
                    entry["sha256"] = "f" * 64
                    expected = "components differs"
                self.assertIn(expected, parity.compare(left, changed)["first_divergence"])

    def test_complete_architecture_derived_inventory_fails_closed(self):
        for mutate in ("remove_component", "remove_expected_inventory", "wrong_shape", "wrong_byte_length"):
            with self.subTest(mutate=mutate):
                left, right = deepcopy(self.serial), deepcopy(self.candidate)
                for trace in (left, right):
                    commit = trace["requests"][0]["commits"][0]
                    if mutate == "remove_component":
                        commit["components"].pop()
                    elif mutate == "remove_expected_inventory":
                        commit["expected_component_inventory"].pop()
                    elif mutate == "wrong_shape":
                        commit["components"][0]["shape"][0] += 1
                    else:
                        commit["components"][0]["byte_length"] += 4
                self.assertFalse(parity.compare(left, right)["equal"])

    def test_qsa_and_mtp_format_metadata_and_ring_mapping_are_required(self):
        changed = deepcopy(self.candidate)
        changed["requests"][0]["commits"][0]["state_formats"]["qsa_layer_1"]["idx_block_pos_value"] = 999
        self.assertIn("format_metadata", parity.compare(self.serial, changed)["first_divergence"])

        changed = deepcopy(self.candidate)
        changed["requests"][0]["commits"][0]["state_formats"]["mtp"]["ring_slots_by_logical_position"] = [0, 0]
        self.assertIn("duplicate or out-of-range", parity.compare(self.serial, changed)["first_divergence"])

        changed = deepcopy(self.candidate)
        changed["requests"][0]["commits"][0]["state_formats"]["qsa_layer_1"]["kv_mode"] = "ring"
        result = parity.compare(self.serial, changed)
        self.assertIn("kv_mode", result["first_divergence"])

    def test_qsa_and_mtp_format_objects_have_exact_mode_specific_fields(self):
        changed = deepcopy(self.candidate)
        qsa_commit = changed["requests"][0]["commits"][0]
        qsa_commit["state_formats"]["qsa_layer_1"]["ring_slots_by_logical_position"] = []
        arch, _ = parity._architecture(changed, "candidate")
        with self.assertRaisesRegex(parity.TraceError, "format fields must be exactly"):
            parity._validate_state_formats(qsa_commit, arch, "candidate")
        self.assertIn("schema", parity.compare(self.serial, changed)["first_divergence"])

        changed = deepcopy(self.candidate)
        mtp_commit = changed["requests"][0]["commits"][0]
        mtp_commit["state_formats"]["mtp"]["idx_block_pos_value"] = 1
        arch, _ = parity._architecture(changed, "candidate")
        with self.assertRaisesRegex(parity.TraceError, "format fields must be exactly"):
            parity._validate_state_formats(mtp_commit, arch, "candidate")
        self.assertIn("schema", parity.compare(self.serial, changed)["first_divergence"])

        # A semantically valid format difference must be compared as state, not
        # silently ignored after each trace validates independently.
        changed = deepcopy(self.candidate)
        commit = changed["requests"][0]["commits"][0]
        commit["state_formats"]["qsa_layer_1"]["kv_mode"] = "streamed"
        for component in commit["components"]:
            if component["component_id"] in {"qsa_kv_key@1", "qsa_kv_value@1"}:
                component["format_metadata"]["kv_mode"] = "streamed"
        parity._index_trace(changed, "candidate")
        self.assertIn("state_formats differs", parity.compare(self.serial, changed)["first_divergence"])

    def test_accepted_mtp_ids_must_be_offered_prefix(self):
        changed = deepcopy(self.candidate)
        commit = changed["requests"][0]["commits"][0]
        commit["mtp_accepted_token_ids"] = [999]
        self.assertIn("exact prefix", parity.compare(self.serial, changed)["first_divergence"])

    def test_ple_previous_ids_match_prompt_tail_then_committed_history(self):
        changed = deepcopy(self.candidate)
        changed["requests"][0]["input_token_tail_ids"] = [198, 200]
        self.assertIn("initial PLE predecessor IDs", parity.compare(self.serial, changed)["first_divergence"])

        changed = deepcopy(self.candidate)
        commit = changed["requests"][0]["commits"][1]
        commit["ple_previous_token_ids"] = [203, 999]
        previous_component = next(c for c in commit["components"] if c["kind"] == "ple_previous_token_ids")
        previous_component["format_metadata"]["token_ids"] = [203, 999]
        self.assertIn("do not match prompt plus committed-token history",
                      parity.compare(self.serial, changed)["first_divergence"])

    def test_quantized_kv_byte_lengths_have_cpu_contract_coverage(self):
        for kv_format in ("int8", "q4_0", "hybrid_k8v4"):
            with self.subTest(kv_format=kv_format):
                architecture = fixtures.tiny_architecture()
                architecture["qsa_geometry"]["head_dim"] = 64
                architecture["mtp_geometry"]["head_dim"] = 64
                serial = fixtures.make_trace("serial_off", architecture, kv_format)
                candidate = fixtures.make_trace("abcd_on", architecture, kv_format)
                result = parity.compare(serial, candidate)
                self.assertTrue(result["equal"], result)

    def test_quantized_payload_segments_have_independent_literal_offsets(self):
        architecture = fixtures.tiny_architecture()
        architecture["qsa_geometry"]["head_dim"] = 64
        architecture["mtp_geometry"]["head_dim"] = 64

        def component(kv_format, kind):
            boundary = {"position_end_exclusive": 2,
                        "state_formats": fixtures._state_formats(architecture, 2, kv_format=kv_format)}
            return parity._expected_component(kind, 1, boundary, architecture, "literal serialization test")

        int8_key = component("int8", "qsa_kv_key")
        self.assertEqual(int8_key["byte_length"], 132)
        self.assertEqual(int8_key["format_metadata"]["payload_segments"], [
            {"name": "codes_int8", "offset_bytes": 0, "byte_length": 128,
             "logical_order": "logical_position,kv_head,head_dim"},
            {"name": "scales_fp16_le", "offset_bytes": 128, "byte_length": 4,
             "logical_order": "logical_position,kv_head,scale_group_of_64"},
        ])

        q4_value = component("q4_0", "qsa_kv_value")
        self.assertEqual(q4_value["byte_length"], 72)
        self.assertEqual(q4_value["format_metadata"]["payload_segments"], [{
            "name": "q4_0_blocks", "offset_bytes": 0, "byte_length": 72,
            "logical_order": "logical_position,kv_head,head_dim_block",
            "block_layout": "18 bytes: fp16_scale_le then 16 packed code bytes; element j is low nibble and element j+16 is high nibble",
        }])

        k8v4_key = component("hybrid_k8v4", "qsa_kv_key")
        k8v4_value = component("hybrid_k8v4", "qsa_kv_value")
        self.assertEqual((k8v4_key["byte_length"], k8v4_value["byte_length"]), (132, 72))
        self.assertEqual(k8v4_key["format_metadata"]["payload_segments"][1]["offset_bytes"], 128)
        self.assertEqual(k8v4_value["format_metadata"]["payload_segments"][0]["offset_bytes"], 0)

    def test_loader_rejects_nonregular_and_oversized_files_without_unbounded_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fifo = root / "trace.fifo"
            os.mkfifo(fifo)
            with self.assertRaisesRegex(parity.TraceError, "regular file"):
                parity.load(fifo)

            oversized = root / "oversized.json"
            with oversized.open("wb") as stream:
                stream.truncate(parity.MAX_TRACE_BYTES + 1)
            with self.assertRaisesRegex(parity.TraceError, "byte limit"):
                parity.load(oversized)

    def test_current_qwen_geometry_is_only_a_synthetic_inventory_example(self):
        result = parity._index_trace(self.current_inventory, "fixture")[0]
        commit = result["requests"]["synthetic-r-01"]["commits"][0]
        counts = commit["expected_component_counts"]
        self.assertEqual(self.current_inventory["evidence_class"], "synthetic_contract_only")
        self.assertIn("synthetic inventory example", result["architecture"]["model_family"])
        self.assertEqual((len(result["architecture"]["gdn_layers"]), len(result["architecture"]["qsa_layers"])), (36, 12))
        self.assertEqual(counts["gdn_recurrence"], 36)
        self.assertEqual(counts["qsa_idx_pooled"], 12)
        self.assertEqual(len(commit["components"]), 149)
        self.assertFalse(self.current_inventory["runtime_parity_claim"])

    def test_capture_boundary_requires_commit_and_sync_declarations(self):
        changed = deepcopy(self.candidate)
        changed["requests"][0]["commits"][0]["capture_point"]["mutating_streams_synchronized"] = False
        self.assertFalse(parity.compare(self.serial, changed)["equal"])

        changed = deepcopy(self.candidate)
        changed["requests"][0]["commits"][0]["capture_point"]["mtp_draft_stream_synchronized"] = False
        self.assertIn("mtp_draft_stream_synchronized", parity.compare(self.serial, changed)["first_divergence"])

    def test_v2_is_not_silently_migrated(self):
        legacy = {"contract_version": 2, "trace_kind": "native_transaction_trace_v2"}
        result = parity.compare(legacy, legacy)
        self.assertFalse(result["equal"])
        self.assertFalse(result["runtime_parity_claim"])

    def test_aggregate_trace_caps_reject_before_deep_validation(self):
        too_many_commits = deepcopy(self.candidate)
        commit = too_many_commits["requests"][0]["commits"][0]
        too_many_commits["requests"][0]["commits"] = [commit] * (parity.MAX_TOTAL_COMMITS + 1)
        result = parity.compare(self.serial, too_many_commits)
        self.assertEqual(result["first_divergence"],
                         f"candidate: total commit count exceeds {parity.MAX_TOTAL_COMMITS}")

        too_many_components = deepcopy(self.candidate)
        too_many_components["requests"][0]["initial_checkpoint"]["components"] = [None] * (parity.MAX_TOTAL_COMPONENTS + 1)
        result = parity.compare(self.serial, too_many_components)
        self.assertEqual(result["first_divergence"],
                         f"candidate: total component count exceeds {parity.MAX_TOTAL_COMPONENTS}")


if __name__ == "__main__":
    unittest.main()
