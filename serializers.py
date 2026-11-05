"""How books, members, loans and reports look in the API's JSON. One shape per record type."""
from policy import current_fine, money


def book_json(book):
    return {
        "id": book["id"],
        "title": book["title"],
        "author": book["author"],
        "isbn": book["isbn"],
        "available": bool(book["available"]),
    }


def member_json(member):
    return {"id": member["id"], "name": member["name"], "email": member["email"], "type": member["type"]}


def loan_json(loan, with_current_fine=False):
    body = {
        "id": loan["id"],
        "book_id": loan["book_id"],
        "member_id": loan["member_id"],
        "due_date": loan["due_date"],
        "returned": bool(loan["returned"]),
        "fine": money(loan["fine"]),
        "fine_paid": bool(loan["fine_paid"]),
        "renewals": loan["renewals"],
        "checked_out": loan["checked_out"],
    }
    if with_current_fine:
        body["current_fine"] = money(current_fine(loan))
    return body


def account_loan_json(loan):
    """The shorter loan shape used inside GET /members/<id>/loans."""
    return {
        "id": loan["id"],
        "book_id": loan["book_id"],
        "due_date": loan["due_date"],
        "returned": bool(loan["returned"]),
        "fine": money(loan["fine"]),
        "fine_paid": bool(loan["fine_paid"]),
    }


def account_json(account):
    return {
        "loans": [account_loan_json(loan) for loan in account["loans"]],
        "total_owed": money(account["total_owed"]),
        "loans_remaining": account["loans_remaining"],
    }


def overdue_report_json(report):
    return {
        "items": [dict(item, fine=money(item["fine"])) for item in report["items"]],
        "total_fines": money(report["total_fines"]),
    }


def summary_report_json(report):
    return dict(report, fines_outstanding=money(report["fines_outstanding"]))
