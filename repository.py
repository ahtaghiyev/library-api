"""All SQL lives here. Each function takes an open connection and returns rows."""


# ---------- books ----------


def all_books(conn, only_available=False):
    if only_available:
        return conn.execute("SELECT * FROM books WHERE available = 1").fetchall()
    return conn.execute("SELECT * FROM books").fetchall()


def get_book(conn, book_id):
    return conn.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()


def add_book(conn, title, author, isbn):
    cur = conn.execute(
        "INSERT INTO books (title, author, isbn, available) VALUES (?, ?, ?, 1)", (title, author, isbn)
    )
    return cur.lastrowid


def delete_book(conn, book_id):
    conn.execute("DELETE FROM books WHERE id = ?", (book_id,))


def set_book_available(conn, book_id, available):
    conn.execute("UPDATE books SET available = ? WHERE id = ?", (1 if available else 0, book_id))


def count_books(conn):
    return conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]


# ---------- members ----------


def all_members(conn):
    return conn.execute("SELECT * FROM members").fetchall()


def get_member(conn, member_id):
    return conn.execute("SELECT * FROM members WHERE id = ?", (member_id,)).fetchone()


def get_member_by_email(conn, email):
    return conn.execute("SELECT * FROM members WHERE email = ?", (email,)).fetchone()


def add_member(conn, name, email, member_type):
    cur = conn.execute("INSERT INTO members (name, email, type) VALUES (?, ?, ?)", (name, email, member_type))
    return cur.lastrowid


# ---------- loans ----------


def all_loans(conn):
    return conn.execute("SELECT * FROM loans").fetchall()


def get_loan(conn, loan_id):
    return conn.execute("SELECT * FROM loans WHERE id = ?", (loan_id,)).fetchone()


def loans_for_member(conn, member_id):
    return conn.execute("SELECT * FROM loans WHERE member_id = ?", (member_id,)).fetchall()


def add_loan(conn, book_id, member_id, due_date, checked_out):
    cur = conn.execute(
        "INSERT INTO loans (book_id, member_id, due_date, checked_out) VALUES (?, ?, ?, ?)",
        (book_id, member_id, due_date, checked_out),
    )
    return cur.lastrowid


def mark_returned(conn, loan_id, fine):
    conn.execute("UPDATE loans SET returned = 1, fine = ? WHERE id = ?", (fine, loan_id))


def extend_loan(conn, loan_id, new_due_date):
    conn.execute("UPDATE loans SET due_date = ?, renewals = renewals + 1 WHERE id = ?", (new_due_date, loan_id))


def mark_fine_paid(conn, loan_id):
    conn.execute("UPDATE loans SET fine_paid = 1 WHERE id = ?", (loan_id,))


def open_loans_with_details(conn):
    """Open loans with the book title and member name, for the overdue report."""
    return conn.execute(
        """
        SELECT loans.id AS loan_id, books.title AS title, members.name AS member,
               loans.due_date AS due_date, loans.returned AS returned
        FROM loans
        JOIN books ON books.id = loans.book_id
        JOIN members ON members.id = loans.member_id
        WHERE loans.returned = 0
        """
    ).fetchall()
