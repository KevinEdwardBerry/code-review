# Expected: 01-sql-injection

## Must find
- `sqli` (critical): src/users.py `find_user_by_name` builds SQL by string concatenation with user input (new lines 12-13). Fix: parameterized query `cur.execute("... WHERE name = ?", (name,))`.

## Acceptable extras (not false positives)
- low/nit: connection not closed if `execute` raises (use `with`/try-finally).

## Must not flag
- Use of sqlite3 itself, or the function name.

## Hard fail
- Missing `sqli` sets `missed_critical`.
