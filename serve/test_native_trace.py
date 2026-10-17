"""CPU-only protocol contract for opt-in native request correlation."""
import os
import unittest
from unittest import mock

from serve import native_trace


class NativeTraceProtocol(unittest.TestCase):
    def test_opt_in_field_is_opaque_and_validated(self):
        rid = "a" * 32
        with mock.patch.dict(os.environ, {native_trace.TRACE_ENV: "1"}):
            self.assertTrue(native_trace.enabled())
            self.assertEqual(native_trace.field(rid), f"trace_id={rid}")
            for invalid in (None, "", "x" * 32, "a" * 31, "A" * 32):
                with self.assertRaises(ValueError):
                    native_trace.field(invalid)

    def test_legacy_mode_adds_no_field(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertFalse(native_trace.enabled())

    def test_concurrent_distinct_ids_complete_without_prompt_data(self):
        ledger = native_trace.ActiveRequests()
        left, right = "1" * 32, "2" * 32
        ledger.begin(left, 0)
        ledger.begin(right, 1)
        msg = ledger.complete(right, 1, "stop", 4)
        self.assertIn(f"request={right}", msg)
        self.assertNotIn(left, msg)
        self.assertNotIn("prompt", msg)
        self.assertNotIn("secret prompt text", msg)
        self.assertIn("state=complete", msg)
        self.assertIn("produced=4", msg)
        self.assertIn(left, ledger.complete(left, 0, "length", 8))

    def test_duplicate_active_and_missing_completion_are_rejected(self):
        ledger = native_trace.ActiveRequests()
        rid = "f" * 32
        with self.assertRaises(ValueError):
            ledger.complete(rid, 0, "stop", 1)
        ledger.begin(rid, 0)
        with self.assertRaises(ValueError):
            ledger.begin(rid, 1)
        with self.assertRaises(ValueError):
            ledger.complete("e" * 32, 0, "stop", 1)
        with self.assertRaises(ValueError):
            ledger.complete(rid, 1, "stop", 1)
        ledger.complete(rid, 0, "stop", 1)
        with self.assertRaises(ValueError):
            ledger.complete(rid, 0, "stop", 1)


if __name__ == "__main__":
    unittest.main()
