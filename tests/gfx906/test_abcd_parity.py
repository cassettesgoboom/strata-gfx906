import importlib.util
import json
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("abcd_parity", Path(__file__).with_name("abcd_parity.py"))
abcd_parity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(abcd_parity)
FIXTURES = ROOT / "benchmarks/gfx906/fixtures"


class AbcdParityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.serial = json.loads((FIXTURES / "abcd-parity-serial-synthetic.json").read_text())
        cls.abcd = json.loads((FIXTURES / "abcd-parity-on-synthetic.json").read_text())

    def test_matching_fixture_passes_and_occupancy_is_not_parity(self):
        result = abcd_parity.compare(self.serial, self.abcd)
        self.assertTrue(result["equal"], result)
        self.assertFalse(result["occupancy"]["compared_for_parity"])
        self.assertNotEqual(result["occupancy"]["serial"], result["occupancy"]["abcd"])

    def test_first_token_divergence_is_reported(self):
        changed = deepcopy(self.abcd)
        changed["requests"][0]["commits"][1]["native_token_id"] += 1
        result = abcd_parity.compare(self.serial, changed)
        self.assertEqual(result["first_divergence"], "request r-01 commit 1: native_token_id differs")

    def test_mtp_decisions_are_compared(self):
        changed = deepcopy(self.abcd)
        changed["requests"][0]["commits"][0]["mtp_accepted_token_ids"] = [901]
        result = abcd_parity.compare(self.serial, changed)
        self.assertIn("mtp_accepted_token_ids differs", result["first_divergence"])

    def test_cache_and_persistent_state_are_compared(self):
        for field, request in (("cache_reused_tokens", None), ("gdn_state_sha256", 0),
                               ("recurrent_state_sha256", 1)):
            with self.subTest(field=field):
                changed = deepcopy(self.abcd)
                if request is None:
                    changed["requests"][0][field] += 1
                else:
                    changed["requests"][0]["commits"][request][field] = "f" * 64
                self.assertIn(field + " differs", abcd_parity.compare(self.serial, changed)["first_divergence"])

    def test_request_identity_and_commit_boundaries_are_required(self):
        changed = deepcopy(self.abcd)
        changed["requests"][0]["request_id"] = "other"
        self.assertEqual(abcd_parity.compare(self.serial, changed)["first_divergence"], "request_ids differ")
        changed = deepcopy(self.abcd)
        del changed["requests"][0]["commits"][1]["recurrent_state_sha256"]
        self.assertIn("missing recurrent_state_sha256", abcd_parity.compare(self.serial, changed)["first_divergence"])


if __name__ == "__main__":
    unittest.main()
