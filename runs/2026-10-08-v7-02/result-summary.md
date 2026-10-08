# v7 - 2026-10-08 — Detailed results

- Prompt: `prompts/code-review.v7.md`
- Reviewer: subagent_explore (unknown / Subagent Default where reported)
- Judge: subagent_general (unknown)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **68.1/100** (-7.2 vs v7-01)
- Hard fails: none

## What changed
This is a re-run of v7; the prompt file `prompts/code-review.v7.md` is unchanged from the previous v7-01 run. The original v6 → v7 diff stripped all severity, line-citation, concurrency, typo, and output-format guidance.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-sql-injection | 3 | 0 | 1 | 2 | 2 | 2 | 2 | 58.3 | -26.7 |
| 02-off-by-one | 3 | 1 | 2 | 2 | 3 | 2 | 2 | 73.3 | +5.0 |
| 03-race-condition | 3 | 0 | 2 | 2 | 3 | 2 | 2 | 66.7 | -18.3 |
| 04-missing-error-handling | 3 | 2 | 1 | 2 | 3 | 2 | 2 | 75.0 | -8.3 |
| 05-clean-refactor | 3 | 1 | 2 | 2 | 2 | 2 | 2 | 70.0 | +1.7 |
| 06-typos | 3 | 1 | 1 | 2 | 2 | 2 | 2 | 65.0 | +3.3 |


### Typo recall (fixture 06)

| Category | Found/Total |
|---|---|
| misspelling | 1/1 |
| swap | 3/3 |
| missing_letter | 2/2 |


## Observations / next changes
### Patterns in misses and false positives
- The minimal v7 prompt still finds every seeded issue, but it pays a heavy precision penalty: reviewers invent or over-interpret non-defects (schema qualification, query buffer, naming conventions, null-safety "regression", out-of-range pagination, `Colour` false positive).
- Severity calibration is the weakest area: medium issues are repeatedly labeled critical/high (SQLi is correctly critical, but `totalPages`, `fd_leak`, and `no_validation` are over-ranked).
- Actionability remains mediocre because no exact `file:line` citations are provided on any fixture.
- Format adherence is loose: extra sections (`Suggested revised version`, `Testing Recommendations`, emoji severity labels) replace the required Summary/Findings/Verdict structure.

### Per-typo-category recall (fixture 06)
- misspelling: 1/1
- swap: 3/3
- missing_letter: 2/2

### Suggested prompt changes
1. Restore severity definitions and concrete examples so medium/edge issues stop being over-ranked as critical/high.
2. Add explicit must-not-flag lists for style items, British spellings in proper names, literal test data, and behavior-preserving rewrites.
3. Require exact `file:line` citations with a worked `@@` hunk-header example.
4. Enforce a Summary/Findings/Verdict format and forbid emojis, positives-as-findings, and extra sections.

## Per-fixture results
### 01-sql-injection

- [01-sql-injection.md](01-sql-injection.md)

<details><summary>Full AI response for 01-sql-injection</summary>

# Code Review: `src/users.sql`

## Critical Issues

### 1. SQL Injection Vulnerability (BLOCKER)
The stored procedure builds a SQL string by concatenating `@name` directly into the query text and executing it with `sp_executesql`:

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

An attacker passing `@name = "x' OR '1'='1" --"` (or worse, `x'; DROP TABLE users; --`) will execute arbitrary SQL. This defeats the entire purpose of a stored procedure and is a textbook injection hole.

**Fix:** There is no reason for dynamic SQL here at all. Use a static parameterized statement:

```sql
CREATE OR ALTER PROCEDURE FindUserByName
    @name nvarchar(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id, name, email FROM users WHERE name = @name;
END
GO
```

If dynamic SQL were genuinely required (it isn’t), the safe pattern is parameterization via `sp_executesql`:

```sql
SET @query = N'SELECT id, name, email FROM users WHERE name = @p1';
EXEC sp_executesql @query, N'@p1 nvarchar(255)', @p1 = @name;
```

