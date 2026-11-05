# Diagnosis of the original `app.py`

These problems were found by reading `app.py` before any changes (commit `d315810`).

| # | Problem | Where | Mainly | Future change it makes harder |
|---|---|---|---|---|
| 1 | The fine rule ($0.50 per day) is copied into 7 places, and the "amount owed" loop is copied twice | `member_loans`, `list_loans`, `get_loan`, `create_loan`, `return_book`, `report_overdue`, `report_summary` | Cohesion | Changing fine policy (a grace period, a cap, a different rate for staff). Every copy must change the same way, or reports and checkout will disagree. |
| 2 | `notify()` gets the recipient from the global `CURRENT_MEMBER`, which callers must set first | `CURRENT_MEMBER`, `notify`, `create_loan`, `renew_loan` | Coupling (global and temporal) | Sending email from a new place, such as an overdue reminder, or running with several threads: it can crash on `None` or mail the wrong member. |
| 3 | `return_book` and `pay_fine` write to `outbox.txt` directly instead of calling `notify()`, so the message format is written in 3 places | `notify`, `return_book`, `pay_fine` | Coupling | Switching to a real mail server, or changing the message format. |
| 4 | `check(value, kind)` bundles unrelated validations behind a string flag, and `notify` switches on `kind` and a `send` flag | helpers section | Cohesion (logical), plus control coupling | Adding a validation or a specific error message. A typo such as `check(x, "emial")` silently returns `False`. |
| 5 | Rows are read by position (`r[4]`, `loan[6]`) after `SELECT *` | every handler | Coupling | Adding or reordering a column. Every index after it silently points at the wrong field. |
| 6 | The JSON for a loan is built by hand 6 times, and books and members 3 times each | `list_loans`, `get_loan`, `create_loan`, `return_book`, `renew_loan`, `pay_fine`; book and member handlers | Cohesion | Adding or renaming a response field. It is already inconsistent: `current_fine` appears in some loan responses but not others. |
| 7 | Each route does everything: parsing HTTP, validating, opening `library.db`, applying rules, writing, sending email. Limits of 3 and 5 are duplicated. | every route, most clearly `create_loan`; `member_loans` | Cohesion, plus coupling to a specific database file | Reusing checkout rules outside HTTP, unit-testing rules, or adding a member type such as `faculty`, which meant editing `check`, `member_loans` and `create_loan`. |
