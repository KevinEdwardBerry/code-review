# Expected: 01-csharp-sql-injection

## Must find
- `sqli_email` (critical): `FindByEmailAsync` interpolates the caller-controlled `email` value into SQL at `src/CustomerRepository.cs:14` (`var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`). An email containing SQL syntax can alter the predicate or inject additional SQL when the command executes. Fix: use a parameterized query (`WHERE Email = @email`) and bind `email` through a `SqlCommand` parameter with the appropriate database type.

## Must not flag
- The use of `Microsoft.Data.SqlClient`, async disposal, the repository/record declarations, or cancellation-token handling.
- The possibility of SQL injection from any line other than the interpolated SQL statement; report this as one finding anchored to the vulnerable line.

## Hard fail
- Missing `sqli_email` sets `missed_critical`.
