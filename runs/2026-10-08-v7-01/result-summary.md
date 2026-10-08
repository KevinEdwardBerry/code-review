# v7 - 2026-10-08 — Detailed results

- Prompt: `prompts/code-review.v7.md`
- Reviewer: subagent_explore (unknown concrete model)
- Judge: subagent_general (unknown concrete model)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **75.3/100** (-5.0 vs v7-00)
- Hard fails: none

## What changed
This is a re-run of v7; the prompt file `prompts/code-review.v7.md` is unchanged from the previous v7-00 run. The original v6→v7 diff is shown below for context.

```diff
--- prompts/code-review.v6.md	2026-10-07 18:03:15
+++ prompts/code-review.v7.md	2026-10-08 10:15:26
@@ -1,113 +1,4 @@
 You are a senior software engineer performing a thorough code review of the change below.
 
-## Goal and scope
-Find every substantiated, actionable defect introduced or exposed by the change, assess its impact, and suggest a concrete fix. Review every file and hunk; do not stop after finding one issue. The checklist is illustrative, not exhaustive:
-- Correctness, edge cases, API contracts, callers, compatibility, and data or configuration changes.
-- Security, privacy, authorization, and untrusted input.
-- State, concurrency, transactions, data integrity, error handling, recovery, and resource lifetimes.
-- Performance and scalability.
-- Tests, deployment, and operational behavior when they affect correctness or safety.
-- Maintainability and naming when they create a concrete defect or meaningful future risk, including behavior-changing or public API typos.
-
-Trace relevant surrounding code, contracts, callers, tests, and configuration when available; distinguish regressions from pre-existing issues. If context is missing, do not present assumptions as facts.
-
-## Severity
-Rank by concrete impact. Downgrade if the impact is theoretical or only occurs on edge/failure/remainder cases.
-- **critical**: exploitable vulnerability, data loss, or crash in normal use (e.g. SQL injection, auth bypass, unhandled exception on the common path, a race that corrupts persisted state).
-- **high**: documented behavior is wrong on common, typical inputs; a missing invariant guaranteed to fail for ordinary callers.
-- **medium**: incorrect behavior limited to edge/remainder/failure cases, or costly public-API defects that are expensive to fix later.
-- **low**: minor user-facing issue or defensive improvement with a concrete benefit (e.g. user-facing error-message typo, unused import).
-- **nit**: non-actionable or cosmetic observation (e.g. formatting, comment typo, consistent local abbreviation).
-
-### Severity examples
-- A documented 1-based parameter treated as 0-based is **high** because every typical caller gets the wrong result.
-- A count or total helper that drops the final partial result (e.g. floors a division that should be ceilinged) is **medium**.
-- User input concatenated directly into an executable query or command string in a reachable code path is **critical**.
-- A non-reachable, malformed snippet that merely repeats a vulnerable pattern (e.g. leftover documentation or test data) is **low/nit**, not a separate critical or high finding.
-- A missing status or error check on a remote or I/O call is **medium** because it only matters on failure paths.
-
-## Citing exact `file:line`
-Every finding must include an exact `file:line` citation in its title (or `file:start-end` if it spans adjacent lines). Cite the new-file line number on which the defect occurs, not the function header or hunk start. Derive it from the `@@` hunk header.
-
-For a hunk like:
-```
-@@ -1,4 +5,5 @@
- def load():
-     raw = open("x")
--    data = raw.read()
--    return data
-+    content = raw.read()
-+    raw.close()
-+    return content
-```
-`+5,5` means the hunk starts at new-file line 5. Count every hunk line without the leading `+`, `-`, or space markers:
-- 5 `def load():` (context)
-- 6 `    raw = open("x")` (context)
-- 7 `    content = raw.read()` (added)
-- 8 `    raw.close()` (added)
-- 9 `    return content` (added)
-
-For a second hunk like:
-```
-@@ -0,0 +1,5 @@
-+app:
-+  host: localhost
-+  port: 3306
-+  ssl: true
-+  timeout: 30
-```
-`+1,5` means new-file line 1 is `app:` and the file runs through line 5; `port: 3306` is at line 3 and `timeout: 30` is at line 5.
-
-## Rules
-- Report every distinct, actionable issue attributable to the change; there is no finding limit. Do not omit a real issue because it falls outside the checklist or another issue is more prominent.
-- Judge validation, performance, compatibility, and other concerns by concrete impact: do not dismiss them as optional, and do not report generic improvements without a demonstrated failure mode or meaningful risk.
-- Quote the relevant line(s) and explain the impact. Context may support a finding, but do not report pre-existing issues.
-- Do not invent or speculate. If the change is sound, say so and report only genuine nits (or none).
-- Order findings by severity, keep distinct defects separate, and give each a concrete fix. Be concise without sacrificing coverage.
-
-### Concurrency
-When a change introduces shared mutable state, review every method, property, getter, and read-only accessor that touches that state — not just mutators. Read-only paths need the same synchronization as writes; an unsynchronized read against a concurrent write can corrupt a non-thread-safe collection or throw (e.g. concurrent read and write to a shared map or list).
-
-### Behavior-preserving rewrites
-A clean, mathematically-equivalent rewrite is to be treated as behavior-preserving unless a reachable, concrete failure case is demonstrated. If no real defect is shown, the verdict must be `approve` or `approve with nits`, not `request changes`.
-
-**Worked example:** A diff that replaces
-```
-if user is None:
-    return "guest"
-return user.name
-```
-with
-```
-return "guest" if user is None else user.name
-```
-is a behavior-preserving refactor. Do not flag the conditional expression, the formatting, or any added `using` / `import` as a defect. Only point out genuine nits with a concrete failure mode.
-
-### Typos
-Check every text token in the diff — identifiers, keys, API names, user-facing strings, literal string data, and comments — for typos. A typo in an identifier, key, API name, or user-facing string is a bug. A typo in a comment is a nit. A typo in literal string data is actionable only when the string is user-facing or otherwise semantically meaningful; literal test data, fixtures, and example strings are not actionable even if misspelled.
-
-Do not flag terms in the Known acceptable typos list, brand names, British/variant spellings in proper names, or consistently-used local abbreviations.
-
-## Known acceptable typos
-If a project-specific exception list is provided below, do not flag those terms. If the list is absent or empty, use the defaults in the Typos rule.
-
-{{TYPO_EXCEPTIONS}}
-
-## Output format
-### Summary
-One or two sentences on what the change does and your overall assessment.
-
-### Findings
-Ordered from highest to lowest severity. For each:
-- **[severity] file:line - short title**
-  - Problem: what is wrong and why it matters.
-  - Fix: concrete suggestion.
-  - Code snippet: quote the relevant line(s) from the diff.
-
-If there are none, write "No issues found."
-
-### Verdict
-One of: `approve`, `approve with nits`, `request changes`.
-
 ## Diff
 {{DIFF}}
```

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-sql-injection | 3 | 2 | 3 | 2 | 3 | 2 | 2 | 85.0 | +1.7 |
| 02-off-by-one | 3 | 1 | 1 | 2 | 3 | 2 | 2 | 68.3 | -18.4 |
| 03-race-condition | 3 | 2 | 3 | 2 | 3 | 2 | 2 | 85.0 | +10.0 |
| 04-missing-error-handling | 3 | 3 | 1 | 2 | 3 | 2 | 3 | 83.3 | +3.3 |
| 05-clean-refactor | 3 | 1 | 1 | 2 | 3 | 2 | 2 | 68.3 | -13.4 |
| 06-typos | 3 | 1 | 1 | 2 | 2 | 1 | 1 | 61.7 | -13.3 |


