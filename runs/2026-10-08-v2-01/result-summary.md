# v2 - 2026-10-08 — Detailed results

- Prompt: `prompts/code-review.v2.md`
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **87.5/100** (+3.6 vs v2-00)
- Hard fails: 03-race-condition — `fabricated` (review includes a code expression not present in the diff); 06-typos — `fabricated` (incorrect line references)

## What changed

The prompt is unchanged from the previous v2 run. Compared with the previously evaluated prompt version v1, the diff adds evidence-based review guidelines, exact changed `file:line` references and fixes, anti-speculation and behavior-equivalence checks, severity levels and focus areas, typo guidance, and the required Summary / Findings / Verdict structure.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 01-sql-injection | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | 0.0 |
| 02-off-by-one | 3 | 2 | 2 | 2 | 3 | 3 | 3 | 83.3 | -6.7 |
| 03-race-condition | 3 | 1 | 3 | 2 | 2 | 3 | 3 | 78.3 | +6.6 — FAIL |
| 04-missing-error-handling | 3 | 3 | 2 | 3 | 2 | 3 | 3 | 91.7 | +16.7 |
| 05-clean-refactor | 3 | 2 | 3 | 2 | 3 | 3 | 3 | 88.3 | -11.7 |
| 06-typos | 3 | 2 | 2 | 2 | 3 | 3 | 3 | 83.3 | +16.6 — FAIL |

Overall delta: +3.6 points from v2-00's 83.9/100. Fixture totals are rounded to one decimal before taking the mean; per-fixture deltas compare these rounded totals with the most recent previous changelog entry, v2-00.

## Typo recall

| Category | Found / total |
|---|---:|
| misspelling | 1/1 |
| swap | 3/3 |
| missing_letter | 2/2 |

## Observations / next changes

- The strongest review was SQL injection (100.0); the I/O/config review also scored 91.7 by finding all three expected concerns. The run's two hard fails were fabricated content: the concurrency review quoted `counts[path]++/= 1`, which is absent from the patch, and the typo review cited several incorrect lines.
- The principal regressions from v2-00 were pagination (-6.7) and the clean refactor (-11.7). Pagination added an unsupported out-of-range-page complaint and downgraded the main issue's severity. The clean-refactor review introduced an unseeded style nit. The greatest gains were error handling (+16.7) and typos (+16.6), with all typo categories at full recall.
- Across fixtures, line-reference accuracy remains inconsistent; wrong references reduced actionability and, in the typo fixture, caused a hard fail. Extra concerns about unrequested boundary behavior, unused options, and style can also reduce precision.
- Suggested next prompt changes:
  1. Require every cited line number and code excerpt to be checked against the new-file line numbering in the supplied diff; omit a finding if the precise location cannot be verified.
  2. In concurrency reviews, cite the actual shared-state operations and address `Inc`, `Count`, and `Snapshot` separately; do not paraphrase code in a way that changes the quoted expression.
  3. Suppress concerns that depend on unprovided contracts (such as out-of-range pagination or whether an option should be used) and avoid non-actionable style nits on clean refactors.
  4. Preserve severity distinctions: rate demonstrated user-impacting defects by their actual impact, and keep cosmetic typo findings below exported API and user-facing issues.

## Per-fixture results

### [01-sql-injection](01-sql-injection.md) — 100.0/100 (0.0)
<details><summary>Full AI response</summary>

## Summary
The new stored procedure builds a SQL statement by concatenating an unsanitized user-supplied parameter, introducing a direct SQL injection vulnerability.

## Findings

- [Critical] src/users.sql:8-10 — SQL injection via string concatenation into dynamic SQL
  ```sql
  SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
  EXEC sp_executesql @query;
  ```
  **Impact:** `@name` is interpolated verbatim, so input like `'; DROP TABLE users; --` (or exfiltration/UNION-based payloads) executes arbitrary SQL with the caller's privileges. Any caller passing user input here enables full SQLi.
  **Fix:** Either drop dynamic SQL entirely (`SELECT id, name, email FROM users WHERE name = @name;`) or parameterize it: `EXEC sp_executesql N'SELECT id, name, email FROM users WHERE name = @name', N'@name nvarchar(255)', @name;`