### 2. Unicode Prefix Missing
The dynamic string literal uses `'...'` instead of `N'...'`. Since `@query` is `nvarchar`, non-Unicode content in the literal is fine here, but the convention and safety practice is to always use `N` prefixes on `nvarchar` literals. Minor now, but it becomes a real bug if the query ever embeds other nvarchar data.

### 3. Quote-Escaping Fragility
Even if injection weren’t a concern, a legitimate name containing a single quote (e.g., `O'Brien`) would break the query at runtime — a silent functional bug that only surfaces with real data.

## Moderate Issues

### 4. `@query` Size Limit
`nvarchar(1023)` is an arbitrary, small cap. If this pattern grows, truncation produces a truncated/partial statement — possibly an error, possibly an altered-but-valid query. Use `nvarchar(max)` when dynamic SQL is justified (or, again, eliminate it).

### 5. Missing Schema Qualification
`users` should be `dbo.users` (or the appropriate schema). Unqualified references incur resolution overhead and can resolve to the wrong object depending on the executing user’s default schema.

### 6. Error Handling / Semantics
- No consideration of what "find" means: exact match vs. `LIKE`? Multiple users with the same name will return multiple rows — confirm callers handle that.
- No `TRY/CATCH` or transaction needed for a single SELECT, but worth noting if this proc grows.

## Minor / Style

- `SET NOCOUNT ON;` — good, included.
- Consider naming convention consistency (`FindUserByName` vs. `usp_...` or `Users_GetByName`, whatever the codebase uses).
- `CREATE OR ALTER` requires SQL Server 2016 SP1+ — confirm the target version.

## Summary

| Severity | Issue |
|---|---|
| 🔴 Blocker | SQL injection via string concatenation + `sp_executesql` |
| 🔴 Blocker | Quote characters in input break the query |
| 🟡 Moderate | Unqualified table name; arbitrary 1023-char buffer; unclear match semantics |
| 🟢 Minor | Missing `N` prefix; naming/version conventions |

**Recommendation:** Reject this change. The dynamic SQL provides zero benefit — replace it with the plain parameterized `SELECT` shown above, which fixes the injection hole, the quote-escaping bug, and the buffer limit in one edit.

</details>

### 02-off-by-one

- [02-off-by-one.md](02-off-by-one.md)

<details><summary>Full AI response for 02-off-by-one</summary>

# Code Review: `src/pagination.js`

## Summary
The diff adds two pagination helpers: `getPage` and `totalPages`. Both contain correctness bugs related to indexing and edge cases.

## Findings

### 🔴 Critical: Off-by-one error in `getPage`
The JSDoc states the page number is **1-based**, but the implementation treats it as 0-based:

```js
const start = page * pageSize;
```

For `page = 1, pageSize = 10`, this yields `start = 10`, skipping the entire first page. For a 1-based API it must be:

```js
const start = (page - 1) * pageSize;
```

This is the kind of bug that will silently drop the first `pageSize` items — easy to miss without a test asserting `getPage(items, 1, n)` returns the first `n` items.

### 🔴 Critical: `totalPages` undercounts when there’s a remainder

```js
return Math.floor(items.length / pageSize);
```

`Math.floor` truncates the partial last page. E.g., `items.length = 25, pageSize = 10` returns `2`, but there are `3` pages (the last with 5 items). Should be:

```js
return Math.ceil(items.length / pageSize);
```

### 🟡 No input validation
Both functions will produce confusing results rather than errors on invalid input:
- `getPage(items, 0, n)` or negative `page` → `slice` with negative indices returns items from the **end** of the array (silently wrong).
- `pageSize <= 0` → `totalPages` returns `Infinity` or `NaN`; `getPage` returns an empty array or the whole array depending on the sign.
- `items` not an array → `slice`/`length` throw or misbehave.

Recommend validating: `page >= 1`, `pageSize >= 1` (integer), and `Array.isArray(items)`, throwing `RangeError`/`TypeError` as appropriate.

