"""Unit tests for the library rules. No Flask, no database, no files."""
import unittest
from datetime import date

import policy

TODAY = date(2026, 11, 5)


def loan(due_date, returned=False, fine=0.0, fine_paid=False, renewals=0):
    return {"due_date": due_date, "returned": returned, "fine": fine, "fine_paid": fine_paid, "renewals": renewals}


class FineTests(unittest.TestCase):
    def test_no_fine_when_on_time_or_early(self):
        self.assertEqual(policy.late_fine("2026-11-05", TODAY), 0)
        self.assertEqual(policy.late_fine("2026-11-20", TODAY), 0)

    def test_fifty_cents_per_day_late(self):
        self.assertEqual(policy.late_fine("2026-11-01", TODAY), 2.0)

    def test_current_fine_is_fixed_once_returned(self):
        self.assertEqual(policy.current_fine(loan("2026-10-01", returned=True, fine=1.5), TODAY), 1.5)

    def test_amount_owed_counts_open_late_loans_and_unpaid_fines(self):
        loans = [
            loan("2026-10-31"),  # open, 5 days late: 2.5
            loan("2026-10-01", returned=True, fine=1.0),  # unpaid: 1.0
            loan("2026-10-01", returned=True, fine=3.0, fine_paid=True),  # paid: 0
            loan("2026-11-30"),  # open, not due: 0
        ]
        self.assertEqual(policy.amount_owed(loans, TODAY), 3.5)


class BorrowingTests(unittest.TestCase):
    def test_limits_by_member_type(self):
        self.assertEqual(policy.loan_limit("student"), 3)
        self.assertEqual(policy.loan_limit("staff"), 5)

    def test_member_who_owes_cannot_borrow(self):
        self.assertEqual(policy.checkout_problem("staff", [loan("2026-11-01")], TODAY), "member has unpaid fines")

    def test_student_at_limit_cannot_borrow(self):
        loans = [loan("2026-11-20")] * 3
        self.assertEqual(policy.checkout_problem("student", loans, TODAY), "loan limit reached")
        self.assertIsNone(policy.checkout_problem("staff", loans, TODAY))


class RenewalTests(unittest.TestCase):
    def test_renewal_adds_fourteen_days(self):
        self.assertEqual(policy.renewed_due_date("2026-11-19"), "2026-12-03")

    def test_renewal_rules(self):
        self.assertIsNone(policy.renewal_problem(loan("2026-11-05"), TODAY))
        self.assertEqual(policy.renewal_problem(loan("2026-11-04"), TODAY), "overdue loans cannot be renewed")
        self.assertEqual(policy.renewal_problem(loan("2026-11-20", renewals=1), TODAY), "loan was already renewed")
        self.assertEqual(policy.renewal_problem(loan("2026-11-20", returned=True), TODAY), "loan already returned")


if __name__ == "__main__":
    unittest.main()
