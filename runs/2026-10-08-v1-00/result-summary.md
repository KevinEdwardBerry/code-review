# v1 - 2026-10-08 — Detailed results

- Prompt: `prompts/code-review.v1.md`
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **70.6/100** (new baseline; no previous evaluation)
- Hard fails: 05-clean-refactor — `fabricated` (unsupported claim that the class declaration was removed and re-added)

## What changed

Baseline: this is the first evaluated prompt version; there is no previous evaluated prompt to diff against.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 01-sql-injection | 3 | 1 | 2 | 2 | 3 | 1 | 2 | 71.7 | new |
| 02-off-by-one | 3 | 3 | 0 | 2 | 3 | 2 | 2 | 76.7 | new |
| 03-race-condition | 3 | 1 | 2 | 2 | 3 | 1 | 3 | 73.3 | new |
| 04-missing-error-handling | 3 | 1 | 1 | 2 | 3 | 1 | 2 | 66.7 | new |
| 05-clean-refactor | 3 | 1 | 2 | 2 | 2 | 2 | 3 | 71.7 | new — FAIL |
| 06-typos | 3 | 1 | 1 | 2 | 2 | 1 | 2 | 63.3 | new |

Overall delta: new baseline. Scores use weighted criteria (30/20/15/15/10/5/5) and are rounded to one decimal per fixture before the mean.

## Typo recall

| Category | Found / total |
|---|---:|
| misspelling | 1/1 |
| swap | 3/3 |
| missing_letter | 2/2 |

## Observations / next changes

- Recall was complete on all six fixtures, including all six typo items. No expected finding was missed, and no `missed_critical` or `missed_behavioral_typo` flag was set.
- Precision was consistently reduced by optional/speculative material. Examples included unrelated style/API comments, speculative null handling/timeouts, and flagging the explicitly acceptable proper-name spelling `Colour`.
- The clean-refactor fixture had a hard fail: the review claimed an identical class declaration was removed and re-added, which is not supported by the diff. This is the only hard fail.
- Severity calibration and format adherence were weak: severity was frequently absent or overstated, and most reviews did not use the expected Summary / Findings / Verdict structure. File-and-line references were also generally missing, lowering actionability.
- Suggested prompt changes:
  1. Require a compact `Summary / Findings / Verdict` structure, with findings ordered by severity and each finding including severity plus exact file/line references.
  2. Require every finding to cite evidence from the diff and explain the concrete impact; omit speculative best-practice/style suggestions unless the diff demonstrates a defect.
  3. Calibrate severity to impact and distinguish blocking defects from optional nits; do not label all correctness issues as blocking.
  4. For clean refactors, explicitly check that alleged behavior changes or diff churn are visible in the patch before reporting them; otherwise approve with no or clearly optional nits.

## Per-fixture results

### [01-sql-injection](01-sql-injection.md) — 71.7/100 (new)
<details><summary>Full AI response</summary>

## Code Review: `src/users.sql`

### 🔴 Critical: SQL Injection Vulnerability

The `FindUserByName` procedure concatenates the `@name` parameter directly into a dynamic SQL string:

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

This is a textbook SQL injection vulnerability. An input like `' OR '1'='1' --` or `'; DROP TABLE users; --` would execute arbitrary SQL. Also, any legitimate name containing a single quote (e.g., `O'Brien`) will break the query.

### Recommended Fix

**Option 1 (preferred):** Dynamic SQL isn't needed at all here — use a plain parameterized query:

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

**Option 2:** If dynamic SQL is genuinely required, parameterize `sp_executesql`:

```sql
DECLARE @query nvarchar(1023) =
    N'SELECT id, name, email FROM users WHERE name = @name';
EXEC sp_executesql @query, N'@name nvarchar(255)', @name = @name;
```

### Minor Issues

- `@query` should be `nvarchar` with Unicode literal prefix (`N'...'`) to avoid implicit-conversion issues with non-ASCII names.
- No `NULL`/empty-input handling — decide whether `@name IS NULL` should return nothing or raise an error.
- If names aren't unique, consider whether callers expect multiple rows; document the contract.

**Verdict:** Do not merge as-is — the injection flaw must be fixed.

</details>

### [02-off-by-one](02-off-by-one.md) — 76.7/100 (new)
<details><summary>Full AI response</summary>

## Code Review: `src/pagination.js`

Two off-by-one errors in this small diff — both functions return incorrect results for valid inputs.

### 1. `getPage`: off-by-one on a 1-based page number (bug)

The docstring says `page` is 1-based, but the math treats it as 0-based:

```js
const start = page * pageSize;
```

For `page = 1`, `start = pageSize`, so the first `pageSize` items are skipped entirely. There is also no way to fetch the first page — `page = 0` "works" but contradicts the documented contract.

**Fix:**
```js
const start = (page - 1) * pageSize;
```

### 2. `totalPages`: `Math.floor` should be `Math.ceil` (bug)

```js
return Math.floor(items.length / pageSize);
```

With 10 items and `pageSize = 4`, this returns `2` instead of `3`, silently dropping the last page (which would contain 2 items). Any consumer looping `page = 1..totalPages()` will never reach those items.

