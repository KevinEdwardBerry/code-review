# Code Review: `src/users.sql`

## Critical Issues

### 1. SQL Injection (BLOCKER)
Both additions build SQL via string concatenation with unparameterized user input:

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
EXEC sp_executesql @query
```
and
```sql
SELECT id, name, email FROM users WHERE name = '" + name + "'"
```

An input like `' OR '1'='1` or `'; DROP TABLE users; --` would execute arbitrary SQL. This defeats the entire purpose of a stored procedure.

**Fix** — the proc doesn't need dynamic SQL at all:
```sql
CREATE PROCEDURE FindUserByName
    @name NVARCHAR(255)
AS
BEGIN
    SELECT id, name, email FROM users WHERE name = @name;
END
```
If dynamic SQL were truly needed, use parameters: `EXEC sp_executesql @query, N'@name NVARCHAR(255)', @name`.

### 2. Invalid SQL Syntax (BLOCKER)
```sql
SELECT id, name, email FROM users WHERE name = '" + name + "'
```
This line sits at file top-level, outside any procedure, and mixes SQL with application-language string concatenation (`" + name + "`). It will fail to parse/execute as SQL. It looks like application code (e.g., PHP/JS) was accidentally pasted into the `.sql` file — it should be removed and replaced with a parameterized query in the calling code, or a call to the stored procedure.

## Minor Issues

- **Inconsistent style:** keywords are uppercase but there's no `;` statement terminators; `EXEC` lacks parentheses (valid, but `EXEC(...)` or `EXECUTE` is cleaner).
- **`NVARCHAR(MAX)`** for `@query` is unnecessary here, though harmless.
- No `SET NOCOUNT ON;` in the procedure (minor convention).
- The comment `-- User queries` followed by `+` on blank lines suggests formatting noise in the diff; ensure the file doesn't contain stray artifacts.

## Recommendation
Do not merge. Rewrite the procedure as a static parameterized query and delete the orphaned concatenated SELECT line entirely — and audit the application layer for any similar string-concatenated queries, since the pasted line suggests this pattern exists elsewhere.
