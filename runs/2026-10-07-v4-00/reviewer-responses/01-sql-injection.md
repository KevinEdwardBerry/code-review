### Summary
The change adds a SQL Server stored procedure `FindUserByName` that builds a query via string concatenation, plus a stray non-SQL fragment line. Both the procedure and the trailing line contain classic SQL injection, and the trailing line is also invalid SQL that will break the script.

### Findings
- **[critical] src/users.sql:8 - SQL injection via string concatenation in stored procedure**
  - Problem: `@name` is concatenated directly into the query text and executed with `sp_executesql`. A value like `' OR 1=1 --` (or `'; DROP TABLE users --`) lets an attacker read or modify arbitrary data.
  - Fix: Don't use dynamic SQL at all — `SELECT id, name, email FROM users WHERE name = @name` — or, if dynamic SQL is required, parameterize: `SET @query = N'... WHERE name = @p1'; EXEC sp_executesql @query, N'@p1 NVARCHAR(255)', @p1 = @name`.
  - Code snippet:
    ```sql
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **[critical] src/users.sql:12 - Stray line is both invalid T-SQL and SQL injection**
  - Problem: The line `SELECT id, name, email FROM users WHERE name = '" + name + "'` is not valid T-SQL — `name` is an undefined identifier and `"..."` string quoting/concatenation is wrong, so running this script fails outright. It also appears to be a pasted application-code fragment embedding the same injectable concatenation pattern.
  - Fix: Remove the line entirely; the procedure already covers the lookup. If it was meant as a query, replace with `WHERE name = @name` against a declared parameter.
  - Code snippet:
    ```sql
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

- **[low] src/users.sql:7 - DECLARE missing semicolon/terminator robustness**
  - Problem: `DECLARE @query NVARCHAR(MAX)` and `SET`/`EXEC` statements lack semicolons; while currently legal, a `BEGIN...END` block followed by more statements can hit parsing pitfalls (e.g., if a `WITH`/CTE or `THROW` is added later). Minor defensive issue.
  - Fix: Terminate statements with semicolons and initialize in one step: `DECLARE @query NVARCHAR(MAX) = N'...';`.
  - Code snippet:
    ```sql
    DECLARE @query NVARCHAR(MAX)
    ```

### Verdict
request changes