### Typo recall (fixture 06)

| Category | Found/Total |
|---|---|
| misspelling | 1/1 |
| swap | 2/2 |
| missing_letter | 2/2 |

## Observations / next changes
### Patterns in misses and false positives
- The minimal v7 prompt still achieves full recall on every fixture, but it loses precision and severity calibration without explicit guidance.
- 02 `totalPages` is over-ranked to high (expected medium) and the review flags the must-not-flag `module.exports` item plus speculative tests/inconsistency.
- 04 `fd_leak` and `no_validation` are over-ranked to high (expected medium/low).
- 05 (clean refactor) invents a false rounding/behavior difference and pads the findings with non-issues instead of an `approve`/`approve with nits` verdict.
- 06 finds every typo but also flags must-not-flag `teh` and `Colour`, buries the public-API `getAdress` typo under non-typo concerns, and lacks a clear severity ordering.
- Exact `file:line` citations are missing across all fixtures.

### Suggested prompt changes
1. Restore the `## Severity` section with concrete definitions and examples to stop over-ranking acceptable extras.
2. Restore the `## Citing exact file:line` requirement and a worked `@@` hunk-header example.
3. Restore the concurrency, behavior-preserving-rewrite, and typo must-not-flag rules from v6.
4. Restore the Summary/Findings/Verdict output format and forbid emojis and extra sections.

