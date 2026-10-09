## Summary
High-risk change: `FindByEmailAsync` builds its SQL query via string interpolation of user-supplied input, exposing the repository to SQL injection.

## Findings

- [Critical] src/CustomerRepository.cs:14 — SQL injection via interpolated email parameter
  ```
  var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";
  ```
  The `email` argument is concatenated directly into the query text, so a caller supplying input like `' OR '1'='1` (or `'; DROP TABLE Customers;--`) alters the executed SQL. This can leak arbitrary customer data or execute destructive statements. Fix by parameterizing the query:
  ```csharp
  const string sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
  await using var command = new SqlCommand(sql, connection);
  command.Parameters.Add(new SqlParameter("@email", SqlDbType.NVarChar, 256) { Value = email });
  ```

## Verdict
Request changes
