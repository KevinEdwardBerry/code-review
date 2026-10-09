## Summary
The change adds a customer repository whose email lookup is built via string interpolation, introducing a SQL injection vulnerability.

## Findings
[Critical] src/CustomerRepository.cs:14 — SQL injection via interpolated query
`var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`
Impact: `email` is inserted directly into the SQL text, so a value like `' OR '1'='1` (or worse, a stacked statement) lets an attacker bypass the lookup filter or execute arbitrary SQL.
Fix: Use a parameterized query, e.g. `var sql = "SELECT Id, Email FROM Customers WHERE Email = @email";` and `command.Parameters.AddWithValue("@email", email);` (or `command.Parameters.Add("@email", SqlDbType.NVarChar).Value = email;`).

## Verdict
Request changes