### 🟡 Out-of-range pages silently return `[]`
`getPage(items, 999, 10)` returns `[]` rather than signaling the page doesn’t exist. This may be intended (lenient slicing) but should be documented, or clamped/validated against `totalPages`.

### 🟢 Minor: consistency/documentation
- Document units and types in JSDoc (`@param {Array} items`, `@param {number} page`, etc.) — especially since the 1-based contract is the source of the bug.
- Consider returning `0` pages for empty `items` (current code does this correctly once `Math.ceil` is used — `Math.ceil(0/x) = 0`, good).

## Suggested Fix

```js
function getPage(items, page, pageSize) {
  if (!Number.isInteger(page) || page < 1) throw new RangeError('page must be a positive integer');
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError('pageSize must be a positive integer');
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

function totalPages(items, pageSize) {
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError('pageSize must be a positive integer');
  return Math.ceil(items.length / pageSize);
}
```

## Testing Recommendations
Add tests covering: first page, last partial page, `items.length % pageSize === 0`, empty array, page beyond range, `page = 0`, `pageSize = 0`.

## Verdict
**Request changes** — two functional bugs (off-by-one, floor vs. ceil) will cause incorrect pagination in any consumer of this module.

</details>

### 03-race-condition

- [03-race-condition.md](03-race-condition.md)

<details><summary>Full AI response for 03-race-condition</summary>

# Code Review: `src/counter.cs`

## Summary

Adds a `RequestStats` class that tracks per-path request counts using a `Dictionary<string, int>`, with `Inc`, `Count`, and `Snapshot` methods. The logic is correct for single-threaded use, but there are several issues worth flagging — one significant (mutable state leak / thread safety) and several minor.

## Issues

### 1. `Snapshot()` exposes internal mutable state (High)

```csharp
public Dictionary<string, int> Snapshot()
{
    return counts;
}
```

This returns a direct reference to the internal dictionary. Callers can:
- Mutate the counts (e.g., `stats.Snapshot()["/foo"] = 0`), corrupting internal state.
- Hold a live view that changes under them — typically not what "snapshot" implies (a snapshot should be a point-in-time copy).
- Enumerate while another part of the code calls `Inc`, causing `InvalidOperationException`.

**Recommendation:** Return a copy or a read-only view:

```csharp
public Dictionary<string, int> Snapshot() => new Dictionary<string, int>(counts);
// or
public IReadOnlyDictionary<string, int> Snapshot() => new Dictionary<string, int>(counts);
```

Also consider whether returning `IReadOnlyDictionary<string, int>` better communicates intent.

### 2. Not thread-safe (High, if used in a request-handling context)

The class name (`RequestStats`) and comment ("records one request") strongly suggest this will be called from concurrent request handlers. `Dictionary<K,V>` is not thread-safe: concurrent `Inc` calls can lose updates (read-modify-write race on `counts[path]++`), and mixed reads/writes can corrupt internal structure or throw.

**Recommendations:**
- Use `ConcurrentDictionary<string, int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or
- Guard all access with a `lock`, or
- Document explicitly that the class is not thread-safe and callers must synchronize.

Even with `ConcurrentDictionary`, `Snapshot()` should copy (e.g., `new Dictionary<string,int>(counts)` — a snapshot of a `ConcurrentDictionary` enumeration is safe).

### 3. File/class naming conventions (Medium)

- File is named `counter.cs` but declares `RequestStats`. C# convention is one file per public class, named after the class (`RequestStats.cs`).
- Missing a `namespace` declaration. Putting types in the global namespace in a shared source file is a smell and can cause collisions.
- Path/file casing: `.cs` lowercase is fine, but ensure it fits repo conventions.

### 4. Performance micro-issues (Low)

```csharp
if (counts.ContainsKey(path))
    counts[path]++;
else
    counts[path] = 1;