## Per-fixture results
### 01-sql-injection

- [01-sql-injection.md](01-sql-injection.md)

<details><summary>Full AI response for 01-sql-injection</summary>

# Code Review: `src/users.sql`

## Critical: SQL Injection Vulnerability

The `FindUserByName` stored procedure builds a query via string concatenation and executes it with `sp_executesql`. This is a textbook SQL injection flaw — the `@name` parameter is injected unescaped into the query text.

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

An attacker passing `@name = ' OR '1'='1'` (or worse, `'; DROP TABLE users;--`) can exfiltrate data or execute arbitrary statements. Note that wrapping the logic in a stored procedure provides **no** protection here — the vulnerability is created by the dynamic SQL itself.

### Fix options

**Option 1 (preferred):** Dynamic SQL isn't needed at all — this is a static query:

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

**Option 2:** If dynamic SQL were genuinely required, parameterize `sp_executesql` instead of concatenating:

```sql
EXEC sp_executesql
    N'SELECT id, name, email FROM users WHERE name = @name',
    N'@name nvarchar(255)',
    @name = @name;
```

## Minor issues

- `@query` is declared `nvarchar(1023)` — an odd size; if dynamic SQL is kept, `nvarchar(max)` avoids silent truncation.
- No error handling / `TRY...CATCH` or transaction semantics — not strictly needed for a single SELECT, but worth noting if the proc grows.
- `SELECT id, name, email` — good that it's explicit columns rather than `SELECT *`.
- Trailing `GO` is fine as a batch separator for SQL Server tooling; just confirm it's compatible with whatever migration runner applies this file.

## Verdict

**Request changes.** The procedure must be rewritten to use a parameterized query before merge.
</details>

### 02-off-by-one

- [02-off-by-one.md](02-off-by-one.md)

<details><summary>Full AI response for 02-off-by-one</summary>

## Code Review: `src/pagination.js`

## Summary
The change adds two pagination helpers, `getPage` and `totalPages`. Both contain logic bugs that contradict their documented behavior.

## Findings

### 1. `getPage` — off-by-one error (high severity)
The docstring says the page number is **1-based**, but the implementation treats it as 0-based:

```js
const start = page * pageSize;   // page 1 → start at index pageSize
```

With `page = 1`, `pageSize = 10`, this returns items 10–19, skipping the first 10 entirely. Page 1 should begin at index 0.

**Fix:**
```js
const start = (page - 1) * pageSize;
```

### 2. `totalPages` — truncates instead of rounding up (high severity)

```js
return Math.floor(items.length / pageSize);
```

`Math.floor` drops the final partial page. With 25 items and `pageSize = 10`, it returns `2` instead of `3`, so the last 5 items are unreachable.

**Fix:**
```js
return Math.ceil(items.length / pageSize);
```

