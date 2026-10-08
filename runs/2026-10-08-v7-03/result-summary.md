# v7 - 2026-10-08 — Detailed results

- Prompt: `prompts/code-review.v7.md`
- Reviewer: subagent_explore (concrete model unknown; not exposed by the subagent interface)
- Judge: subagent_general (concrete model unknown; not exposed by the subagent interface)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **64.2/100** (-3.9 vs v7-02; prior: 68.1/100)
- Hard fails: none

## What changed
No prompt changes versus the previous evaluated v7 run (v7-02): both use `prompts/code-review.v7.md`, and the prompt-file diff is empty. This is a re-run of the same minimal v7 prompt; the original v6-to-v7 change removed the detailed scope, severity, citation, concurrency, typo, and output-format guidance.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 01-sql-injection | 3 | 0 | 3 | 2 | 2 | 1 | 1 | 65.0 | +6.7 |
| 02-off-by-one | 3 | 1 | 2 | 2 | 3 | 0 | 2 | 70.0 | -3.3 |
| 03-race-condition | 3 | 2 | 3 | 2 | 3 | 0 | 2 | 81.7 | +15.0 |
| 04-missing-error-handling | 3 | 2 | 2 | 2 | 2 | 0 | 3 | 75.0 | 0.0 |
| 05-clean-refactor | 0 | 0 | 2 | 2 | 1 | 1 | 2 | 28.3 | -41.7 |
| 06-typos | 3 | 1 | 1 | 2 | 3 | 1 | 1 | 65.0 | 0.0 |

### Typo recall (fixture 06)
| Category | Found/Total |
|---|---:|
| misspelling | 1/1 |
| swap | 3/3 |
| missing_letter | 2/2 |

## Observations / next changes
### Patterns in misses and false positives
- All seeded findings in the five non-clean fixtures were identified; none of the expected hard-fail flags fired. Typos were all found, but `Colour` was incorrectly called out despite being explicitly acceptable.
- Precision remains the main weakness: reviewers add speculative concerns and broad style/design recommendations, and the clean refactor review invents actionable null/overflow concerns instead of limiting itself to genuine defects or approving.
- Format scores are 0–1 on every fixture: reviews generally omit the requested Summary/Findings/Verdict structure. Actionability is consistently 2 because citations are absent or approximate rather than exact `file:line`.
- Severity calibration is uneven: the 1-based pagination defect and public API typo are not clearly prioritized over lower-impact findings, and several secondary suggestions are overemphasized.
- Regression against the immediately prior v7-02 run is concentrated in 05-clean-refactor (-41.7); 02-off-by-one also declined (-3.3). The concurrency fixture improved (+15.0), while 04 and 06 were unchanged.

### Per-typo-category recall (fixture 06)
- misspelling: 1/1
- swap: 3/3
- missing_letter: 2/2

### Suggested prompt changes
1. Require exact `### Summary`, `### Findings`, and `### Verdict` sections, with no substitute sections or extraneous recommendations.
2. Require a precise new-file `file:line` citation for each finding, derived from diff hunk headers; approximate line numbers do not satisfy the requirement.
3. Add a grounding rule: report only concrete, change-attributable defects supported by the diff; on behavior-preserving clean changes, do not invent null, overflow, style, or other speculative regressions.
4. Clarify severity ordering and typo exceptions: rank public API defects above user-facing copy and cosmetic typos, and do not flag documented acceptable spellings such as `Colour`.

## Per-fixture results
### 01-sql-injection
- [01-sql-injection.md](01-sql-injection.md)

<details><summary>Full AI response for 01-sql-injection</summary>

## Code Review: `src/users.sql`

### Critical: SQL Injection (Blocker)

The procedure builds a query via string concatenation and executes it with `sp_executesql`, which is fully vulnerable to SQL injection:

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

An attacker passing `@name = "' OR '1'='1' --"` can dump all users; worse inputs can modify/drop data depending on connection permissions. The entire purpose of `sp_executesql` is to enable *parameterized* queries — it's being misused here.

**Fix — two options:**

1. Simplest: no dynamic SQL at all.
```sql
CREATE OR ALTER PROCEDURE FindUserByName
    @name nvarchar(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id, name, email FROM users WHERE name = @name;
END
```