```

- Double lookup: `ContainsKey` + indexer. Could use `TryGetValue` to do one lookup:
  ```csharp
  counts.TryGetValue(path, out var c);
  counts[path] = c + 1;
  ```
- Same for `Count`: `counts.TryGetValue(path, out var c) ? c : 0` avoids two hash lookups. (On modern .NET you can also use `CollectionsMarshal.GetValueRefOrAddDefault` for a single lookup.)

### 5. Null/empty path handling (Low)

- `Inc(null)` throws `ArgumentNullException` from the dictionary — acceptable, but undocumented. `Count(null)` also throws; an alternative is to return 0 for null. Decide and document, or add explicit `ArgumentNullException.ThrowIfNull(path)`.
- No validation of empty string — probably fine, but worth a thought.

### 6. `counts` field could be `readonly` (Low)

```csharp
private readonly Dictionary<string, int> counts = new();
```
Target-typed `new()` and `readonly` make intent clearer and prevent accidental reassignment.

### 7. Comments (Nit)

`// Inc records one request...` — C# convention is XML doc comments (`/// <summary>...`) on public APIs so IntelliSense/tooling picks them up.

## Suggested revised version

```csharp
using System.Collections.Concurrent;
using System.Collections.Generic;

namespace MyApp.Stats
{
    /// <summary>Tracks request counts per path. Thread-safe.</summary>
    public class RequestStats
    {
        private readonly ConcurrentDictionary<string, int> counts = new();

        /// <summary>Records one request for the given path.</summary>
        public void Inc(string path) =>
            counts.AddOrUpdate(path, 1, (_, c) => c + 1);

        /// <summary>Returns the number of requests recorded for the given path.</summary>
        public int Count(string path) =>
            counts.TryGetValue(path, out var c) ? c : 0;

        /// <summary>Returns a point-in-time copy of the current counts.</summary>
        public IReadOnlyDictionary<string, int> Snapshot() =>
            new Dictionary<string, int>(counts);
    }
}
```

## Verdict

Logic is correct for a single-threaded scenario, but I’d request changes before merge: fix the mutable-state leak in `Snapshot()`, address (or document) thread safety given the apparent request-tracking use case, add a namespace, and rename the file to match the class.

</details>

### 04-missing-error-handling

- [04-missing-error-handling.md](04-missing-error-handling.md)

<details><summary>Full AI response for 04-missing-error-handling</summary>

# Code Review: `src/config.ts`

## Summary
This change adds a typed config-loading module with three functions. The overall shape is reasonable, but there are several correctness and robustness issues, most notably a **file descriptor leak** and **unchecked write completeness** in `writeBackup`.

## Findings

### 1. `writeBackup` leaks a file descriptor (High)
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
`fd` is never closed via `fs.closeSync(fd)`. Repeated calls will leak descriptors and can eventually hit `EMFILE`. If an exception is thrown by `writeSync`, the leak is guaranteed. Either:
- Use `fs.writeFileSync(path, data)` (simplest, handles open/write/close internally), or
- Wrap in `try/finally` and call `fs.closeSync(fd)`.

### 2. `writeSync` may perform a partial write (Medium)
`fs.writeSync` returns the number of bytes written; it is not guaranteed to write the full string in one call. Either check the return value and loop, or just use `fs.writeFileSync`, which handles this for you.

### 3. No runtime validation of parsed config (High)
```ts
const cfg = JSON.parse(raw)
return cfg
```
`JSON.parse` returns `any`; returning it as `AppConfig` silently accepts missing or wrongly-typed fields (e.g., `port: "8080"`, missing `dbUrl`). This defeats the purpose of the interface. Add explicit validation:
```ts
if (typeof cfg.port !== "number" || typeof cfg.dbUrl !== "string") {
  throw new Error("invalid config");
}
```
or use a schema validator (zod, ajv, etc.).

### 4. Same validation problem in `fetchRemoteConfig` (High)
`res.json()` also returns `any` (in older TS DOM libs) and is blindly returned as `AppConfig`. A malformed remote payload propagates deep into the app before failing. Validate as above.

