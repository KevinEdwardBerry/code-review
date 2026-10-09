## Summary
Adds a new `CustomerRepository` with a SQL injection vulnerability in email lookup — high-risk change.

## Findings

[Critical] src/CustomerRepository.cs:14 — SQL injection via string-interpolated query
```
var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";
```
The `email` parameter is interpolated directly into the SQL text. An attacker can supply input like `' OR '1'='1` to bypass the email filter or `'; DROP TABLE Customers;--` to execute arbitrary statements, depending on the SQL Server configuration. This exposes customer data and allows destructive queries.

Fix: use a parameterized query:
```csharp
var sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
await using var command = new SqlCommand(sql, connection);
command.Parameters.AddWithValue("@email", email);
```

## Verdict
Request changes