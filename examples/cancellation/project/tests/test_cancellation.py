"""Acceptance tests derived from CANCEL-01 through CANCEL-06."""
import importlib.util
import os
from pathlib import Path
import sys
import unittest

SOURCE = Path(os.environ.get("CANCELLATION_MODULE", Path(__file__).resolve().parents[1] / "cancellation.py"))
spec = importlib.util.spec_from_file_location("cancellation_fixture", SOURCE)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
Order, Cancellation, cancel_order = module.Order, module.Cancellation, module.cancel_order


class CancellationAcceptanceTests(unittest.TestCase):
    def test_cancel_day_zero_full_refund(self):
        # CANCEL-01, CANCEL-02
        self.assertEqual(cancel_order(Order("pending", 0, 12345)), Cancellation("cancelled", 12345, None))

    def test_cancel_day_seven_full_refund(self):
        # CANCEL-01 inclusive boundary, CANCEL-02
        self.assertEqual(cancel_order(Order("pending", 7, 12345)), Cancellation("cancelled", 12345, None))

    def test_day_eight_is_expired(self):
        # CANCEL-03
        self.assertEqual(cancel_order(Order("pending", 8, 12345)), Cancellation("rejected", 0, "window_expired"))

    def test_shipped_is_rejected_without_refund(self):
        # CANCEL-04
        self.assertEqual(cancel_order(Order("shipped", 2, 12345)), Cancellation("rejected", 0, "not_pending"))

    def test_cancelled_has_no_additional_refund(self):
        # CANCEL-05
        self.assertEqual(cancel_order(Order("cancelled", 2, 12345)), Cancellation("cancelled", 0, None))

    def test_cancelled_after_window_is_still_idempotent(self):
        # CANCEL-05 listed edge case
        self.assertEqual(cancel_order(Order("cancelled", 30, 12345)), Cancellation("cancelled", 0, None))

    def test_invalid_age_is_rejected(self):
        # CANCEL-06, including booleans
        for age in [-1, True, 1.5, "1"]:
            with self.subTest(age=age):
                with self.assertRaisesRegex(ValueError, "^invalid_order$"):
                    cancel_order(Order("pending", age, 12345))

    def test_invalid_total_is_rejected(self):
        # CANCEL-06
        for total in [0, -1, True, 1.5, "1"]:
            with self.subTest(total=total):
                with self.assertRaisesRegex(ValueError, "^invalid_order$"):
                    cancel_order(Order("pending", 1, total))

    def test_unknown_state_is_rejected(self):
        # CANCEL-06
        for status in ["unknown", 4, None, []]:
            with self.subTest(status=status):
                with self.assertRaisesRegex(ValueError, "^invalid_order$"):
                    cancel_order(Order(status, 1, 12345))


if __name__ == "__main__":
    unittest.main()
