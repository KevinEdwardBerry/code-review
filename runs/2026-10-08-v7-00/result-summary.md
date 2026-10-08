# v7 - 2026-10-08 — Detailed results

- Prompt: `prompts/code-review-v7.md`
- Reviewer: subagent_explore (unknown concrete model)
- Judge: subagent_general (unknown concrete model)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **80.3/100** (-12.2 vs v6)
- Hard fails: none

## What changed
```diff
--- /Users/kevinberry/src/code-review/prompts/code-review.v6.md	2026-10-07 18:03:15
+++ /Users/kevinberry/src/code-review/prompts/code-review-v7.md	2026-10-08 10:15:26
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
| 01-sql-injection | 3 | 2 | 2 | 2 | 3 | 3 | 3 | 83.3 | -16.7 |
| 02-off-by-one | 3 | 2 | 2 | 3 | 3 | 2 | 3 | 86.7 | -13.3 |
| 03-race-condition | 3 | 1 | 2 | 2 | 3 | 2 | 3 | 75.0 | -20.0 |
| 04-missing-error-handling | 3 | 2 | 2 | 2 | 3 | 2 | 2 | 80.0 | -16.7 |
| 05-clean-refactor | 3 | 2 | 3 | 2 | 2 | 2 | 2 | 81.7 | -15.0 |
| 06-typos | 3 | 1 | 3 | 2 | 2 | 2 | 2 | 75.0 | +8.3 |

### Typo recall (fixture 06)

| Category | Found/Total |
|---|---|
| misspelling | 1/1 |
| swap | 2/2 |
| missing_letter | 2/2 |


## Observations / next changes
### Patterns in misses and false positives
- v7 is a minimal one-line prompt; the reviewer still finds all seeded issues but loses calibration. The second SQLi line in 01 and the `totalPages` floor in 02 are over-ranked to critical, `fd_leak` in 04 is over-ranked to high, and `lenght`/`maxRetires` in 06 are over-ranked to critical.
- The 06-typos fixture still flags must-not-flag items (`teh` in `TEXT`, `usernam` local abbreviation, and `Colour` in `LABEL`) and includes several unseeded non-typo observations.
- Exact `file:line` citations are missing; most findings use approximate line numbers or none.
- Output format deviates from the requested Summary/Findings/Verdict structure: some reviews use emojis, extra sections, or lack the exact headings.

### Suggested prompt changes
1. Restore the `## Severity` section with concrete, ordered definitions and examples to stop over-ranking acceptable extras.
2. Restore the `## Citing exact file:line` requirement and a worked `@@` hunk-header example.
3. Restore the concurrency, behavior-preserving rewrite, and typo rules (including the must-not-flag list) from v6.
4. Restore the `## Output format` template and require Summary/Findings/Verdict ordering without emojis or extra sections.

## Per-fixture results
### 01-sql-injection

- [01-sql-injection.md](01-sql-injection.md)

<details><summary>Full AI response for 01-sql-injection</summary>

# Code Review: `src/users.sql`

## Critical Issues

### 1. SQL Injection (BLOCKER)
Both additions build SQL via string concatenation with unparameterized user input:

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
EXEC sp_executesql @query
```
and
```sql
SELECT id, name, email FROM users WHERE name = '" + name + "'"
```

An input like `' OR '1'='1` or `'; DROP TABLE users; --` would execute arbitrary SQL. This defeats the entire purpose of a stored procedure.

**Fix** — the proc doesn't need dynamic SQL at all:
```sql
CREATE PROCEDURE FindUserByName
    @name NVARCHAR(255)
AS
BEGIN
    SELECT id, name, email FROM users WHERE name = @name;
END
```
If dynamic SQL were truly needed, use parameters: `EXEC sp_executesql @query, N'@name NVARCHAR(255)', @name`.

### 2. Invalid SQL Syntax (BLOCKER)
```sql
SELECT id, name, email FROM users WHERE name = '" + name + "'
```
This line sits at file top-level, outside any procedure, and mixes SQL with application-language string concatenation (`" + name + "`). It will fail to parse/execute as SQL. It looks like application code (e.g., PHP/JS) was accidentally pasted into the `.sql` file — it should be removed and replaced with a parameterized query in the calling code, or a call to the stored procedure.

## Minor Issues

