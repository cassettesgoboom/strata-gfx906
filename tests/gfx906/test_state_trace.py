import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("gfx906_state_trace", ROOT / "tools/gfx906_state_trace.py")
state_trace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(state_trace)
FIXTURES = ROOT / "benchmarks/gfx906/fixtures"


class StateTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serial = json.loads((FIXTURES / "native-state-trace-serial-synthetic.json").read_text())
        cls.candidate = json.loads((FIXTURES / "native-state-trace-abcd-synthetic.json").read_text())

    def test_synthetic_matching_pair_is_diagnostic_only(self):
        result = state_trace.compare(self.serial, self.candidate)
        self.assertTrue(result["diagnostic_records_equal"], result)
        self.assertEqual(result["comparison_scope"], "supplied_declared_checkpoints_only")
        self.assertFalse(result["runtime_parity_claim"])
        self.assertIn("cannot prove", result["warning"])

    def test_mutually_truncated_plans_are_only_declared_checkpoint_equality(self):
        left, right = deepcopy(self.serial), deepcopy(self.candidate)
        for trace in (left, right):
            trace["stage_plan"].pop()
            trace["checkpoints"].pop()
        result = state_trace.compare(left, right)
        self.assertTrue(result["diagnostic_records_equal"], result)
        self.assertEqual(result["comparison_scope"], "supplied_declared_checkpoints_only")
        self.assertIn("cannot prove", result["warning"])
        self.assertFalse(result["runtime_parity_claim"])

    def test_incomplete_stage_coverage_fails_closed(self):
        changed = deepcopy(self.candidate)
        changed["checkpoints"].pop(1)
        result = state_trace.compare(self.serial, changed)
        self.assertFalse(result["diagnostic_records_equal"])
        self.assertIn("checkpoint stage coverage", result["first_divergence"])

    def test_omitted_layer_from_declared_inventory_fails_closed(self):
        changed = deepcopy(self.candidate)
        changed["layer_ranges"][0]["count"] = 1
        result = state_trace.compare(self.serial, changed)
        self.assertFalse(result["diagnostic_records_equal"])
        self.assertIn("owned component ordinals", result["first_divergence"])

    def test_missing_and_unknown_component_ordinals_fail_closed(self):
        changed = deepcopy(self.candidate)
        changed["checkpoints"][0]["components"].pop(1)
        result = state_trace.compare(self.serial, changed)
        self.assertIn("component ordinals differ", result["first_divergence"])
        changed = deepcopy(self.candidate)
        extra = deepcopy(changed["checkpoints"][0]["components"][0])
        extra["ordinal"] = 99
        changed["checkpoints"][0]["components"].append(extra)
        result = state_trace.compare(self.serial, changed)
        self.assertIn("unknown component ordinal", result["first_divergence"])

    def test_every_component_ordinal_hash_is_compared(self):
        changed = deepcopy(self.candidate)
        qsa = next(c for c in changed["checkpoints"][1]["components"]
                   if c["component_id"] == "qsa_indexer_idx_block_pos" and c["ordinal"] == 1)
        qsa["sha256"] = "f" * 64
        result = state_trace.compare(self.serial, changed)
        self.assertEqual(result["first_divergence"], "checkpoint 1 ('qsa_indexer_idx_block_pos', 1): sha256 differs")

    def test_wrong_request_window_or_committed_tokens_rejected(self):
        for key, value in (("request_id", "other"), ("commit_window_index", 1),
                           ("committed_token_ids", [900, 999])):
            with self.subTest(key=key):
                changed = deepcopy(self.candidate)
                changed["window_identity"][key] = value
                self.assertEqual(state_trace.compare(self.serial, changed)["first_divergence"], "window_identity differs")

    def test_trace_capture_method_must_match(self):
        changed = deepcopy(self.candidate)
        changed["provenance"]["trace_capture_method"] = "different supplied method"
        self.assertEqual(state_trace.compare(self.serial, changed)["first_divergence"], "provenance.trace_capture_method differs")

    def test_malformed_membership_fields_fail_closed_without_exceptions(self):
        for field, value in (("evidence_class", []), ("mode", {})):
            with self.subTest(field=field):
                changed = deepcopy(self.candidate)
                changed[field] = value
                self.assertFalse(state_trace.compare(self.serial, changed)["diagnostic_records_equal"])
        for container, field, value in (("range", "component_id", []), ("range", "byte_order", []),
                                        ("checkpoint", "component_id", {})):
            with self.subTest(container=container, field=field):
                changed = deepcopy(self.candidate)
                if container == "range":
                    changed["layer_ranges"][0][field] = value
                else:
                    changed["checkpoints"][0]["components"][0][field] = value
                self.assertFalse(state_trace.compare(self.serial, changed)["diagnostic_records_equal"])

    def test_component_order_and_metadata_are_checked(self):
        changed = deepcopy(self.candidate)
        changed["checkpoints"][0]["components"].reverse()
        self.assertIn("component order", state_trace.compare(self.serial, changed)["first_divergence"])
        changed = deepcopy(self.candidate)
        del changed["checkpoints"][0]["components"][0]["dtype"]
        self.assertIn("missing metadata dtype", state_trace.compare(self.serial, changed)["first_divergence"])

    def test_v2_transaction_comparator_remains_independent(self):
        old_spec = importlib.util.spec_from_file_location("abcd_parity", ROOT / "tests/gfx906/abcd_parity.py")
        old_module = importlib.util.module_from_spec(old_spec)
        old_spec.loader.exec_module(old_module)
        left = json.loads((FIXTURES / "abcd-parity-serial-synthetic.json").read_text())
        right = json.loads((FIXTURES / "abcd-parity-on-synthetic.json").read_text())
        self.assertTrue(old_module.compare(left, right)["equal"])


if __name__ == "__main__":
    unittest.main()