## Verdict
Request changes

</details>

### [02-off-by-one](02-off-by-one.md) — 83.3/100 (-6.7)
<details><summary>Full AI response</summary>

## Summary
New pagination helpers contain an off-by-one indexing bug and an incorrect total-pages calculation for non-even divisions; overall risk is moderate.

## Findings

[Medium] src/pagination.js:6 — `getPage` computes `start` as `page * pageSize`, but the docstring says the page is 1-based.

```js
 * Returns the items for a 1-based page number.
 */
function getPage(items, page, pageSize) {
  const start = page * pageSize;
```

Impact: `getPage(items, 1, 10)` returns items 10–19 instead of 0–9, skipping the first page entirely and leaving the first `pageSize` items unreachable via page 1. Fix: `const start = (page - 1) * pageSize;`

[Medium] src/pagination.js:16 — `totalPages` uses `Math.floor`, undercounting pages when `items.length` isn't a multiple of `pageSize`.

```js
return Math.floor(items.length / pageSize);
```

Impact: e.g., 25 items with pageSize 10 reports 2 pages, dropping the last 5 items so they can never be reached. Fix: `Math.ceil(items.length / pageSize)`.

[Low] src/pagination.js:6 — `getPage` with a 1-based API will silently return an empty array for `page` beyond `totalPages` (or for page 0/negative inputs, slice with negative indices yields surprising results). If callers can pass out-of-range pages, clamp or document the behavior. Low severity since it's a boundary/doc concern, not a demonstrated defect.

## Verdict
Request changes

</details>

### [03-race-condition](03-race-condition.md) — 78.3/100 (+6.6 — FAIL: fabricated)
<details><summary>Full AI response</summary>

## Summary
Adds a request counter that mutates a non-thread-safe `Dictionary` from concurrent `Task.Run` calls, causing races and potentially lost counts or corruption.

## Findings

**[High] src/counter.cs:35 — unsynchronized concurrent mutation of `Dictionary<string,int>`**

```csharp
await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));
```