- **Inconsistent style:** keywords are uppercase but there's no `;` statement terminators; `EXEC` lacks parentheses (valid, but `EXEC(...)` or `EXECUTE` is cleaner).
- **`NVARCHAR(MAX)`** for `@query` is unnecessary here, though harmless.
- No `SET NOCOUNT ON;` in the procedure (minor convention).
- The comment `-- User queries` followed by `+` on blank lines suggests formatting noise in the diff; ensure the file doesn't contain stray artifacts.

## Recommendation
Do not merge. Rewrite the procedure as a static parameterized query and delete the orphaned concatenated SELECT line entirely — and audit the application layer for any similar string-concatenated queries, since the pasted line suggests this pattern exists elsewhere.


</details>

### 02-off-by-one

- [02-off-by-one.md](02-off-by-one.md)

<details><summary>Full AI response for 02-off-by-one</summary>

## Code Review: `src/pagination.js`

### 🔴 Critical Bugs

**1. Off-by-one error in `getPage` (line ~8)**

```js
const start = page * pageSize;
```

The docstring says the page number is **1-based**, but the math treats it as 0-based. With `page = 1`, `start = pageSize`, so page 1 skips the first `pageSize` items entirely, and page 0 (or the last page) behaves incorrectly.

**Fix:**
```js
const start = (page - 1) * pageSize;
```

**2. `totalPages` truncates instead of rounding up (line ~16)**

```js
return Math.floor(items.length / pageSize);
```

With 25 items and `pageSize = 10`, this returns `2` instead of `3` — the final 5 items are unreachable. Page counts must round up:

**Fix:**
```js
return Math.ceil(items.length / pageSize);
```

### 🟡 Missing Input Validation

- **`pageSize <= 0`**: `Math.floor(n / 0)` → `Infinity` in `totalPages`, and `page * 0` in `getPage` silently returns an empty slice. Should throw or guard.
- **`page < 1`**: negative/0 page numbers produce negative `start`, and `slice` with a negative index reads from the end of the array — silently wrong results.
- **`items` not an array**: `.slice` / `.length` would throw `TypeError` on null/undefined — a friendlier guard may be warranted depending on conventions.

### 🟢 Minor Notes

- No test coverage is added alongside the new module — both bugs above would be caught by a trivial test (`getPage(items, 1, 10)` should return the first 10 items).
- `module.exports` (CommonJS) — fine if consistent with the rest of the codebase, but can't be verified since files weren't read.

### Verdict

**Request changes.** Both functions have correctness bugs in their core logic; `getPage` contradicts its own documented 1-based contract, and `totalPages` under-counts. Neither should merge as-is.


</details>

### 03-race-condition

- [03-race-condition.md](03-race-condition.md)

<details><summary>Full AI response for 03-race-condition</summary>

## Code Review: `src/counter.cs`

### 🔴 Correctness / API design issues

1. **`Snapshot()` returns the internal mutable dictionary** (line ~26)
   - Callers can mutate, clear, or corrupt internal state: `stats.Snapshot()["/admin"] = 999;`
   - Fix: return a copy (`new Dictionary<string,int>(counts)`) or expose `IReadOnlyDictionary<string,int>`.

