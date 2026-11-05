"""The HTTP layer: read the request, call one service, turn the result into JSON.

No SQL and no library rules here.
"""
from flask import Blueprint, jsonify, request

import serializers as out
import services
from policy import DEFAULT_MEMBER_TYPE

api = Blueprint("api", __name__)

STATUS_FOR_ERROR = {
    services.InvalidInput: 400,
    services.NotFound: 404,
    services.RuleBroken: 409,
}


@api.errorhandler(services.LibraryError)
def handle_library_error(error):
    return jsonify({"error": error.message}), STATUS_FOR_ERROR.get(type(error), 400)


def body():
    return request.get_json(silent=True) or {}


def flag(name):
    return request.args.get(name) == "true"


# ---------- books ----------


@api.get("/books")
def list_books():
    return jsonify([out.book_json(b) for b in services.list_books(only_available=flag("available"))])


@api.get("/books/<int:book_id>")
def get_book(book_id):
    return jsonify(out.book_json(services.get_book(book_id)))


@api.post("/books")
def create_book():
    data = body()
    book = services.add_book(data.get("title"), data.get("author"), data.get("isbn"))
    return jsonify(out.book_json(book)), 201


@api.delete("/books/<int:book_id>")
def delete_book(book_id):
    services.delete_book(book_id)
    return "", 204


# ---------- members ----------


@api.get("/members")
def list_members():
    return jsonify([out.member_json(m) for m in services.list_members()])


@api.get("/members/<int:member_id>")
def get_member(member_id):
    return jsonify(out.member_json(services.get_member(member_id)))


@api.post("/members")
def create_member():
    data = body()
    member = services.add_member(data.get("name"), data.get("email"), data.get("type", DEFAULT_MEMBER_TYPE))
    return jsonify(out.member_json(member)), 201


@api.get("/members/<int:member_id>/loans")
def member_loans(member_id):
    return jsonify(out.account_json(services.member_account(member_id)))


# ---------- loans ----------


@api.get("/loans")
def list_loans():
    loans = services.list_loans(only_overdue=flag("overdue"))
    return jsonify([out.loan_json(loan, with_current_fine=True) for loan in loans])


@api.get("/loans/<int:loan_id>")
def get_loan(loan_id):
    return jsonify(out.loan_json(services.get_loan(loan_id), with_current_fine=True))


@api.post("/loans")
def create_loan():
    data = body()
    loan = services.check_out(data.get("book_id"), data.get("member_id"), data.get("due_date"))
    return jsonify(out.loan_json(loan)), 201


@api.post("/loans/<int:loan_id>/return")
def return_book(loan_id):
    return jsonify(out.loan_json(services.return_book(loan_id)))


@api.post("/loans/<int:loan_id>/renew")
def renew_loan(loan_id):
    return jsonify(out.loan_json(services.renew_loan(loan_id)))


@api.post("/loans/<int:loan_id>/pay-fine")
def pay_fine(loan_id):
    return jsonify(out.loan_json(services.pay_fine(loan_id)))


# ---------- reports ----------


@api.get("/reports/overdue")
def report_overdue():
    return jsonify(out.overdue_report_json(services.overdue_report()))


@api.get("/reports/summary")
def report_summary():
    return jsonify(out.summary_report_json(services.summary_report()))