### 5. `fetchRemoteConfig` ignores HTTP errors (Medium)
```ts
const res = await fetch(url)
return res.json()
```
A 404/500 response body will still be parsed and cast to `AppConfig`. Check `res.ok` (or `res.status`) and throw a descriptive error. Also consider a timeout (`AbortSignal.timeout(...)`) since `fetch` has no default timeout, and handle JSON parse failures with a wrapped error.

### 6. `loadConfig` swallows context on errors (Low)
`fs.readFileSync` and `JSON.parse` errors propagate raw, which is okay, but wrapping them (`throw new Error(\`failed to load config from ${path}: ...\`)`) would make debugging much easier. Consider whether a synchronous blocking read is acceptable here — fine for startup config loading, but worth noting.

### 7. No durability guarantee for the backup (Low)
If `writeBackup` is meant to produce a durable backup, consider `fs.fsyncSync(fd)` before closing (or document that durability isn’t required). `"w"` also truncates an existing backup before writing — a crash mid-write could leave a truncated backup; writing to a temp file + rename would be safer.

### 8. Style/consistency (Nit)
Inconsistent semicolons (missing after `readFileSync`, `JSON.parse`, `openSync`, `writeSync`, `fetch`, `res.json()`). If the codebase uses semicolons (as the import line suggests), keep it consistent — or let the linter/formatter enforce it.

## Recommendations
- Rewrite `writeBackup` as `fs.writeFileSync(path, data)` (fixes findings 1–2).
- Extract a `validateConfig(raw: unknown): AppConfig` used by both loaders.
- Check `res.ok` and add a timeout in `fetchRemoteConfig`.
- Wrap errors with path/URL context.

</details>

### 05-clean-refactor

- [05-clean-refactor.md](05-clean-refactor.md)

<details><summary>Full AI response for 05-clean-refactor</summary>

# Code Review

## Summary
The change replaces a manual accumulation loop with LINQ `Sum`, and refactors the tax calculation from `total + (total * taxRate)` to `subtotal * (1 + taxRate)`. This is a small, readability-focused refactor.

## Findings

### 1. ✅ Functional equivalence (mostly)
The math is equivalent: `total + total * taxRate == total * (1 + taxRate)` for decimal arithmetic in normal cases. However, there’s a subtle difference worth noting:

- **Original:** `total + (total * taxRate)` — one multiplication, one addition.
- **New:** `subtotal * (1 + taxRate)` — one addition on `decimal` (with implicit `int → decimal` conversion), one multiplication.

With `decimal`, both are exact arithmetic (no floating-point rounding), so results should be identical. If this were `double`, the two forms could produce different rounding, but for `decimal` money calculations this is fine. ✅

### 2. ⚠️ Null-safety regression risk
- **Original:** `foreach` over `items` throws `NullReferenceException` if `items` is null.
- **New:** `items.Sum(...)` throws `ArgumentNullException` if `items` is null.

Different exception type — if any caller or test catches `NullReferenceException` specifically, this is a breaking change. Minor, but worth noting. Consider `items?.Sum(...) ?? 0m` if null is a legitimate input.

### 3. ⚠️ Overflow behavior unchanged but worth checking
`Sum` on `decimal` throws `OverflowException` if the accumulated total exceeds `decimal.MaxValue`. The original `total = total + ...` also throws on overflow, so behavior is equivalent. ✅

### 4. ⚠️ `1 + taxRate` type inference
`1 + taxRate` — the literal `1` is `int`, implicitly converted to `decimal`. Works correctly, but for clarity and to signal intent, `1m + taxRate` would be more idiomatic in a `decimal` context. Nitpick only.

### 5. ✅ Readability improvement
`items.Sum(item => item.Price * item.Quantity)` is clearer and idiomatic C#. Good change.

### 6. 📝 Naming improvement
`subtotal` is a better name than `total` since it’s pre-tax. Positive.