`stats.Inc(p)` runs `counts.ContainsKey(path)` then `counts[path]++/= 1` on multiple thread-pool threads concurrently. `Dictionary` is not thread-safe: the check-then-act sequence loses increments (two threads both see "missing" and write 1), and concurrent writes can corrupt internal state or throw `IndexOutOfRangeException`/`InvalidOperationException` during rehash. `Count`/`Snapshot` can also read during a resize. Fix: use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, v) => v + 1)`, or serialize all access with a lock.

**[Medium] src/counter.cs:23 — `Snapshot()` returns the live mutable dictionary**

```csharp
public Dictionary<string, int> Snapshot()
{
    return counts;
}
```

Callers receive the internal dictionary, so they can mutate it unsynchronized and enumerate it while `Inc` is writing (throws `InvalidOperationException` during enumeration under concurrent mutation). Fix: return a copy (`new Dictionary<string,int>(counts)` under the same lock) or `IReadOnlyDictionary` built from a snapshot; with `ConcurrentDictionary`, use `ToDictionary`/`ToArray`.

## Verdict
Request changes.

</details>

### [04-missing-error-handling](04-missing-error-handling.md) — 91.7/100 (+16.7)
<details><summary>Full AI response</summary>

## Summary
Adds config loading, backup writing, and remote config fetching helpers; the main risk is a file-descriptor leak in `writeBackup` plus unvalidated/unchecked JSON in the config loaders.

## Findings

[Medium] src/config.ts:16 — `writeBackup` never closes the file descriptor
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
`fs.openSync` returns a descriptor that is never released with `fs.closeSync(fd)`. Repeated calls leak file descriptors, which can eventually exhaust the process's fd limit, and on some platforms data may not be fully flushed until close. Fix: wrap in try/finally and call `fs.closeSync(fd)`, or simply use `fs.writeFileSync(path, data)` which handles open/write/close atomically.

[Low] src/config.ts:22 — `fetchRemoteConfig` ignores HTTP error status
```ts
const res = await fetch(url)
return res.json()
```
`fetch` does not throw on 4xx/5xx, so an error response body (e.g., an HTML error page) will either fail JSON parsing with an opaque error or be returned as a bogus `AppConfig`. Fix: check `res.ok` and throw a descriptive error before parsing.

[Low] src/config.ts:9 — `loadConfig` returns unvalidated JSON as `AppConfig`
```ts
const cfg = JSON.parse(raw)
return cfg
```
`JSON.parse` returns `any`; a config file missing `port`/`dbUrl` or with wrong types silently satisfies the `AppConfig` contract, surfacing failures far from the load site. Fix: validate the parsed shape (e.g., a schema check or explicit field checks) before returning. Same concern applies to `fetchRemoteConfig` (src/config.ts:22).

## Verdict
Request changes

</details>

### [05-clean-refactor](05-clean-refactor.md) — 88.3/100 (-11.7)
<details><summary>Full AI response</summary>

## Summary
A behavior-equivalent refactor of `OrderTotal` that replaces a manual accumulation loop with LINQ `Sum` and combines the tax calculation into a single expression.

## Findings

Both implementations produce identical results for all inputs:

- Old: `total + total * taxRate` = `total * (1 + taxRate)` — identical to new `subtotal * (1 + taxRate)` for `decimal` arithmetic.
- New `items.Sum(item => item.Price * item.Quantity)` is valid only if `Price * Quantity` is `decimal` — given the old code accumulated into a `decimal` without casts, this holds; if the product were `int`/`double`, `Sum` would return a different numeric type and fail to compile against the `decimal` return type, so the compiler catches any mismatch.
- Null `items` throws in both versions (just a different exception type), and an empty list returns `0m` in both.

None.

**Low (nit, not a defect):** `src/totals.cs:7` — `subtotal * (1 + taxRate)` uses `1`, an `int` literal; the compiler promotes it to `decimal` correctly, but `1m` would be marginally clearer. Optional.

## Verdict
Approve

</details>

### [06-typos](06-typos.md) — 83.3/100 (+16.6 — FAIL: fabricated)
<details><summary>Full AI response</summary>

## Summary
The change adds an account creation module with mostly functional code, but contains several typos — including in an exported function name and a user-facing error message — plus a docstring that describes behavior the code doesn't implement.

## Findings

- **[Medium] src/accounts.ts:39 — Typo in exported identifier `getAdress`**
  ```ts
  export function getAdress(account: Account): string {
  ```
  `getAdress` should be `getAddress`. Exported API names are hard to rename later without breaking consumers. Fix: rename to `getAddress` before release.

- **[Low] src/accounts.ts:23 — Misspellings in user-facing error message**
  ```ts
  throw new Error("Username lenght must be at least 3 charaters.")
  ```
  "lenght" → "length", "charaters" → "characters". This string is shown to users. Fix: `throw new Error("Username length must be at least 3 characters.")`

- **[Low] src/accounts.ts:15 — Docstring claims behavior not implemented; also a comment typo**
  ```ts
  /**
   * Creates a new account and sends a welcome email.
   * We recieve the raw form input and normalize it.
   */
  ```
  The function never sends a welcome email (only logs), so the doc comment is misleading. Also "recieve" → "receive". Fix: either implement the email send or correct the comment.

- **[Low] src/accounts.ts:21 — Typo'd local variable `retires`**
  ```ts
  const retires = opts.maxRetries ?? DEFAULTS.maxRetries
  ```
  Used consistently (line 35), so functionally fine, but reads as "retires" rather than "retries". Fix: rename to `retries`.

- **[Low] src/accounts.ts:10 — `timeoutMs` option accepted but never used**
  ```ts
  const DEFAULTS = { maxRetries: 3, timeoutMs: 5000 }
  ```
  `opts.timeoutMs` is silently accepted and ignored. Fix: remove it from `DEFAULTS` or use it, so callers don't assume it has an effect.

- **[Low] src/accounts.ts:43 — Typo in public string literal**
  ```ts
  export const TEXT = "teh quick brown fox"
  ```
  "teh" → "the". Fix only if this string is user-facing; otherwise harmless.

## Verdict
Request changes — primarily to fix the exported `getAdress` name and the user-facing error message before this ships.

</details>

---
