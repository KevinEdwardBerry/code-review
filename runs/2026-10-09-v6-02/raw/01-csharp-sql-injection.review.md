## Summary
New `CustomerRepository` that builds a SQL query via string interpolation, introducing a SQL injection vulnerability.

## Findings
[Critical] src/CustomerRepository.cs:14 — SQL injection via interpolated `email`
> `var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`

`email` is an unvalidated caller-supplied string interpolated directly into the SQL text. A value such as `' OR '1'='1` (or a `'; DROP TABLE ...--` payload) alters the query, allowing arbitrary data reads or destructive statements depending on connection permissions. Fix by parameterizing:

```csharp
const string sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
await using var command = new SqlCommand(sql, connection);
command.Parameters.AddWithValue("@email", email);
```

## Verdict
Request changes