2. If dynamic SQL is truly required (it isn't here), parameterize it:
```sql
SET @query = N'SELECT id, name, email FROM users WHERE name = @name';
EXEC sp_executesql @query, N'@name nvarchar(255)', @name = @name;
```

### Additional Issues

1. **Buffer truncation:** `@query` is `nvarchar(1023)` while `@name` is `nvarchar(255)` — fine for this string, but the odd limit (1023) suggests a pattern that could silently truncate in longer queries. If kept, use `nvarchar(max)` for the query variable.

2. **String literals should be Unicode-prefixed:** `'SELECT ...'` should be `N'SELECT ...'` when assigned to `nvarchar` to avoid implicit conversion issues.

3. **`GO` placement:** `GO` is a batch separator for tools like SSMS/sqlcmd, not T-SQL. If this file is executed through a migration runner that doesn't understand `GO`, it will fail. If it *is* needed, note the procedure body is terminated by `END`, so `GO` placement is fine — but verify the deployment tool supports it.

4. **Missing error handling / schema qualification:** Consider `dbo.FindUserByName` and `dbo.users` — unqualified object names can resolve to the caller's default schema and cause subtle bugs.

5. **Minor:** `NOCOUNT ON` is good, but there's no `TRY/CATCH` or transaction handling (acceptable for a read-only query, but worth noting).

### Verdict

**Request changes.** The concatenation-based dynamic SQL is a textbook injection vulnerability. The non-dynamic rewrite (option 1) is the correct fix — it's simpler, faster (no recompilation of dynamic text), and safe.

</details>

### 02-off-by-one
- [02-off-by-one.md](02-off-by-one.md)

<details><summary>Full AI response for 02-off-by-one</summary>

## Code Review: `src/pagination.js`

I found two correctness bugs — one per function — plus a few robustness concerns.

### 🔴 Bug 1: `getPage` contradicts its documented 1-based contract

```js
/**
 * Returns the items for a 1-based page number.
 */
function getPage(items, page, pageSize) {
  const start = page * pageSize;   // BUG: treats page as 0-based
  const end = start + pageSize;
  return items.slice(start, end);
}
```

With a 1-based API, `getPage(items, 1, 10)` should return the *first* 10 items. Instead, `start = 1 * 10 = 10`, so it skips the first page entirely and returns items 10–19. Every caller gets the wrong page, and `getPage(items, 0, ...)` silently returns page 1 even though page 0 shouldn't exist.

**Fix:**
```js
const start = (page - 1) * pageSize;
```

### 🔴 Bug 2: `totalPages` undercounts with `Math.floor`

```js
function totalPages(items, pageSize) {
  return Math.floor(items.length / pageSize);  // BUG
}
```

For `items.length = 25, pageSize = 10`, this returns `2`, but there are 3 pages (the last with 5 items). Any UI rendering page buttons or a "next page" check will drop the final partial page, making those items unreachable — compounding Bug 1, since even callers who fix `getPage` themselves can't reach the last page.

**Fix:**
```js
return Math.ceil(items.length / pageSize);
```

### 🟡 Robustness concerns (worth addressing)

- **No validation of `pageSize`:** `pageSize <= 0` → `totalPages` returns `Infinity`/`NaN` (division by zero) or a negative number; `getPage` behaves strangely with negative sizes. Consider `if (pageSize <= 0) throw new RangeError(...)`.
- **No validation of `page`:** out-of-range or non-integer pages silently return empty/partial slices. Depending on desired API strictness, clamp or throw.
- **No input check on `items`:** passing a non-array throws a generic `TypeError`; a clearer guard (`Array.isArray`) improves error messages.
- **Mutability/`slice` behavior:** `slice` is correct (non-mutating, clamps `end`), so that's fine — just noting it handles `end > length` gracefully.

### Verdict

**Request changes.** The two off-by-one/logic bugs mean the module returns wrong results for its primary use cases (page 1 is unreachable, last partial page is uncounted). Suggested corrected implementation:

```js
function getPage(items, page, pageSize) {
  if (!Array.isArray(items)) throw new TypeError("items must be an array");
  if (!Number.isInteger(pageSize) || pageSize <= 0) throw new RangeError("pageSize must be a positive integer");
  if (!Number.isInteger(page) || page < 1) throw new RangeError("page must be a positive integer");
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

function totalPages(items, pageSize) {
  if (!Number.isInteger(pageSize) || pageSize <= 0) throw new RangeError("pageSize must be a positive integer");
  return Math.ceil(items.length / pageSize);
}
```

Also recommend adding tests covering: first page, last partial page, empty array, page beyond range, `page = 0`, `pageSize = 0`.

</details>

### 03-race-condition
- [03-race-condition.md](03-race-condition.md)

<details><summary>Full AI response for 03-race-condition</summary>

## Code Review: `src/counter.cs`

### 🔴 Critical / High-Severity Issues

**1. Not thread-safe (line 8–13)**
`RequestStats` is almost certainly intended for concurrent request counting (the name and API suggest request-per-path tracking). `Dictionary<K,V>` is **not thread-safe** in .NET:
- Concurrent `Inc` calls can lose updates (`counts[path]++` is a read-modify-write, not atomic) and can even corrupt the internal hash table structure, leading to infinite loops or exceptions on subsequent reads.
- `Count`/`Snapshot` called during a write can observe inconsistent state or throw.

**Fix:** Use `System.Collections.Concurrent.ConcurrentDictionary<string, int>`:
```csharp
private readonly ConcurrentDictionary<string, int> counts = new();

public void Inc(string path) => counts.AddOrUpdate(path, 1, (_, v) => v + 1);
```

**2. `Snapshot()` exposes mutable internal state (line 22–25)**
Returning `counts` directly hands callers a reference to the private dictionary. Callers can:
- Mutate stats behind the class's back (e.g., `snapshot["/x"] = 0;`), corrupting internal state.
- Keep a stale/half-updated view while the dictionary is being modified by request threads, or hold a lock-free reference to a mutating structure.

**Fix:** Return a defensive copy:
```csharp
public Dictionary<string, int> Snapshot() => new(counts);
// or better, a read-only view:
public IReadOnlyDictionary<string, int> Snapshot() => new ReadOnlyDictionary<string,int>(counts);
```

### 🟡 Medium Issues

**3. Double dictionary lookup in `Inc` and `Count`**
`ContainsKey` + indexer does two hash lookups. `TryGetValue` does one:
```csharp
public void Inc(string path)
{
    if (counts.TryGetValue(path, out var n)) counts[path] = n + 1;
    else counts[path] = 1;
}
```
(This micro-opt is moot if you adopt `ConcurrentDictionary.AddOrUpdate`.)

**4. No null validation on `path`**
`counts.ContainsKey(null)` throws `ArgumentNullException`. If a null path is a caller error, fail fast and explicitly:
```csharp
ArgumentNullException.ThrowIfNull(path);
```

### 🟢 Minor / Nits

**5. Comment style**
`.Inc` / `Count` / `Snapshot` comments are fine as documentation but consider `<summary>` XML doc comments, which is idiomatic for C# public APIs.

**6. `counts` should be `readonly`**
```csharp
private readonly Dictionary<string, int> counts = new();
```
Guards against accidental reassignment.

### Summary
The logic is correct for single-threaded use, but as a request counter it will very likely be used from multiple threads, where it will silently lose counts or corrupt the dictionary. `Snapshot()` also leaks the internal collection. Recommended shape:
```csharp
public class RequestStats
{
    private readonly ConcurrentDictionary<string, int> counts = new();

    public void Inc(string path)
    {
        ArgumentNullException.ThrowIfNull(path);
        counts.AddOrUpdate(path, 1, static (_, v) => v + 1);
    }

    public int Count(string path) => counts.TryGetValue(path, out var n) ? n : 0;

    public IReadOnlyDictionary<string, int> Snapshot() =>
        new Dictionary<string, int>(counts); // point-in-time copy
}
```

</details>

### 04-missing-error-handling
- [04-missing-error-handling.md](04-missing-error-handling.md)

<details><summary>Full AI response for 04-missing-error-handling</summary>

## Code Review

### Issues Found

**1. `writeBackup` leaks the file descriptor (bug — should fix)**
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
`fs.closeSync(fd)` is never called, so the fd stays open until GC/process exit. On repeated calls this can exhaust file descriptors (`EMFILE`). Either close it in a `try/finally`, or simply use `fs.writeFileSync(path, data)` which handles open/write/close atomically.

**2. `loadConfig` returns unvalidated data (type-safety concern)**
```ts
const cfg = JSON.parse(raw)
return cfg
```
`JSON.parse` returns `any`; nothing guarantees `port` is a number or `dbUrl` exists. A malformed config silently propagates until it fails elsewhere. Consider runtime validation (e.g., zod, or manual checks with a thrown error). Same applies to `fetchRemoteConfig`, which returns `res.json()` (a `Promise<any>`) cast to `AppConfig`.

**3. `fetchRemoteConfig` lacks error handling (reliability concern)**
- No check of `res.ok` — a 404/500 response will still be parsed and returned as if it were a valid config.
- No timeout — `fetch` can hang indefinitely.
- No handling of non-JSON error bodies (`res.json()` will throw a less-informative error).

**4. No error handling around file/JSON operations in `loadConfig`**
`fs.readFileSync` throws a raw `ENOENT` for missing files and `JSON.parse` throws a bare `SyntaxError` with byte-offset info. Wrapping these in a descriptive error (including `path`) would help debugging, though this is minor.

**5. Style/consistency nits**
- Mixed semicolon usage: interface fields use `;`, function bodies don't.
- `loadConfig`/`writeBackup` are synchronous while `fetchRemoteConfig` is async — fine, but synchronous I/O in `loadConfig` blocks the event loop if called at runtime rather than startup.

### Recommendations
- Replace `writeBackup` body with `fs.writeFileSync(path, data)` (or close `fd` in `finally`).
- Add a validation step producing `AppConfig` or throwing, shared by `loadConfig` and `fetchRemoteConfig`.
- In `fetchRemoteConfig`, check `res.ok`, add `AbortSignal.timeout(...)`, and surface HTTP errors clearly.

### Verdict
The fd leak in `writeBackup` is the one definite bug; the rest are robustness/typing improvements. I'd request changes on the leak and validation before approval.

</details>

### 05-clean-refactor
- [05-clean-refactor.md](05-clean-refactor.md)

<details><summary>Full AI response for 05-clean-refactor</summary>

## Code Review: `src/totals.cs`

### Summary
The change refactors a manual accumulation loop into a LINQ `Sum()` call and consolidates the tax calculation. The logic is mathematically equivalent, but there are a few points worth noting.

### Findings

**1. Behavioral equivalence — ✅ Correct (with one caveat)**
- Old: `total + (total * taxRate)`
- New: `subtotal * (1 + taxRate)`
- For `decimal` arithmetic these are equivalent (`a + a·r == a·(1 + r)`), and `1 + taxRate` is implicitly converted to `decimal`, so no type issue.

**2. Null-safety regression — ⚠️ Potential issue**
- Old code: `foreach` over `items` would throw `NullReferenceException` if `items` is null.
- New code: `items.Sum(...)` throws `ArgumentNullException` if `items` is null.
- This is a minor change in exception type. If any callers/tests assert on the specific exception, they may break. More importantly, neither version handles null — consider `items?.Sum(...) ?? 0m` or an explicit guard if null is possible.

**3. Empty list behavior — ✅ Safe**
- `Sum` on an empty `List<Item>` over `decimal` returns `0m`, matching the old `total = 0m` behavior. No regression here.

**4. Overflow considerations — ⚠️ Minor**
- `item.Price * item.Quantity` — if `Quantity` is not `decimal` (e.g., `int`), this multiplies `decimal * int` → `decimal`, fine.
- `Sum()` throws `OverflowException` if the accumulated total exceeds `decimal.MaxValue`, same as the old `+` accumulation. Equivalent behavior.
- One subtle difference: `subtotal * (1 + taxRate)` computes `1 + taxRate` first. If `taxRate` is near `decimal.MaxValue`, `1 + taxRate` could overflow where `subtotal * taxRate` wouldn't (edge case, unlikely in practice for a tax rate).

**5. Semantics/readability — ✅ Improvement**
- Renaming `total` → `subtotal` is clearer since it now correctly describes the pre-tax amount.
- The LINQ version is more idiomatic and concise.

**6. Redundant `using` — nit**
- If `System.Linq` was already imported elsewhere via global usings or the file is part of a project with `ImplicitUsings`, this may be redundant — harmless either way.

### Recommendation
**Approve with minor comments.** The refactor is correct and cleaner. Suggest either (a) adding a null check / documenting the non-null contract, and (b) confirming `taxRate` is a realistic rate so `1 + taxRate` can't overflow. Optionally keep the two-step form for readability:

```csharp
var subtotal = items.Sum(item => item.Price * item.Quantity);
var tax = subtotal * taxRate;
return subtotal + tax;
```

</details>

### 06-typos
- [06-typos.md](06-typos.md)

<details><summary>Full AI response for 06-typos</summary>

# Code Review: `src/accounts.ts`

## Summary
Adds an `Account` interface, a `createAccount` function, a `getAdress` getter, and two exported constants. The change has several typos (some user-visible), documentation/implementation mismatches, and a few design concerns.

---

## Issues

### 🔴 High — User-facing defects

1. **Typo in user-visible error message** (line ~21)
   ```ts
   throw new Error("Username lenght must be at least 3 charaters.")
   ```
   "lenght" → "length", "charaters" → "characters". This string is shown to users and also makes tests brittle if anyone snapshots it.

2. **Typo in exported function name** (line ~36)
   ```ts
   export function getAdress(account: Account): string
   ```
   `getAdress` → `getAddress`. Because this is a public export, fixing it later is a breaking API change — rename it now before it ships.

### 🟡 Medium

3. **Doc comment doesn't match behavior**
   > "Creates a new account **and sends a welcome email**."
   No email is sent — the function just builds an object and `console.log`s. Either implement the email or fix the comment; as written, the doc is misleading.

4. **Unused option: `timeoutMs`**
   `opts.timeoutMs` is accepted via `Partial<typeof DEFAULTS>` but never read. Either use it, or don't expose it — dead options imply functionality that doesn't exist.

5. **`Partial<typeof DEFAULTS>` as the options type is fragile**
   Consumers can't discover the options shape as a named type, and it's coupled to the `DEFAULTS` object's exact value types. Prefer an explicit `interface CreateAccountOptions { maxRetries?: number; timeoutMs?: number }`.

6. **Misspelled variable `retires`** (line ~15)
   ```ts
   const retires = opts.maxRetries ?? DEFAULTS.maxRetries
   ```
   → `retries`. Not a bug, but it propagates into the log line and hurts readability/greppability.

### 🟢 Low / nits

7. **Typos in comments and constants**
   - JSDoc: "We **recieve** the raw form input" → "receive".
   - `TEXT = "teh quick brown fox"` → "the". If this is placeholder/test text, flag it; it looks like it could leak into UI or tests.

8. **Inconsistent validation**
   `username` is trimmed/lowercased and validated, but `email` and `address` are passed through unvalidated — no trim, no format check on email. At minimum, document that validation is the caller's responsibility.

9. **Unnecessary object shorthand verbosity**
   ```ts
   username: username,
   ```
   → `username,` (shorthand).

10. **`console.log` in a service module**
    Library/service code writing directly to stdout is hard to silence. Consider a logger, an event, or returning the info to the caller.

11. **Missing semicolons / style inconsistency** — the new code omits semicolons; if the codebase standard uses them, run the formatter/linter.

12. **`LABEL = "Acme Colour Labs"`** — mixed US/UK spelling ("Colour"). Only a nit, but worth checking against brand/copy conventions; also, both `TEXT` and `LABEL` are exported with no usage or explanation — are they meant to live here?

---

## Suggested fixes (priority order)

1. Fix the error message spelling and rename `getAdress` → `getAddress` before merging (public API).
2. Correct the JSDoc or implement the welcome email.
3. Replace `Partial<typeof DEFAULTS>` with a named `CreateAccountOptions` interface; either use or remove `timeoutMs`.
4. Fix remaining typos (`retires`, `recieve`, `teh`) and simplify `username: username` to shorthand.
5. Decide on validation policy for `email`/`address` and replace `console.log` with proper logging.

</details>

---