### 7. ⚠️ Missing using/namespace considerations
`using System.Linq;` was added — correct and necessary. Note the original file’s implicit `using System.Collections.Generic;` for `List<Item>` must still exist elsewhere (global usings or elsewhere in the file); the diff context suggests it’s fine.

## Minor Issues
- **Performance:** `Sum` with a lambda has marginally more overhead than a raw loop (delegate invocation per item), but this is negligible for order calculations and not worth reverting.
- No unit tests shown — recommend confirming tests exist covering: empty list (returns `0m` — `Sum` on empty returns 0, same as original ✅), null input, and a tax rate of 0.

## Verdict
**Approve with minor comments.** The refactor is correct, more readable, and semantically equivalent for `decimal` arithmetic. Suggested nits:
- Use `1m` instead of `1` for clarity.
- Consider/document null-input behavior change (`NullReferenceException` → `ArgumentNullException`).

```csharp
var subtotal = items.Sum(item => item.Price * item.Quantity);
return subtotal * (1m + taxRate);
```

</details>

### 06-typos

- [06-typos.md](06-typos.md)

<details><summary>Full AI response for 06-typos</summary>

# Code Review

## Summary
The diff adds an `Account` interface, a `createAccount` function, a `getAdress` helper, and two string constants to a previously near-empty `src/accounts.ts`.

## Issues

### Bugs / Functional issues

1. **`getAdress` is misspelled** — should be `getAddress`. This typo will propagate into every call site and is hard to fix later once consumers depend on it. Rename before merging.

2. **Unused `timeoutMs` option** — `opts` accepts `timeoutMs` via `Partial<typeof DEFAULTS>`, but it’s never read. Either use it or don’t accept it. Similarly, `retires` is only used in a `console.log`, so `maxRetries` doesn’t actually control any retry behavior — the JSDoc says "sends a welcome email" but no email logic exists. The docs over-promise.

3. **No email normalization/validation** — `username` is trimmed and lowercased, but `email` and `address` are passed through raw. Inconsistent normalization; at minimum `email` should probably be trimmed/lowercased too.

4. **`username.length < 3` after trim is fine, but check ordering** — normalization happens before validation, which is correct; however, the original (pre-trim) input is lost if callers need it for error reporting. Minor.

5. **`console.log` in library code** — logging "Created account for ..." leaks PII (username) and couples the module to stdout. Use a logger or remove.

### Typos (multiple — suggests missing spellcheck)

- `recieve` → `receive` (JSDoc)
- `retires` → `retries` (variable name; read as "retires" throughout)
- `lenght` → `length` (error message)
- `charaters` → `characters` (error message)
- `getAdress` → `getAddress` (exported API — see above)
- `teh` → `the` in `TEXT = "teh quick brown fox"` — if intentional (e.g., test fixture), add a comment; otherwise fix.
- `LABEL = "Acme Colour Labs"` — "Colour" is valid British English; flag only if the codebase standardizes on American English.

### Style / consistency

- `DEFAULTS` object and statements lack semicolons while the file/project may use them — verify against lint config.
- `{ username: username }` can be shorthand `{ username }`.
- `TEXT` and `LABEL` constants are exported with no usage or context — unclear purpose; remove if dead code or move to an appropriate module.
- `input: Account` for raw form input is misleading — raw input isn’t an `Account` yet (and arguably shouldn’t carry a trimmed/lowercased contract). Consider a separate `AccountInput`/`CreateAccountInput` type.

## Recommendations

1. Rename `getAdress` → `getAddress` and `retires` → `retries` before this becomes public API.
2. Fix all misspellings, especially in the user-facing error message.
3. Either implement the documented email/retry behavior or trim the JSDoc/opts to match reality.
4. Normalize `email` alongside `username`; validate email format.
5. Remove `console.log` or route through the project’s logging abstraction.
6. Add unit tests for: short username rejection, normalization, defaults merging.

</details>



---
