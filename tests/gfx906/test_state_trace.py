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

    def test_synthetic_matching_pair_is_contract_only(self):
        result = state_trace.compare(self.serial, self.candidate)
        self.assertTrue(result["equal"], result)
        self.assertFalse(result["runtime_parity_claim"])

    def test_incomplete_stage_coverage_fails_closed(self):
        changed = deepcopy(self.candidate)
        changed["checkpoints"].pop(1)
        result = state_trace.compare(self.serial, changed)
        self.assertFalse(result["equal"])
        self.assertIn("stage_index", result["first_divergence"])

    def test_missing_component_and_component_metadata_fail_closed(self):
        changed = deepcopy(self.candidate)
        changed["checkpoints"][0]["components"] = [c for c in changed["checkpoints"][0]["components"] if c["component_id"] != "qsa_indexer_idx_block_pos"]
        result = state_trace.compare(self.serial, changed)
        self.assertIn("missing required components", result["first_divergence"])
        changed = deepcopy(self.candidate)
        del changed["checkpoints"][0]["components"][0]["dtype"]
        result = state_trace.compare(self.serial, changed)
        self.assertIn("missing component metadata dtype", result["first_divergence"])

    def test_component_identity_and_digest_are_compared(self):
        changed = deepcopy(self.candidate)
        changed["checkpoints"][1]["components"][1]["sha256"] = "f" * 64
        result = state_trace.compare(self.serial, changed)
        self.assertEqual(result["first_divergence"], "checkpoint 1 qsa_indexer_idx_block_pos: sha256 differs")

    def test_v2_transaction_comparator_remains_independent(self):
        old_spec = importlib.util.spec_from_file_location("abcd_parity", ROOT / "tests/gfx906/abcd_parity.py")
        old_module = importlib.util.module_from_spec(old_spec)
        old_spec.loader.exec_module(old_module)
        left = json.loads((FIXTURES / "abcd-parity-serial-synthetic.json").read_text())
        right = json.loads((FIXTURES / "abcd-parity-on-synthetic.json").read_text())
        self.assertTrue(old_module.compare(left, right)["equal"])


if __name__ == "__main__":
    unittest.main()