2. **Not thread-safe**
   - A request-stats counter is almost certainly incremented from concurrent request threads. `Dictionary` is not safe for concurrent read/write — `Inc` can lose updates or corrupt internal buckets.
   - Fix: use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd`, or guard all access with a `lock`.

3. **`Inc(null)` throws `ArgumentNullException`**
   - `Dictionary` does not accept null keys. Either validate (`ArgumentNullException.ThrowIfNull(path)`) explicitly or document the contract.

### 🟡 Minor / style

4. **Double lookup** — `ContainsKey` + indexer performs two hash lookups. Prefer `TryGetValue`:
   ```csharp
   counts.TryGetValue(path, out int n);
   counts[path] = n + 1;
   ```
   (Or `CollectionsMarshal.GetValueRefOrAddDefault` for a single lookup.)

5. **File/class name mismatch** — file is `counter.cs` but declares `public class RequestStats`. Convention is `RequestStats.cs`; some tooling/builds expect this.

6. **No namespace** — the class lands in the global namespace; wrap it in the project's namespace.

7. **Field could be `readonly`** — `counts` is never reassigned: `private readonly Dictionary<string,int> counts = new();`

8. **`Count` duplicates lookup logic** — could be `counts.TryGetValue(path, out var n) ? n : 0`.

### Suggested rewrite

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

**Verdict:** Works for single-threaded use, but the mutable `Snapshot()` leak and lack of thread safety should be fixed before merge, given this is clearly intended to count HTTP requests.


</details>

### 04-missing-error-handling

- [04-missing-error-handling.md](04-missing-error-handling.md)

<details><summary>Full AI response for 04-missing-error-handling</summary>

## Code Review: `src/config.ts` config helpers

### Issues

**1. `writeBackup` leaks the file descriptor (high severity)**
```ts
const fd = fs.openSync(path, "w");
fs.writeSync(fd, data);
```
`fd` is never closed with `fs.closeSync(fd)`. Repeated calls exhaust the process's fd limit. Also, `fs.writeSync` on a string may perform a partial write — there's no loop or byte-count check. This whole function is better expressed as `fs.writeFileSync(path, data)`, which is atomic-equivalent, closes properly, and handles partial writes. If `openSync` is intentionally used (e.g., to control flags/mode), wrap it:
```ts
const fd = fs.openSync(path, "w");
try {
  fs.writeSync(fd, data, null, "utf8");
} finally {
  fs.closeSync(fd);
}
```

**2. `loadConfig` performs no validation of `cfg` (medium)**
`JSON.parse` returns `any` and it's cast implicitly to `AppConfig`. A malformed file (missing `port`, `port` as a string, etc.) propagates silently and fails far from the cause. Validate the shape before returning:
```ts
const cfg = JSON.parse(raw);
if (typeof cfg.port !== "number" || typeof cfg.dbUrl !== "string") {
  throw new Error(`Invalid config at ${path}`);
}
```
Or use a schema validator (zod, ajv). Also consider whether `JSON.parse`/`readFileSync` errors should be wrapped with the path for context — a bare `ENOENT` stack doesn't tell the caller which file failed.

**3. `fetchRemoteConfig` has the same validation gap, plus no HTTP error handling (medium)**
```ts
const res = await fetch(url);
return res.json();
```
- `res.ok` is never checked — a 404/500 body will be parsed as config, likely producing a silently wrong `AppConfig` or a confusing JSON error. Should be:
```ts
if (!res.ok) throw new Error(`fetch ${url} failed: ${res.status}`);
```
- No timeout/AbortSignal — a hung remote endpoint leaves this awaiting forever. Consider `AbortSignal.timeout(...)`.
- `res.json()` returns `any`; same runtime-validation concern as #2.

**4. Inconsistent sync/async API surface (minor)**
`loadConfig` is synchronous but `fetchRemoteConfig` is async, and the file writes are sync. Fine for startup code, but if `writeBackup` is called on a hot path, blocking I/O + the fd leak compounds. Worth documenting intent.

**5. Security note (minor)**
`writeBackup` writes with default permissions and `path`/`url` are unchecked. If `path` can come from user input, this is a path-traversal/write-anywhere risk; if `url` is user-controlled, `fetchRemoteConfig` is an SSRF vector. Likely internal-only, but flag it if either is reachable from request data.

### Recommendations (priority order)
1. Replace `writeBackup` with `fs.writeFileSync`, or close the fd in a `finally`.
2. Check `res.ok` and add a timeout in `fetchRemoteConfig`.
3. Validate the parsed shape in both loaders before returning `AppConfig` — ideally share one `validateConfig(raw: unknown): AppConfig` helper so the two paths can't drift.

### What looks fine
- Typing the interface and returning `Promise<AppConfig>` is reasonable.
- `readFileSync`/`openSync` at startup is acceptable for a config module.


</details>

### 05-clean-refactor

- [05-clean-refactor.md](05-clean-refactor.md)

<details><summary>Full AI response for 05-clean-refactor</summary>

Code review findings:

## Summary
The refactor replaces a manual accumulation loop with LINQ `Sum` and consolidates the tax calculation into a single expression. Functionally equivalent, but there are a few points worth noting.

## Findings

**1. Correctness — equivalent, with one subtle improvement (no severity: low/nit)**
- `subtotal * (1 + taxRate)` is mathematically identical to `total + total * taxRate`, and arguably clearer in intent.
- One minor difference: the old code computed `total * taxRate` first, then added. Floating-point rounding for `decimal` can differ microscopically between `t + t*r` and `t*(1+r)` in edge cases, but for `decimal` this is essentially a non-issue.

**2. Missing `Item` type context**
- `Item` is referenced but its definition isn't in the diff. If `Price` or `Quantity` aren't `decimal`/`int` respectively (e.g., `double` Price), `item.Price * item.Quantity` would resolve to a different `Sum` overload. Worth confirming types, though presumably it compiled.

**3. Null handling — unchanged behavior (info)**
- `items.Sum(...)` throws `ArgumentNullException` on a null list; the old `foreach` threw `NullReferenceException`. Neither handles null gracefully — behavior still broken on null input, just with a different exception. If null is a real possibility, consider `items?.Sum(...) ?? 0m`.

**4. Overflow semantics — unchanged (info)**
- `decimal` arithmetic throws `OverflowException` on overflow rather than wrapping, same as before. No change.

**5. Style**
- The added `using System;` and `using System.Collections.Generic;` may already exist elsewhere or be unnecessary if this file previously relied on implicit usings/global usings — verify no duplicate/unused usings. `System` isn't needed for anything visible here.
- `Sum` iterates once — same O(n) performance as the loop; allocation of the lambda delegate is negligible (compiler may cache it).

## Verdict
Approve. The change is a clean, idiomatic simplification. Only actionable nits: consider null-safety on `items` if callers may pass null, and trim the unused `using System;`.


</details>

### 06-typos

- [06-typos.md](06-typos.md)

<details><summary>Full AI response for 06-typos</summary>

## Code Review: `src/accounts.ts`

### 🔴 Critical — Compile/runtime errors

1. **`opts.maxRetires` is a typo** (line ~`const retries = ...`). `DEFAULTS` defines `maxRetries`, so `opts.maxRetires` is a TypeScript compile error: `Property 'maxRetires' does not exist on type 'Partial<{ maxRetries: number; timeoutMs: number; }>'`. Fix: `opts.maxRetries ?? DEFAULTS.maxRetries`.

2. **`usernam.lenght` is a typo** — `lenght` is not a real property; this throws `TypeError` (or fails compile since `string` has no `lenght`). Fix: `usernam.length`.

### 🟠 Significant issues

3. **`adress` field misspelled** throughout: interface `Account.adress`, usage `input.adress`, and public API `getAdress()`. If this ships, it propagates the misspelling into the public contract. Fix to `address`/`getAddress` before release (breaking change later).

4. **Misleading docstring**: "Creates a new account and sends a welcome email" — no email is sent and nothing is persisted; it only normalizes and returns an object. Either implement or correct the comment. Also "recieve" → "receive".

5. **`timeoutMs` option is accepted but never used** — same for `retries`, which is only logged. Either wire them up or remove from the options type to avoid a misleading API.

6. **No email validation/normalization**: `input.email` is stored raw (no trim/lowercase/format check), inconsistent with username handling.

7. **`input.adress` passed through untrimmed** — normalize consistently.

### 🟡 Minor / polish

8. `usernam` variable name missing the final `e` — rename to `normalizedUsername` or `username`.
9. `"Username must be at least 3 charcters long"` — typo: `characters`.
10. `TEXT = "teh quick brown fox"` — `teh` → `the`. Also this constant looks like leftover test data; question whether it belongs in this module.
11. `LABEL = "Acme Colour Labs"` — `Colour` is valid British English, but verify it matches the project's spelling convention (US vs UK).
12. `console.log` in a service layer — prefer an injected/logger dependency; log statements also expose account data.

### Suggested corrected core

```ts
export interface Account {
  username: string;
  email: string;
  address: string;
}

export function createAccount(input: Account, opts: Partial<typeof DEFAULTS> = {}) {
  const retries = opts.maxRetries ?? DEFAULTS.maxRetries;
  const username = input.username.trim().toLowerCase();

  if (username.length < 3) {
    throw new Error("Username must be at least 3 characters long");
  }

  const account: Account = {
    username,
    email: input.email.trim().toLowerCase(),
    address: input.address.trim(),
  };
  return account;
}
```

**Verdict: Request changes** — items 1 and 2 are hard blockers; items 3–6 should be resolved before merge since they affect the public API surface.


</details>



---
