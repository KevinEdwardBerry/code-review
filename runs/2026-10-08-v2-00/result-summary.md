# v2 - 2026-10-08 — Detailed results

- Prompt: `prompts/code-review.v2.md`
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **83.9/100** (+13.3 vs v1)
- Hard fails: 03-race-condition — `missed_critical` (`unlocked_read`); 06-typos — `fabricated` (incorrect line references)

## What changed

Compared with v1, v2 adds explicit evidence-based review guidelines, asks for exact changed file:line references and fixes, limits speculative concerns, calls out behavior-equivalent refactors, defines severity levels and focus areas, gives typo-specific priorities, and mandates Summary / Findings / Verdict headings and finding order. The direct prompt diff is `prompts/code-review.v1.md` → `prompts/code-review.v2.md`.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 01-sql-injection | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +28.3 |
| 02-off-by-one | 3 | 3 | 2 | 2 | 3 | 3 | 3 | 90.0 | +13.3 |
| 03-race-condition | 2 | 3 | 1 | 2 | 2 | 3 | 3 | 71.7 | -1.6 — FAIL |
| 04-missing-error-handling | 1 | 3 | 3 | 2 | 3 | 3 | 3 | 75.0 | +8.3 |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +28.3 |
| 06-typos | 3 | 1 | 1 | 1 | 3 | 3 | 3 | 66.7 | +3.4 — FAIL |

Overall delta: +13.3 points from v1's 70.6/100. Fixture totals are weighted using rubric weights and rounded to one decimal before computing the mean. Delta compares rounded fixture totals with the most recent prior changelog entry (v1).

## Typo recall

| Category | Found / total |
|---|---:|
| misspelling | 1/1 |
| swap | 3/3 |
| missing_letter | 2/2 |

## Observations / next changes

- The new format, evidence, and no-speculation guidance coincided with strong gains on SQL injection and the clean-refactor fixture; the v1 fabricated clean-refactor hard fail did not recur.
- The race review identified the exposed snapshot and an `Inc` race, but missed unsynchronized reads in `Count`; the judge marked `missed_critical`. The error-handling review found the descriptor leak but missed unchecked HTTP status and config validation. The three missed IDs are `unlocked_read`, `fetch_no_status`, and `no_validation`; `unlocked_read` triggers the race-condition hard fail, while the error-handling fixture has no hard-fail flags.
- All six typo items were found (100% recall for each typo category), but every finding was rated Low, line references were frequently inaccurate, and an unsubstantiated `timeoutMs` finding lowered precision and triggered the `fabricated` hard fail. This is also the only new false positive.
- Suggested next prompt changes:
  1. Add a resource-lifecycle and response-validation checklist for newly added I/O: verify handles are closed on success/error, check HTTP success status, and validate parsed external data; require each observation to cite the exact changed line.
  2. For code that is inherently shared or concurrent in the fixture, explicitly inspect read, write, and snapshot paths for synchronization together; distinguish proven thread-safety defects from assumptions about unknown callers.
  3. For typo findings, preserve the specified impact ranking and verify every file:line points to the exact quoted token; omit unused options or other concerns unless the diff proves they are defective.

## Per-fixture results

### [01-sql-injection](01-sql-injection.md) — 100.0/100 (+28.3)
<details><summary>Full AI response</summary>

## Summary
The new `FindUserByName` procedure builds a SQL statement by concatenating the `@name` parameter directly into a query string, introducing a SQL injection vulnerability.

## Findings

**[Critical] src/users.sql:9-11 — SQL injection via string concatenation in dynamic SQL**

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

Impact: `@name` is interpolated verbatim into the query string. A caller passing a value like `x' OR '1'='1` (or worse, `x'; DROP TABLE users; --`) can read arbitrary rows or execute arbitrary statements. Any user input routed into this parameter is exploitable.

Fix: Either use a plain static query (no dynamic SQL needed here):

```sql
CREATE OR ALTER PROCEDURE FindUserByName
    @name nvarchar(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id, name, email FROM users WHERE name = @name;
END
```

or, if dynamic SQL is truly required, parameterize it:

```sql
EXEC sp_executesql
    N'SELECT id, name, email FROM users WHERE name = @name',
    N'@name nvarchar(255)',
    @name = @name;
```

## Verdict
Request changes

</details>

### [02-off-by-one](02-off-by-one.md) — 90.0/100 (+13.3)
<details><summary>Full AI response</summary>

## Summary
Adds pagination helpers containing an off-by-one indexing bug and a page-count truncation bug.

## Findings

**[High] src/pagination.js:6 — `getPage` uses 0-based math despite documented 1-based API**

```js
 * Returns the items for a 1-based page number.
 */
function getPage(items, page, pageSize) {
  const start = page * pageSize;
```

With the documented 1-based contract, `getPage(items, 1, 10)` returns `items.slice(10, 20)` — the second page. `getPage(items, 0, ...)` would return the first page, and a caller passing `page === totalPages` gets the wrong slice entirely. Fix: `const start = (page - 1) * pageSize;`

**[High] src/pagination.js:15 — `totalPages` truncates partial last page**

```js
  return Math.floor(items.length / pageSize);
```

For `items.length = 25, pageSize = 10`, this returns 2 instead of 3, dropping the last 5 items from any page enumeration. Fix: `return Math.ceil(items.length / pageSize);`

