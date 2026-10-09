# Code Review: CustomerRepository

## Critical

**1. SQL Injection (blocking)** — `src/CustomerRepository.cs:15`

```csharp
var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";
```

`email` is interpolated directly into the SQL string. An attacker can supply a crafted email such as `' OR '1'='1` to bypass filters, or worse, run stacked queries depending on driver settings. This must be parameterized:

```csharp
const string sql = "SELECT Id, Email FROM Customers WHERE Email = @Email";
await using var command = new SqlCommand(sql, connection);
command.Parameters.Add("@Email", SqlDbType.NVarChar, 256).Value = email;
```

Note: specifying `SqlDbType` and length avoids parameter-size mismatches that can hurt plan cache reuse for `NVarChar` columns.

## Suggestions

**2. Implicit `IDisposable` behavior with `await using`** — lines 11, 16, 17

This is correct (`SqlConnection`, `SqlCommand`, `SqlDataReader` all support async dispose), so no change needed — but worth confirming the project targets a framework where `IAsyncDisposable` is implemented on these types (netstandard2.1+/net5+). If the package version is old, `await using` won't compile.

**3. `ExecuteReaderAsync` without `CommandBehavior.SingleRow`** — line 17

Since the method returns at most one `Customer`, passing `CommandBehavior.SingleRow | CommandBehavior.SingleResult` lets the provider optimize and documents intent. Optional, but cheap.

**4. Uniqueness assumption on `Email`** — line 15

`FindByEmailAsync` silently returns the *first* matching row. If `Email` isn't backed by a unique constraint in the database, duplicates produce nondeterministic results. Recommend adding `WHERE ... AND ...` semantics clarification or at minimum documenting/enforcing uniqueness at the schema level.

**5. Missing email validation** — line 8

Not strictly required since parameterization makes it safe, but a cheap guard (`string.IsNullOrWhiteSpace` → `ArgumentException`) avoids useless DB round-trips and clearer error semantics.

**6. Minor: no `ConfigureAwait(false)` / library conventions**

If this is shared library code, consider whether the codebase convention calls for `ConfigureAwait(false)`. Skipped in many modern ASP.NET Core codebases; check project norms.

## Verdict

**Request changes.** The SQL injection vulnerability is a hard blocker — everything else is secondary polish. The structure (sealed types, async throughout, proper disposal, nullable return) is otherwise solid.
