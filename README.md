# Campus Library API: Refactoring Activity

This API works and its tests pass, but all the code is in one file. Your job is to reorganize it to **reduce coupling and increase cohesion, without changing what the API does**.

## Set up

Fork this repository, clone your fork and install the requirements. The [before-class setup](before-class-setup.md) has every step, including what to install first and the Windows commands.

```bash
git clone https://github.com/YOUR-USERNAME/library-api.git
cd library-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Check that everything works:

```bash
python -m unittest               # run the tests: 53 should pass
python -m flask run --port 8000  # start the API (Ctrl+C to stop)
```

With the API running, open these in your browser:

- <http://localhost:8000/books>
- <http://localhost:8000/reports/overdue>

To reset the data, stop the API and delete `library.db`. It is recreated the next time the API starts.

## Your task

### 1. Diagnose (10 minutes)

My diagnosis is in [DIAGNOSIS.md](DIAGNOSIS.md).

Read `app.py` **without changing it**. List at least five design problems. For each one, note:

- where it is
- whether it is mainly a coupling or a cohesion problem
- what future change it would make harder

### 2. Refactor (30 minutes)

Reorganize the code in small steps, and run the tests after each step. You decide the structure.

Fill in the "Before" column of the table below before you start.

### 3. Change request (10 minutes)

Your instructor will give you a new requirement. Implement it in your refactored code and count the places you had to edit.

## Rules

1. **Do not change `test_api.py`.**
2. **Keep `app.py` in this folder**, and make sure it still provides `app` and `init_db`. It can be very short.
3. **Keep `library.db` and `outbox.txt` as relative paths**, so they are created in the folder the API runs from. `outbox.txt` stands in for a real mail server.
4. **Keep the API's behavior the same:** the same URLs, status codes and JSON.

## Measure your work

| Measure | Before | After |
|---|---|---|
| Tests passing | 53 / 53 | 53 / 53 in `test_api.py`, plus 9 new rule tests in `test_policy.py` (62 total) |
| Lines in the largest file | 555 (`app.py`) | 228 (`services.py`); `app.py` is now 15 |
| Places where the fine rate appears | 7 | 1 (`FINE_PER_DAY` in `policy.py`) |
| Route handlers containing SQL | 16 of 16 | 0 of 16 (all SQL is in `repository.py`) |
| Places edited for the change request | n/a | _fill in after class_ |
| Can the fine rule be tested without HTTP or a database? | No | Yes: `policy.late_fine("2026-11-01", today=date(2026, 11, 5))` returns 2.0 (see `test_policy.py`) |

The line counts leave out `test_api.py` (317 lines, unchanged).

### New structure

Each module only depends on the ones below it:

| Module | Job |
|---|---|
| `app.py` | Builds the Flask app and creates the database on first run |
| `api.py` | HTTP: reads the request, calls one service, returns JSON, maps errors to status codes |
| `serializers.py` | The JSON shape of each record type |
| `services.py` | The library's operations (check out, return, renew, pay a fine, reports) |
| `policy.py` | The library's rules as pure functions: fines, loan limits, due dates, renewals |
| `notifications.py` | Emails to members (`outbox.txt` is only known to `send_email`) |
| `validation.py` | Format checks for email, ISBN, dates and member type |
| `repository.py` | All SQL queries |
| `db.py` | The connection, schema and sample data |

The commits follow the refactoring steps: the fine rule first, then the global `CURRENT_MEMBER`, then the layers, then unit tests for the rules.

## Questions to answer

1. Which module is the most cohesive? Describe its one job in a sentence.

   `policy.py`. It states the library's rules (how fines, loan limits, due dates and renewals work) as functions that take plain values and return answers, with no Flask, SQL or files.

2. Which dependency did you remove, and what can now change independently because of that?

   I removed the routes' dependency on the database, and the notifications' dependency on the `CURRENT_MEMBER` global. Routes no longer contain SQL or read columns by position (`loan[4]`), so the schema can gain or reorder columns by editing `repository.py` alone. `notify` now receives the recipient's email as a parameter, so emails can be sent from anywhere, safely under concurrent requests, and the mail channel can change from `outbox.txt` to a real server by editing only `send_email`.

3. What coupling remains, and why did you accept it?

   - `services.py` imports `repository`, `policy` and `notifications` directly instead of receiving them as parameters. Injecting them would allow swapping in fakes, but for an app this size it adds indirection with little gain, and `policy` is already testable alone.
   - The rest of the code still reads row fields by column name (`loan["due_date"]`), so a column rename would reach beyond `repository.py`. Mapping rows into separate model classes would remove that, but it would roughly double the code for a schema this small.
   - The error messages (for example `"loan limit reached"`) live in `policy.py` and `services.py`, but they are part of the API's contract. I accepted this because they describe the rule that was broken, and `api.py` still decides the status code.

## API reference

| Method | URL | Purpose |
|---|---|---|
| GET | `/books` | List books (`?available=true` to filter) |
| POST | `/books` | Add a book |
| GET | `/books/<id>` | Get a book |
| DELETE | `/books/<id>` | Delete a book that isn't on loan |
| GET | `/members` | List members |
| POST | `/members` | Add a member |
| GET | `/members/<id>` | Get a member |
| GET | `/members/<id>/loans` | Get a member's loans and amount owed |
| GET | `/loans` | List loans (`?overdue=true` to filter) |
| POST | `/loans` | Check out a book |
| GET | `/loans/<id>` | Get a loan |
| POST | `/loans/<id>/return` | Return a book |
| POST | `/loans/<id>/renew` | Renew a loan |
| POST | `/loans/<id>/pay-fine` | Pay a fine |
| GET | `/reports/overdue` | List overdue loans |
| GET | `/reports/summary` | Get library totals |

## Library rules

- Loans last 14 days and can be renewed once, for 14 more days, if they aren't overdue.
- Late returns cost $0.50 per day.
- Students can have 3 open loans, and staff can have 5.
- Members who owe money can't check out books.
