# Expected: 01-sql-injection

## Must find
- `sqli` (critical): src/users.sql `FindUserByName` builds SQL by string concatenation with user input (new lines 9-10). Fix: use parameterized query with `sp_executesql` properly: `EXEC sp_executesql N'SELECT id, name, email FROM users WHERE name = @name', N'@name NVARCHAR(255)', @name`.

## Acceptable extras (not false positives)
- low/nit: the additional query also shows SQL injection via string concatenation.

## Must not flag
- Use of T-SQL syntax, stored procedures, or the procedure name.

## Hard fail
- Missing `sqli` sets `missed_critical`.
