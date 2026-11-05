"""The library's rules, as plain functions.

Nothing here knows about Flask, SQLite or email, so every rule can be
tested by calling a function. A loan is anything that supports
loan["due_date"], loan["returned"], loan["fine"] and loan["fine_paid"]
(a dict or a sqlite3.Row both work).
"""
from datetime import date, timedelta

FINE_PER_DAY = 0.50
LOAN_DAYS = 14
RENEWAL_DAYS = 14
MAX_RENEWALS = 1
LOAN_LIMITS = {"student": 3, "staff": 5}
MEMBER_TYPES = tuple(LOAN_LIMITS)
DEFAULT_MEMBER_TYPE = "student"


def money(amount):
    return round(float(amount), 2)


def _today(today):
    return today or date.today()


# ---------- fines ----------


def days_late(due_date, today=None):
    """Days past the due date. Zero or negative means not late."""
    return (_today(today) - date.fromisoformat(due_date)).days


def late_fine(due_date, today=None):
    """The fine for a book with this due date, if it came back today."""
    return max(0, days_late(due_date, today)) * FINE_PER_DAY


def current_fine(loan, today=None):
    """The fine a loan carries right now: fixed once returned, still growing if not."""
    if loan["returned"]:
        return loan["fine"]
    return late_fine(loan["due_date"], today)


def amount_owed(loans, today=None):
    """Unpaid fines on returned books plus fines still building on open loans."""
    total = 0
    for loan in loans:
        if not loan["returned"]:
            total += late_fine(loan["due_date"], today)
        elif not loan["fine_paid"]:
            total += loan["fine"]
    return total


def is_overdue(loan, today=None):
    return not loan["returned"] and days_late(loan["due_date"], today) > 0


# ---------- borrowing ----------


def loan_limit(member_type):
    return LOAN_LIMITS.get(member_type, LOAN_LIMITS[DEFAULT_MEMBER_TYPE])


def open_loan_count(loans):
    return sum(1 for loan in loans if not loan["returned"])


def loans_remaining(member_type, loans):
    return loan_limit(member_type) - open_loan_count(loans)


def checkout_problem(member_type, loans, today=None):
    """Why this member can't borrow another book, or None if they can."""
    if amount_owed(loans, today) > 0:
        return "member has unpaid fines"
    if open_loan_count(loans) >= loan_limit(member_type):
        return "loan limit reached"
    return None


def default_due_date(today=None):
    return (_today(today) + timedelta(days=LOAN_DAYS)).isoformat()


# ---------- renewing ----------


def renewal_problem(loan, today=None):
    """Why this loan can't be renewed, or None if it can."""
    if loan["returned"]:
        return "loan already returned"
    if date.fromisoformat(loan["due_date"]) < _today(today):
        return "overdue loans cannot be renewed"
    if loan["renewals"] >= MAX_RENEWALS:
        return "loan was already renewed"
    return None


def renewed_due_date(due_date):
    return (date.fromisoformat(due_date) + timedelta(days=RENEWAL_DAYS)).isoformat()
