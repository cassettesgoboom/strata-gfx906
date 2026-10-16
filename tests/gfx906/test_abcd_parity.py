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
        self.assertTrue(result["synthetic_contract_only"])
        self.assertFalse(result["runtime_parity_claim"])
        self.assertIn("authenticity", result["warning"])
        self.assertEqual(result["state_comparison_boundary"], "commit_window_end")
        self.assertFalse(result["occupancy"]["compared_for_parity"])
        self.assertNotEqual(result["occupancy"]["serial"], result["occupancy"]["abcd"])

    def test_multi_token_window_matches_and_first_list_divergence_is_reported(self):
        self.assertEqual(self.serial["requests"][0]["commits"][0]["native_token_ids"], [900, 901])
        self.assertEqual(abcd_parity.compare(self.serial, self.abcd)["equal"], True)
        changed = deepcopy(self.abcd)
        changed["requests"][0]["commits"][0]["native_token_ids"] = [900, 999]
        result = abcd_parity.compare(self.serial, changed)
        self.assertEqual(result["first_divergence"], "request r-01 commit 0: native_token_ids differs")

    def test_window_end_state_is_not_claimed_per_emitted_token(self):
        result = abcd_parity.compare(self.serial, self.abcd)
        commit = self.abcd["requests"][0]["commits"][0]
        self.assertGreater(len(commit["native_token_ids"]), 1)
        self.assertEqual(result["state_comparison_boundary"], "commit_window_end")
        self.assertIn("gdn_state_sha256", commit)
        self.assertNotIn("per_token_state_sha256", commit)

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

    def test_cache_fields_are_required_even_when_missing_from_both_runs(self):
        serial = deepcopy(self.serial)
        abcd = deepcopy(self.abcd)
        for run in (serial, abcd):
            for field in ("cache_key_sha256", "cache_reused_tokens", "cache_fresh_tokens"):
                del run["requests"][0][field]
        self.assertIn("cache_key_sha256", abcd_parity.compare(serial, abcd)["first_divergence"])

    def test_sha256_placeholders_and_malformed_provenance_fail_closed(self):
        for location, field in (("request", "cache_key_sha256"), ("commit", "gdn_state_sha256"),
                                ("provenance", "binary_sha256"), ("provenance", "command_sha256")):
            with self.subTest(location=location, field=field):
                changed = deepcopy(self.abcd)
                if location == "request":
                    changed["requests"][0][field] = "not-a-hash"
                elif location == "commit":
                    changed["requests"][0]["commits"][0][field] = "placeholder"
                else:
                    changed["provenance"][field] = "placeholder"
                self.assertIn("SHA-256", abcd_parity.compare(self.serial, changed)["first_divergence"])

    def test_command_hash_and_input_sampler_identity_must_match(self):
        changed = deepcopy(self.abcd)
        changed["provenance"]["command_sha256"] = "7" * 64
        self.assertEqual(abcd_parity.compare(self.serial, changed)["first_divergence"], "provenance.command_sha256 differs")
        for field in ("input_token_ids_sha256", "sampler_state_sha256"):
            changed = deepcopy(self.abcd)
            changed["requests"][0][field] = "7" * 64
            self.assertIn(field + " differs", abcd_parity.compare(self.serial, changed)["first_divergence"])

    def test_request_order_must_match(self):
        serial = deepcopy(self.serial)
        abcd = deepcopy(self.abcd)
        for run in (serial, abcd):
            second = deepcopy(run["requests"][0])
            second["request_id"] = "r-02"
            run["requests"].append(second)
        abcd["requests"].reverse()
        self.assertEqual(abcd_parity.compare(serial, abcd)["first_divergence"], "request_ids differ")

    def test_commit_indices_must_be_ordered_zero_based_and_contiguous(self):
        for indices in ((9, 10), (-1, 0), (0, 2), (1, 0)):
            with self.subTest(indices=indices):
                changed = deepcopy(self.abcd)
                for step, index in zip(changed["requests"][0]["commits"], indices):
                    step["commit_index"] = index
                reason = abcd_parity.compare(self.serial, changed)["first_divergence"]
                self.assertTrue("commit_index" in reason or "ordered, zero-based, and contiguous" in reason)

    def test_token_fields_reject_wrong_types_and_booleans(self):
        mutations = (
            ("native_token_ids", [True]),
            ("native_token_ids", ["900"]),
            ("native_token_ids", []),
            ("native_token_ids", [-1]),
            ("mtp_offered_token_ids", [True]),
            ("mtp_accepted_token_ids", "[900]"),
        )
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                changed = deepcopy(self.abcd)
                changed["requests"][0]["commits"][0][field] = value
                self.assertFalse(abcd_parity.compare(self.serial, changed)["equal"])

    def test_singular_v1_token_field_is_rejected(self):
        changed = deepcopy(self.abcd)
        step = changed["requests"][0]["commits"][0]
        step["native_token_id"] = step.pop("native_token_ids")[0]
        result = abcd_parity.compare(self.serial, changed)
        self.assertIn("missing native_token_ids", result["first_divergence"])

    def test_missing_synthetic_markers_never_enable_runtime_claim(self):
        serial = deepcopy(self.serial)
        abcd = deepcopy(self.abcd)
        del serial["provenance"]["synthetic"]
        del abcd["provenance"]["synthetic"]
        result = abcd_parity.compare(serial, abcd)
        self.assertTrue(result["equal"], result)
        self.assertFalse(result["synthetic_contract_only"])
        self.assertFalse(result["runtime_parity_claim"])
        self.assertIn("full correctness require independent evidence", result["warning"])


if __name__ == "__main__":
    unittest.main()