**Fix:**
```js
return Math.ceil(items.length / pageSize);
```

### Additional issues worth addressing

- **No input validation / guard clauses:**
  - `page < 1` produces a negative `start` index; `Array.prototype.slice` with negative indices counts from the end of the array, so `getPage(items, 0, 10)` returns the *last* 10 items rather than an empty result — a surprising silent failure.
  - `pageSize <= 0`: `pageSize = 0` gives `NaN` from `totalPages` (division by zero → `Math.ceil(Infinity)` actually returns `Infinity"); negative page sizes give nonsensical slices. Consider throwing or clamping.
  - Non-array `items` will throw a `TypeError` at `.slice`/`.length` — fine to let it throw, but worth documenting or asserting.
- **Out-of-range pages:** `page > totalPages` returns `[]`, which is probably acceptable, but should be a documented/ tested behavior.
- **Missing tests:** Given two independent off-by-one errors slipped in, boundary tests are essential: empty array, exact multiple of `pageSize`, remainder page, `page = 1`, `page` beyond the end.

### Verdict

**Request changes.** The two off-by-one bugs mean the API as documented is unusable: page 1 can never be retrieved, and the final partial page is never counted. Suggested corrected implementation:

```js
function getPage(items, page, pageSize) {
  if (page < 1) return [];
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

function totalPages(items, pageSize) {
  if (pageSize <= 0) return 0;
  return Math.ceil(items.length / pageSize);
}
```

</details>

### [03-race-condition](03-race-condition.md) — 73.3/100 (new)
<details><summary>Full AI response</summary>

## Code Review

The implementation is clean and readable, but there are a few issues worth flagging before this ships:

### Issues

**1. `Snapshot()` exposes internal mutable state (medium–high)**
```csharp
public Dictionary<string, int> Snapshot()
{
    return counts;
}
```
This returns the live internal dictionary, not a snapshot. Callers can mutate it directly (e.g., `stats.Snapshot()["/foo"] = -1` or `.Clear()`), corrupting the stats — and it doesn't protect them from concurrent modification either. Options:
- Return `new Dictionary<string, int>(counts)` for a true copy.
- Better: return `IReadOnlyDictionary<string, int>` (a copy, since the mutable `Dictionary` also implements that interface but remains castable/mutable).

**2. Thread safety (context-dependent, likely high)**
The name `RequestStats` and "records one request" comment strongly suggest this will be called from concurrent request-handling threads. `Dictionary` is not thread-safe — concurrent `Inc` calls can corrupt the internal structure or lose increments. If this is used in a web/request context, consider:
- `ConcurrentDictionary<string, int>` with `AddOrUpdate(path, 1, (_, c) => c + 1)` / `GetOrAdd`, or
- A simple `lock` around `Inc`/`Count`/`Snapshot`, or
- `Interlocked`-style semantics on a per-key basis.
At minimum, document that the class is not thread-safe.

**3. Double dictionary lookups (minor)**
`ContainsKey` + indexer performs two lookups. `TryGetValue` is cleaner:
```csharp
public int Count(string path) => counts.TryGetValue(path, out var c) ? c : 0;
```
For `Inc`, `TryGetValue` + assign, or `CollectionsMarshal.GetValueRefOrAddDefault` (if targeting .NET where it's available) does it in one lookup.

**4. Null `path` handling (minor)**
`Dictionary` throws `ArgumentNullException` on a null key — fine if that's intended, but worth documenting or guarding with `ArgumentNullException.ThrowIfNull(path)` for a clearer error site.

**5. Style (nit)**
- `counts` could be `private readonly`.
- Consider file/class name consistency (`counter.cs` → `RequestStats.cs`).

### Summary
Main concern is `Snapshot()` leaking mutable internal state, plus the unspecified thread-safety contract for what looks like a request-tracking class. Address those two and this is good to go.

</details>

### [04-missing-error-handling](04-missing-error-handling.md) — 66.7/100 (new)
<details><summary>Full AI response</summary>

## Code Review

**Blocking issues**

1. **`writeBackup` leaks the file descriptor** — `fs.openSync` returns an fd that's never closed. If the write throws, or under repeated calls, this will exhaust file descriptors. Either wrap in try/finally with `fs.closeSync(fd)`, or simply use `fs.writeFileSync(path, data)`.

```ts
export function writeBackup(path: string, data: string): void {
  fs.writeFileSync(path, data)
}
```

2. **`loadConfig` returns unvalidated data typed as `AppConfig`** — `JSON.parse` returns `any`; the `AppConfig` return type is a lie. A config file missing `port` or with `port: "abc"` passes silently and fails downstream. Validate (e.g., zod, or manual checks) before returning:

```ts
const cfg = JSON.parse(raw) as unknown
if (typeof cfg !== "object" || cfg === null || typeof (cfg as any).port !== "number" || typeof (cfg as any).dbUrl !== "string") {
  throw new Error(`Invalid config at ${path}`)
}
return cfg as AppConfig
```

3. **`fetchRemoteConfig` has the same validation problem plus no HTTP error handling** — `res.json()` on a 404/500 may still resolve (e.g., an error body parsed as JSON) and be cast to `AppConfig`. Check `res.ok` first, and validate the payload shape as above:

```ts
if (!res.ok) throw new Error(`fetch ${url} failed: ${res.status}`)
```

**Non-blocking suggestions**

- `loadConfig`/`JSON.parse` will throw a raw `SyntaxError` on malformed JSON — consider wrapping with a contextual error message including `path`.
- `writeBackup` opens with "w" which truncates; if a backup should be atomic, write to a temp file and rename.
- Mixing sync (`readFileSync`, `openSync`/`writeSync`) and async (`fetch`) APIs is fine for a CLI, but if this module is used in a server context the sync calls will block the event loop — worth a comment or async variants.
- Style inconsistency: semicolons inside the interface but omitted elsewhere; pick one per project convention.
- No timeout on `fetch` — consider `AbortSignal.timeout(...)`.

**Verdict:** Request changes — the fd leak and the unchecked `AppConfig` casts are real defects; the rest is polish.

</details>

### [05-clean-refactor](05-clean-refactor.md) — 71.7/100 (new — FAIL: fabricated)
<details><summary>Full AI response</summary>

## Code Review

### Summary
The change refactors `OrderTotal` from an imperative loop to a LINQ `Sum` expression. The logic is equivalent for non-negative inputs, and the refactor is a reasonable simplification. A few points worth noting:

### Correctness
- ✅ `items.Sum(item => item.Price * item.Quantity)` correctly computes the subtotal for `decimal` operands.
- ✅ `subtotal * (1 + taxRate)` is mathematically identical to `total + total * taxRate`.
- ⚠️ Minor: `1 + taxRate` — the literal `1` is an `int`, but it will be implicitly converted to `decimal`, so this is correct. Using `1m` would be slightly more idiomatic/explicit:
  ```csharp
  return subtotal * (1m + taxRate);
  ```
- ⚠️ `Sum` on an empty list returns `0m`, same as the original loop — no behavioral change there.
- ⚠️ `items` null-check: neither version handles `null`; both will throw (`Sum` throws `ArgumentNullException`, the loop threw `NullReferenceException`). If null is a possibility, consider guarding or documenting it.

### Style / Readability
- The refactor is concise and idiomatic. `subtotal` is also a better name than `total` for the pre-tax amount.
- One readability note: the original computed `tax` explicitly, which made the two-step (subtotal → tax) structure obvious. The new one-liner is fine, but if tax needs to be exposed/logged later you'd have to recompute it. Not a blocker.

### Minor nit
- The diff shows `public class OrderCalculator` being removed and re-added identically — likely whitespace churn (e.g., line ending or BOM change). Worth checking the file didn't pick up inconsistent line endings or an unintended formatting change.

### Verdict
**Approve with minor suggestions** — use `1m` for clarity and verify the class declaration line wasn't altered unintentionally.

</details>

### [06-typos](06-typos.md) — 63.3/100 (new)
<details><summary>Full AI response</summary>

## Code Review

### Blocking / correctness concerns

1. **No validation of email or address** (`src/accounts.ts`) — `createAccount` validates `username` but passes `email` and `address` through unvalidated and un-normalized. If callers rely on this function to "normalize raw form input" (per the docstring), the docstring promises more than the code delivers. Either validate/normalize all fields or narrow the comment.

2. **`timeoutMs` in `DEFAULTS` is unused** — `opts.timeoutMs` can be passed but is never read; only `maxRetries` is consumed. Either use it or drop it from `DEFAULTS`/the options type.

3. **`getAdress` is a misspelled public API** — should be `getAddress`. Since this is a new export, fix it now before callers adopt the typo'd name. Also note it's trivial — is it needed at all, vs. just `account.address`?

### Non-blocking

4. **`retires` typo** — local variable should be `retries`. Also, the log line says "retrying up to X times" but there is no retry logic in the function; the message is misleading if this logs once. Either implement retries or reword the log.

5. **Misspelled user-facing error message** — "Username lenght must be at least 3 charaters." → "Username length must be at least 3 characters." This string may be shown to users, so it should be corrected.

6. **Comment typo** — "We recieve" → "We receive".

7. **`TEXT = "teh quick brown fox"`** — "teh" → "the". If this is test/placeholder text, consider whether it should be exported at all.

8. **Inconsistent spelling convention** — `LABEL = "Acme Colour Labs"` uses British "Colour" while the codebase uses `address`/American-style identifiers. Fine if it's a brand name, but worth confirming it's intentional.

9. **Missing semicolons / inconsistent style** — statements end without semicolons throughout the new code; confirm this matches project lint config.

10. **Missing return type annotation** — `createAccount` relies on inference; adding `: Account` would make the public API contract explicit.

### Summary

The code is functional but reads as unpolished: several typos leak into a public function name (`getAdress`), a user-facing error message, and a variable name. The bigger issues are semantic — the docstring overpromises normalization/validation, `timeoutMs` is dead config, and the log message implies retry behavior that doesn't exist. Recommend fixing the API name typo before merge and either implementing or removing the promised retry/timeout/validation behavior.

</details>

---