## Verdict
Request changes

</details>

### [03-race-condition](03-race-condition.md) — 71.7/100 (-1.6 — FAIL: missed_critical)
<details><summary>Full AI response</summary>

## Summary
New `RequestStats` class for per-path request counters; low overall risk with one encapsulation defect in `Snapshot` and minor inefficiencies.

## Findings

[Medium] src/counter.cs:25-28 — `Snapshot()` returns the internal mutable dictionary
```csharp
public Dictionary<string, int> Snapshot()
{
    return counts;
}
```
Callers receive a live reference to the private `counts` map, so they can mutate (or clear) it without going through `Inc()`, corrupting the counters — the opposite of what "snapshot" implies, and reads/writes on that shared reference also race with `Inc()` if used across threads. Fix: return a copy, e.g. `return new Dictionary<string, int>(counts);`.

[Low] src/counter.cs:10-13 — Double dictionary lookup in `Inc` (`ContainsKey` + indexer)
```csharp
if (counts.ContainsKey(path))
    counts[path]++;
else
    counts[path] = 1;
```
Performs two hash lookups per increment and, in a multithreaded context, the check-then-act is not atomic. Fix: `counts.TryGetValue(path, out var c); counts[path] = c + 1;` — one lookup, same result. If `Inc` is called concurrently, wrap in a lock or use `ConcurrentDictionary` (the diff itself provides no synchronization, so flag only if callers are concurrent).

[Low] src/counter.cs:17-20 — `Count` also does two lookups via `ContainsKey` + indexer; use `counts.TryGetValue(path, out var c) ? c : 0`.

## Verdict
Approve with nits

</details>

### [04-missing-error-handling](04-missing-error-handling.md) — 75.0/100 (+8.3)
<details><summary>Full AI response</summary>

## Summary
Adds config loading, a synchronous backup-file writer, and a remote config fetcher to `src/config.ts`; low overall risk, with one resource-leak defect.

## Findings

[Medium] src/config.ts:21 — `writeBackup` never closes the file descriptor
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
Each call leaks an open fd; under repeated invocation (e.g., periodic backups) the process can exhaust its file-descriptor limit (`EMFILE`). Fix: call `fs.closeSync(fd) (ideally in a try/finally so an error in `writeSync` doesn't skip the close), or simply use `fs.writeFileSync(path, data) which handles open/write/close itself:
```ts
fs.writeFileSync(path, data)
```

## Verdict
Request changes

</details>

### [05-clean-refactor](05-clean-refactor.md) — 100.0/100 (+28.3)
<details><summary>Full AI response</summary>

## Summary
Low-risk refactor that replaces a manual accumulation loop with `Enumerable.Sum` and algebraically simplifies the tax computation; behavior is equivalent for the same types.

## Findings
None.

Notes considered and dismissed:
- `items.Sum(item => item.Price * item.Quantity)` computes the same running total as the removed loop (decimal `Sum` accumulates with identical per-element multiplication and ordering), and `subtotal * (1 + taxRate)` equals `subtotal + subtotal * taxRate` for decimal arithmetic at the same scale.
- `items == null` throws `ArgumentNullException` instead of `NullReferenceException`; this is a behavior difference only in exception type, not a demonstrated defect.
- Nit (low, optional): `1 + taxRate` — the literal `1` is int, but it is implicitly converted to decimal here, so no defect.

## Verdict
Approve

</details>

### [06-typos](06-typos.md) — 66.7/100 (+3.4 — FAIL: fabricated)
<details><summary>Full AI response</summary>

## Summary
Low-risk addition of an `Account` type and `createAccount` helper; no functional defects, but several typos in exported identifiers and user-facing strings.

## Findings

[Low] src/accounts.ts:41 — Typo in exported function name `getAdress`
```
export function getAdress(account: Account): string {
```
Exported API names are the highest-impact typo category; renaming later is a breaking change for consumers. Fix: rename to `getAddress` before this ships.

[Low] src/accounts.ts:23 — Misspellings in user-facing error message
```
throw new Error("Username lenght must be at least 3 charaters.")
```
`lenght` → `length`, `charaters` → `characters`. Users will see this string. Fix: `throw new Error("Username length must be at least 3 characters.")`

[Low] src/accounts.ts:43 — Typo in exported public string
```
export const TEXT = "teh quick brown fox"
```
`teh` → `the`. If this is test/placeholder text it can be ignored; otherwise correct it.

[Low] src/accounts.ts:16,33 — Local typos `recieve` and `retires`
```
 * We recieve the raw form input and normalize it.
  const retires = opts.maxRetries ?? DEFAULTS.maxRetries
```
Comment typo `recieve` → `receive`; local variable `retires` → `retries` (also used in the log line). Cosmetic but trivially fixable.

[Low] src/accounts.ts:9 — `timeoutMs` option accepted but never used
```
const DEFAULTS = {
  maxRetries: 3,
  timeoutMs: 5000
}
```
`opts.timeoutMs` is part of the accepted options type yet ignored, which may mislead callers into thinking it has an effect. Fix: either use it (e.g., in the retry/timeout logic) or remove it from `DEFAULTS`.

## Verdict
Approve with nits

</details>

---
