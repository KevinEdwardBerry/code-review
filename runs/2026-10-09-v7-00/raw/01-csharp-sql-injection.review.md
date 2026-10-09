## Summary
New repository method builds a SQL query by interpolating user input, introducing a critical SQL injection vulnerability.

## Findings
- [Critical] src/CustomerRepository.cs:14 — SQL injection via string-interpolated query
  `var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`
  The `email` parameter is inserted directly into the SQL text, so an attacker-controlled value (e.g., `' OR '1'='1`) can alter the query, exfiltrate arbitrary rows, or execute injected statements. Fix: use a parameterized query, e.g.
  ```csharp
  var sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
  await using var command = new SqlCommand(sql, connection);
  command.Parameters.AddWithValue("@email", email);
  ```

## Verdict
Request changes
