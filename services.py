"""What the library does: each function is one operation a member or librarian asks for.

Services combine the rules (policy), storage (repository) and emails
(notifications). They report problems by raising the errors below, which
say what went wrong without saying which HTTP status to use.
"""
from datetime import date

import notifications
import policy
import repository
import validation
from db import session


class LibraryError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class InvalidInput(LibraryError):
    """The request is missing data or the data is in the wrong format."""


class NotFound(LibraryError):
    """The book, member or loan doesn't exist."""


class RuleBroken(LibraryError):
    """The request is well formed but a library rule forbids it."""


def _require(row, what):
    if row is None:
        raise NotFound(what + " not found")
    return row


# ---------- books ----------


def list_books(only_available=False):
    with session() as conn:
        return repository.all_books(conn, only_available)


def get_book(book_id):
    with session() as conn:
        return _require(repository.get_book(conn, book_id), "book")


def add_book(title, author, isbn):
    if not title or not author:
        raise InvalidInput("title and author are required")
    if not validation.is_isbn(isbn):
        raise InvalidInput("invalid isbn")
    with session() as conn:
        book_id = repository.add_book(conn, title, author, isbn)
        return repository.get_book(conn, book_id)


def delete_book(book_id):
    with session() as conn:
        book = _require(repository.get_book(conn, book_id), "book")
        if not book["available"]:
            raise RuleBroken("book is on loan")
        repository.delete_book(conn, book_id)


# ---------- members ----------


def list_members():
    with session() as conn:
        return repository.all_members(conn)


def get_member(member_id):
    with session() as conn:
        return _require(repository.get_member(conn, member_id), "member")


def add_member(name, email, member_type=policy.DEFAULT_MEMBER_TYPE):
    if not name:
        raise InvalidInput("name is required")
    if not validation.is_email(email):
        raise InvalidInput("invalid email")
    if not validation.is_member_type(member_type):
        raise InvalidInput("type must be " + " or ".join(policy.MEMBER_TYPES))
    with session() as conn:
        if repository.get_member_by_email(conn, email) is not None:
            raise RuleBroken("email already registered")
        member_id = repository.add_member(conn, name, email, member_type)
        return repository.get_member(conn, member_id)


def member_account(member_id):
    """A member's loans, what they owe and how many more books they can borrow."""
    with session() as conn:
        member = _require(repository.get_member(conn, member_id), "member")
        loans = repository.loans_for_member(conn, member_id)
    return {
        "loans": loans,
        "total_owed": policy.amount_owed(loans),
        "loans_remaining": policy.loans_remaining(member["type"], loans),
    }


# ---------- loans ----------


def list_loans(only_overdue=False):
    with session() as conn:
        loans = repository.all_loans(conn)
    if only_overdue:
        loans = [loan for loan in loans if policy.is_overdue(loan)]
    return loans


def get_loan(loan_id):
    with session() as conn:
        return _require(repository.get_loan(conn, loan_id), "loan")


def check_out(book_id, member_id, due_date=None):
    if not book_id or not member_id:
        raise InvalidInput("book_id and member_id are required")
    if due_date and not validation.is_iso_date(due_date):
        raise InvalidInput("invalid due_date")

    with session() as conn:
        book = _require(repository.get_book(conn, book_id), "book")
        member = _require(repository.get_member(conn, member_id), "member")
        if not book["available"]:
            raise RuleBroken("book is not available")
        problem = policy.checkout_problem(member["type"], repository.loans_for_member(conn, member_id))
        if problem:
            raise RuleBroken(problem)

        today = date.today()
        loan_id = repository.add_loan(
            conn, book_id, member_id, due_date or policy.default_due_date(today), today.isoformat()
        )
        repository.set_book_available(conn, book_id, False)
        loan = repository.get_loan(conn, loan_id)

    notifications.checkout_confirmation(member["email"], book["title"])
    return loan


def return_book(loan_id):
    with session() as conn:
        loan = _require(repository.get_loan(conn, loan_id), "loan")
        if loan["returned"]:
            raise RuleBroken("loan already returned")
        fine = policy.late_fine(loan["due_date"])
        repository.mark_returned(conn, loan_id, fine)
        repository.set_book_available(conn, loan["book_id"], True)
        member = repository.get_member(conn, loan["member_id"])
        book = repository.get_book(conn, loan["book_id"])
        updated = repository.get_loan(conn, loan_id)

    notifications.return_receipt(member["email"], book["title"], fine)
    return updated


def renew_loan(loan_id):
    with session() as conn:
        loan = _require(repository.get_loan(conn, loan_id), "loan")
        problem = policy.renewal_problem(loan)
        if problem:
            raise RuleBroken(problem)
        repository.extend_loan(conn, loan_id, policy.renewed_due_date(loan["due_date"]))
        member = repository.get_member(conn, loan["member_id"])
        book = repository.get_book(conn, loan["book_id"])
        updated = repository.get_loan(conn, loan_id)

    notifications.renewal_confirmation(member["email"], book["title"])
    return updated


def pay_fine(loan_id):
    with session() as conn:
        loan = _require(repository.get_loan(conn, loan_id), "loan")
        if not loan["returned"]:
            raise RuleBroken("return the book before paying")
        if loan["fine"] <= 0 or loan["fine_paid"]:
            raise RuleBroken("no fine to pay")
        repository.mark_fine_paid(conn, loan_id)
        member = repository.get_member(conn, loan["member_id"])
        updated = repository.get_loan(conn, loan_id)

    notifications.payment_receipt(member["email"], loan["fine"])
    return updated


# ---------- reports ----------


def overdue_report():
    with session() as conn:
        rows = repository.open_loans_with_details(conn)
    items = []
    for row in rows:
        late = policy.days_late(row["due_date"])
        if late > 0:
            items.append(
                {
                    "loan_id": row["loan_id"],
                    "title": row["title"],
                    "member": row["member"],
                    "days_late": late,
                    "fine": policy.late_fine(row["due_date"]),
                }
            )
    return {"items": items, "total_fines": sum(item["fine"] for item in items)}


def summary_report():
    with session() as conn:
        total_books = repository.count_books(conn)
        loans = repository.all_loans(conn)
    return {
        "total_books": total_books,
        "on_loan": policy.open_loan_count(loans),
        "fines_outstanding": policy.amount_owed(loans),
    }