### 3. No input validation (medium severity)
- `pageSize <= 0`: `totalPages` returns `Infinity` (or `NaN` for 0); `getPage` behaves nonsensically.
- `page < 1`: `getPage` slices from a negative index, returning the *end* of the array — a silent, surprising result.
- `items` not an array (or null/undefined) throws a `TypeError`.
- Non-integer `page`/`pageSize` values produce fractional slice indices (JS tolerates this by truncation, but it's likely unintended).

Recommend either validating and throwing `RangeError`/`TypeError`, or clamping (`Math.max(1, page)`, etc.) — and documenting which contract is chosen.

### 4. Inconsistency between the two functions
Even after fixing both bugs, consider `getPage(items, totalPages(items, size) + 1, size)`: `slice` returns `[]` for out-of-range start, which is fine, but nothing links an out-of-range `page` to a defined behavior. Worth documenting or testing.

### 5. Style/minor
- `module.exports` (CommonJS) — fine if the codebase is CJS, but confirm consistency with other files.
- No tests accompany the change; these are exactly the kinds of functions where boundary tests (`page=1`, last partial page, empty array) would have caught both bugs.

## Suggested corrected version

```js
function getPage(items, page, pageSize) {
  if (!Array.isArray(items)) throw new TypeError('items must be an array');
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError('pageSize must be a positive integer');
  if (!Number.isInteger(page) || page < 1) throw new RangeError('page must be a positive integer');
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

function totalPages(items, pageSize) {
  if (!Array.isArray(items)) throw new TypeError('items must be an array');
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError('pageSize must be a positive integer');
  return Math.ceil(items.length / pageSize);
}
```

## Verdict
**Request changes.** The two core bugs (findings 1 and 2) mean the functions are incorrect for their primary use case and would silently serve wrong data — e.g., page 1 shows the second page of results and the last page is never shown. Validation (finding 3) should at minimum be a deliberate, documented decision.
</details>

### 03-race-condition

- [03-race-condition.md](03-race-condition.md)

<details><summary>Full AI response for 03-race-condition</summary>

# Code Review

## Critical Issues

### 1. Thread safety — race conditions on `counts`
`RequestStats` looks like a request-metrics type that will almost certainly be called from concurrent request handlers. `Dictionary<K,V>` is **not** thread-safe for concurrent reads *and* writes:

```csharp
if (counts.ContainsKey(path))
    counts[path]++;
else
    counts[path] = 1;
```

Two threads calling `Inc` on the same new path can lose updates, and worse, concurrent `Inc`/`Snapshot`/`Count` calls while the dictionary is rehashing can corrupt internal state or throw. If this type is ever used from a shared/server context, you need synchronization:

- Simplest: wrap all access in a `lock` on a private object.
- Alternative: `ConcurrentDictionary<string, int>` with `AddOrUpdate(path, 1, (_, c) => c + 1)` — but note `Snapshot()` must then materialize a copy anyway (see issue 2).

### 2. `Snapshot()` leaks internal mutable state
```csharp
public Dictionary<string, int> Snapshot()
{
    return counts;
}
```
This returns the live dictionary. Callers can:
- Mutate it (corrupting the stats — e.g., `Snapshot()["/x"] = -999`),
- Enumerate it while another thread is mutating it → `InvalidOperationException` under concurrency, or
- Hold a reference that silently changes over time, defeating the purpose of a "snapshot".

Return a copy instead:

```csharp
public Dictionary<string, int> Snapshot() => new Dictionary<string, int>(counts);
// or better, an IReadOnlyDictionary<string, int>
```

## Minor Issues

### 3. Double lookups are wasteful
`Inc` does up to three dictionary lookups (`ContainsKey`, indexer get/set); `Count` does two. Simplify:

```csharp
public void Inc(string path)
{
    counts.TryGetValue(path, out int c);
    counts[path] = c + 1;
}

public int Count(string path)
    => counts.TryGetValue(path, out int c) ? c : 0;
```

### 4. Mutable `counts` field should be `readonly`
```csharp
private readonly Dictionary<string, int> counts = new();
```

### 5. `path` is never validated
`Inc(null)`/`Count(null)` will throw `ArgumentNullException` from the dictionary anyway, so behavior is consistent, but it's worth deciding whether null/empty paths should be rejected explicitly.

### 6. File location / naming convention
`src/counter.cs` contains a class named `RequestStats` — filename should match (`RequestStats.cs`) per C# conventions. Also, no `namespace` is declared; unless the project genuinely uses the global namespace, add one.

### 7. `Count` duplicates lookup logic — could be `counts.TryGetValue(path, out var n) ? n : 0`.

## Suggested rewrite

```csharp
using System.Collections.Concurrent;
using System.Collections.Generic;

public sealed class RequestStats
{
    private readonly ConcurrentDictionary<string, int> counts = new();

    public void Inc(string path)
    {
        ArgumentNullException.ThrowIfNull(path);
        counts.AddOrUpdate(path, 1, (_, n) => n + 1);
    }

    public int Count(string path) => counts.TryGetValue(path, out var n) ? n : 0;

    public IReadOnlyDictionary<string, int> Snapshot() =>
        new Dictionary<string, int>(counts);
}
```

**Verdict:** Works for single-threaded use, but the mutable `Snapshot()` aliasing bug and lack of thread safety should be fixed before merge, given this is clearly intended to count HTTP requests.
</details>

### 04-missing-error-handling

- [04-missing-error-handling.md](04-missing-error-handling.md)

<details><summary>Full AI response for 04-missing-error-handling</summary>

## Findings

### 1. `writeBackup()` leaks the file descriptor
**Severity: High**

`fs.openSync()` is never followed by `fs.closeSync()`. Repeated calls can exhaust the process's file-descriptor limit and prevent subsequent filesystem operations.

```ts
export function writeBackup(path: string, data: string): void {
  const fd = fs.openSync(path, "w")
  fs.writeSync(fd, data)
}
```

Prefer `fs.writeFileSync(path, data)`, which handles closing correctly, or close the descriptor in a `finally` block:

```ts
export function writeBackup(path: string, data: string): void {
  const fd = fs.openSync(path, "w")
  try {
    fs.writeSync(fd, data)
  } finally {
    fs.closeSync(fd)
  }
}
```

### 2. `loadConfig()` does not validate the parsed configuration
**Severity: High**

`JSON.parse()` returns `any`, so the function can return data that does not satisfy `AppConfig`. For example, the JSON could be valid but omit `dbUrl`, contain a string `port`, or include unexpected values. Failures may then occur far away from configuration loading.

```ts
const cfg = JSON.parse(raw)
return cfg
```

Validate the result before returning:

```ts
if (
  typeof cfg !== "object" ||
  cfg === null ||
  typeof cfg.port !== "number" ||
  !Number.isInteger(cfg.port) ||
  typeof cfg.dbUrl !== "string"
) {
  throw new Error("Invalid configuration")
}
```

Runtime validation is particularly important because the interface alone cannot guarantee that external JSON conforms to the type.

### 3. `fetchRemoteConfig()` returns an unchecked and unvalidated response body
**Severity: High**

The function does not verify that the HTTP request succeeded before parsing, and `res.json()` is implicitly treated as an `AppConfig` without validation. A 404/500 HTML response, malformed JSON, or a valid JSON object with the wrong shape can produce misleading errors or invalid configuration.

```ts
const res = await fetch(url)
return res.json()
```

It should check `res.ok`, parse the body into an `unknown`, and validate it before returning an `AppConfig`.

### 4. Inconsistent and potentially dangerous trust between local and remote configuration
**Severity: Medium**

Both functions return `AppConfig`, but neither ensures that invariant. Remote configuration deserves especially strict validation because it comes from a network source. Depending on how `dbUrl` is used, an invalid or maliciously supplied URL could redirect database connections or leaks credentials.

Validation should apply to both sources, potentially through a shared `validateConfig(value: unknown): AppConfig` helper.

### 5. `writeBackup()` may lose data or leave a partially written file on failure
**Severity: Medium**

If `writeSync()` throws, the current implementation leaves the descriptor open. Even after adding `finally`, the implementation directly truncates the target due to mode `"w"`. If the process fails partway through, the previous backup is lost.

A safer backup pattern is:

1. Write to a temporary file.
2. Flush/close it.
3. Atomically rename it over the destination.

At minimum, fix the descriptor leak; use an atomic write strategy if backup integrity matters.

### 6. Errors do not include useful context
**Severity: Low**

Filesystem errors and JSON parse errors will propagate without identifying which operation or configuration file failed. Consider wrapping errors with contextual information such as the file path, while avoiding logging sensitive file contents.

```ts
throw new Error(`Unable to load configuration from ${path}`, { cause: error })
```

## Recommended direction

Introduce a shared runtime validator and simplify the file write:

```ts
function validateConfig(value: unknown): AppConfig {
  const cfg = value as Partial<AppConfig>

  if (
    typeof cfg?.port !== "number" ||
    !Number.isInteger(cfg.port) ||
    cfg.port < 0 ||
    cfg.port > 65535 ||
    typeof cfg.dbUrl !== "string" ||
    cfg.dbUrl.length === 0
  ) {
    throw new Error("Invalid AppConfig")
  }

  return {
    port: cfg.port,
    dbUrl: cfg.dbUrl,
  }
}
```

Then:

- Use `fs.writeFileSync()` or a temp-file-plus-rename implementation for `writeBackup()`.
- Check `res.ok` in `fetchRemoteConfig()`.
- Pass both local and remote parsed values through `validateConfig()`.
- Consider making `dbUrl` a parsed/validated URL and constraining allowed URL schemes.

Overall, the API surface is simple and reasonable, but the change should not be accepted as-is because it leaks file descriptors and provides no runtime guarantee that either configuration source actually produces an `AppConfig`.
</details>

### 05-clean-refactor

- [05-clean-refactor.md](05-clean-refactor.md)

<details><summary>Full AI response for 05-clean-refactor</summary>

## Code Review: `src/totals.cs`

### Summary
The change refactors a manual accumulation loop into a LINQ `Sum()` and consolidates the tax calculation. It's functionally near-equivalent, cleaner, and idiomatic. A few subtle points worth noting:

### Findings

**1. Potential rounding difference (low severity, worth verifying)**
```csharp
// Before:
var tax = total * taxRate;
return total + tax;          // total + (total * taxRate)

// After:
return subtotal * (1 + taxRate);
```
With `decimal`, `a + a*r` and `a * (1 + r)` can produce different results for certain values due to intermediate rounding — e.g., rates that can't be represented exactly, or when `1 + taxRate` rounds. If `taxRate` is something like `0.0775m`, `1 + taxRate` is exact, but `subtotal * 1.0775` vs `subtotal + subtotal * 0.0775` can differ in the last digit since the intermediate `total * taxRate` is rounded before the addition. If downstream tests assert exact totals or this feeds billing, verify equivalence with representative rates.

**2. Overflow behavior is equivalent — good**
`Enumerable.Sum` for `decimal` uses `checked` arithmetic and throws `OverflowException` on accumulation overflow, same as the original `total = total + ...`. No regression there.

**3. Null handling is equivalent**
Both the old `foreach` and the new `items.Sum(...)` throw `NullReferenceException`/`ArgumentNullException` on a null `items` — behavior differs only in exception type (`ArgumentNullException` from LINQ vs `NullReferenceException` from foreach). If any caller catches `NullReferenceException` specifically (unlikely but possible), this is a subtle change.

**4. Product overflow inside the lambda — unchanged**
`item.Price * item.Quantity` still computes a `decimal` product per item; semantics identical to before.

**5. `using System.Linq;` added correctly**
The diff adds the required import. The file presumably already has `using System.Collections.Generic;` for `List<Item>` since that was needed before.

### Recommendation
**Approve**, with a request to either:
- Confirm no test asserts penny-exact totals that could differ under the new formula, or
- Keep the explicit two-step `var tax = subtotal * taxRate; return subtotal + tax;` for clarity/audit-friendliness if this is financial code — it's also more readable for reviewers checking tax logic.

The refactor is otherwise safe and an improvement in readability.
</details>

### 06-typos

- [06-typos.md](06-typos.md)

<details><summary>Full AI response for 06-typos</summary>

## Code Review: `src/accounts.ts`

### Findings (by severity)

**1. Misspelled error message reaches users (new line ~19)**
```ts
throw new Error("Username lenght must be at least 3 charaters.")
```
"lenght" → "length", "charaters" → "characters". This is user-facing text and will show up in logs/UI.

**2. Doc comment claims email is sent, but no email logic exists (~line 14)**
```ts
/**
 * Creates a new account and sends a welcome email.
 * We recieve the raw form input and normalize it.
 */
```
No welcome email is sent — either the doc is wrong or a feature was dropped. Also "recieve" → "receive".

**3. Misspelled variable and identifier names propagate to the public API**
- `retires` (~line 16, ~line 29) — should be `retries`. Harmless but sloppy; the log message echoes it.
- `getAdress` (~line 37) — **this is an exported function name**, so the typo becomes part of your public API and will be painful to fix later. Rename to `getAddress` now before consumers depend on it.
- `TEXT = "teh quick brown fox"` (~line 39) — likely intentional test data, but flag it.

**4. `timeoutMs` option is accepted but never used (~lines 9, 16)**
`opts.timeoutMs` is silently ignored. Either implement it or remove it from the options type — a caller will assume it takes effect.

**5. No validation/normalization of `email` or `address`**
Only `username` is normalized (trim + lowercase). `email` is typically also trimmed/lowercased, and neither field is validated for presence. `input.username.trim()` will also throw a TypeError if `username` is `undefined`/`null` rather than your friendly error — consider a null check first.

**6. `console.log` in library/service code (~line 29)**
Use the project's logger (if one exists) or remove it; raw `console.log` in an account service usually isn't desired in production.

**7. Minor style/consistency**
- `DEFAULTS` object and most statements lack semicolons while none are used elsewhere — pick one convention (or run the formatter/linter, which would also have caught several of the above via a spell-check rule).
- `username: username` → shorthand `username`.
- `LABEL = "Acme Colour Labs"` — "Colour" may be intentional (British branding), but if the codebase uses American spelling it could be a typo.

### Summary of typos
| Location | Wrong | Right |
|---|---|---|
| doc comment | recieve | receive |
| var `retires` | retires | retries |
| error msg | lenght, charaters | length, characters |
| export `getAdress` | getAdress | getAddress |
| `TEXT` | teh | the (if unintended) |

**Recommendation:** rename `getAdress` before merge (public API risk), fix the error message, reconcile the docstring with actual behavior, and either use or remove `timeoutMs`.
</details>

---
