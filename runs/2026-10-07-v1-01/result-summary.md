# v1 - 2026-10-07-01 — Detailed results

- Prompt: `prompts/code-review.v1.md`
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model; same)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **95.0/100** (+3.1 vs baseline)
- Hard fails: none

## What changed
Fixtures updated: 01 (Python → T-SQL), 03 (Go → C#), 05 (Python → C#). Expected findings updated to match new languages. Prompt unchanged.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-sql-injection | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +6.7 |
| 02-off-by-one | 3 | 3 | 1 | 2 | 3 | 3 | 3 | 85.0 | -10.0 |
| 03-race-condition | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +5.0 |
| 04-missing-error-handling | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +6.7 |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 |
| 06-typos | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 | +10.0 |

Typo recall (06-typos): misspelling 1/1, swap 2/2, missing_letter 3/3.

## Observations / next changes
- **Improvement in recall and precision**: All six typos in fixture 06 now found (vs. missing `usernam` before); all critical/high issues in 01-05 found with no false positives.
- **Severity calibration**: 02 (off-by-one) regressed: `totalPages` floor now rated high (expected medium) and validation rated medium (expected low/nit), two misses. 01, 04 still have one-level overrating on secondary findings. Suggest: tighten severity definitions with concrete examples (e.g., "high = wrong behavior in common paths; medium = edge cases or user-facing defects").
- **Actionability**: 02 and 06 have minor line-reference imprecision (off by 1-2 lines), but code snippets are correct. 06 actionability dropped to 2 due to line refs; consider adding a note to cite code snippets in addition to line numbers.
- **Language shift impact**: T-SQL and C# fixtures are now in scope. Reviewers correctly adapted to new languages; no language-specific false positives or misses. Prompt remains language-agnostic and effective.
- **Consistency**: 03 (race-condition) and 05 (clean-refactor) both scored 100.0, indicating strong handling of concurrency and refactor-quality assessment.

## Per-fixture results
#### [01-sql-injection](sql-injection.md) - 95.0
<details><summary>AI response</summary>

### Summary
The change adds a stored procedure `FindUserByName` that builds a SQL string via concatenation, plus a commented "alternative" line — both introduce SQL injection vulnerabilities in what is labeled "user queries."

### Findings
- **critical src/users.sql:9 - SQL injection via string concatenation in stored procedure**
- Problem: `@name` is interpolated directly into a dynamic SQL string and executed with `sp_executesql`. An attacker passing `x' OR '1'='1` (or `'; DROP TABLE users;--`) can read all users or execute arbitrary statements. This is a textbook exploitable vulnerability.
- Fix: Either use a static query (`SELECT id, name, email FROM users WHERE name = @name`) — preferred, since no dynamic SQL is needed here — or parameterize properly:
```sql
SET @query = N'SELECT id, name, email FROM users WHERE name = @pname'
EXEC sp_executesql @query, N'@pname NVARCHAR(255)', @pname = @name
```
- **high src/users.sql:18 - Vulnerable code left in file as a comment**
- Problem: The line `SELECT ... WHERE name = '" + name + "'` is another injection-prone pattern sitting in the file, explicitly labeled "Alternative vulnerable approach." Even as a comment, it invites copy-paste into application code and may trip security scanners/audits.
- Fix: Delete it, or replace with a safe parameterized example if an alternative is genuinely needed.
- **nit src/users.sql - Formatting/semicolon nits**
- Problem: Extra blank lines at the top of the file, missing semicolon after `DECLARE`, and `NVARCHAR` should be `N'...'` literal prefix for Unicode safety in the query string (the string literal should use the `N` prefix since `@query` is `NVARCHAR`).
- Fix: `SET @query = N'SELECT ...'`, tidy whitespace, add semicolons.

### Verdict
request changes — the stored procedure must not concatenate user input into dynamic SQL.

</details>

#### [02-off-by-one](off-by-one.md) - 85.0
<details><summary>AI response</summary>

### Summary
Adds `getPage` and `totalPages` pagination helpers. Both functions have off-by-one/rounding bugs that will return wrong results in common paths — the change should not ship as-is.

### Findings

- **high src/pagination.js:6 — `getPage` ignores the documented 1-based indexing**
- Problem: The docstring says `page` is 1-based, but `start = page * pageSize` treats it as 0-based. `getPage(items, 1, 10)` skips the first 10 items and returns items 10–19; `getPage(items, 0, 10)` actually returns the first page. Every caller following the documented contract gets the wrong slice.
- Fix:
  ```js
  const start = (page - 1) * pageSize;
  ```

- **high src/pagination.js:14 — `totalPages` undercounts with `Math.floor`**
- Problem: `Math.floor(items.length / pageSize)` drops the final partial page. With 25 items and pageSize 10, it returns 2 instead of 3, so the last 5 items become unreachable through `getPage`/`totalPages` together.
- Fix:
  ```js
  return Math.ceil(items.length / pageSize);
  ```

- **medium src/pagination.js:5-17 — no validation of `page` / `pageSize`**
- Problem: `pageSize <= 0` yields `Infinity`/`NaN` from `totalPages` and empty/odd slices from `getPage`; `page < 1` yields negative slice indices. If these helpers are called with untrusted or computed inputs, results will be silently wrong.
- Fix: add guards, e.g. `if (pageSize <= 0) throw new RangeError('pageSize must be positive')` and clamp/validate `page >= 1`.

### Verdict
request changes

</details>

#### [03-race-condition](race-condition.md) - 100.0
<details><summary>AI response</summary>

### Summary
Adds a `RequestStats` class that counts requests per path using a `Dictionary<string, int>` with increment, lookup, and snapshot methods. The logic is correct for single-threaded use, but the class is not thread-safe and `Snapshot` leaks the mutable internal state — both significant for something named "request stats," which implies concurrent use in a server.

### Findings

- **[high] src/counter.cs:27 — `Snapshot()` returns the live internal dictionary**
  - Problem: Callers receive a reference to `counts` itself, so they can mutate internal state (e.g., `Snapshot().Clear()` or set arbitrary values), and worse, if `Inc` runs while a caller iterates the snapshot it throws `InvalidOperationException` ("collection was modified"). This silently breaks the encapsulation the class exists to provide.
  - Fix: Return a copy: `return new Dictionary<string, int>(counts);`

- **[high] src/counter.cs:7–24 — no thread safety on shared mutable state**
  - Problem: `Inc` uses a check-then-act pattern (`ContainsKey` then index write) on a `Dictionary`, which is not thread-safe. For a request-counter (typically hit from many threads concurrently), concurrent `Inc` calls can lose increments or corrupt the dictionary's internal buckets, which can cause crashes or hangs.
  - Fix: Either use `ConcurrentDictionary<string, int>` with `counts.AddOrUpdate(path, 1, (_, v) => v + 1)` (and `TryGetValue` in `Count`), or guard all three methods with a `lock` on a private object. If single-threaded use is intended, document it on the class.

- **[low] src/counter.cs:10, 20 — `null` path throws `ArgumentNullException`**
  - Problem: `Dictionary` indexer/`ContainsKey` throws on `null` keys. Whether that matters depends on callers (not visible in the diff), but a defensive `ArgumentNullException.ThrowIfNull(path)` — or normalizing null/empty to a default key — would make behavior explicit.
  - Fix: Add `ArgumentNullException.ThrowIfNull(path);` at the top of `Inc` and `Count`, or document that null is rejected.

### Verdict
Request changes — the internal-state leak via `Snapshot` and the missing synchronization are real defects for a request-stats type; both are one-line fixes (return a copy, lock or use `ConcurrentDictionary`).

</details>

#### [04-missing-error-handling](missing-error-handling.md) - 95.0
<details><summary>AI response</summary>

### Summary
Adds a small config module with file load/backup helpers and a remote fetch. The change is simple but has a real resource leak and a couple of robustness gaps worth fixing.

### Findings

- **high src/config.ts:16-19 — `writeBackup` never closes the file descriptor**
  - Problem: `fs.openSync` returns a fd that is never passed to `fs.closeSync`. Repeated calls leak descriptors until the process hits `EMFILE` and crashes. Also, a single `fs.writeSync` is not guaranteed to write all bytes for large `data`.
  - Fix: use `fs.writeFileSync(path, data)` (handles open/write-all/close), or wrap in try/finally:
    ```ts
    const fd = fs.openSync(path, "w");
    try {
      fs.writeSync(fd, data);
    } finally {
      fs.closeSync(fd);
    }
    ```

- **medium src/config.ts:21-24 — `fetchRemoteConfig` ignores HTTP errors and returns unvalidated data**
  - Problem: `res.json()` is returned without checking `res.ok`, so a 404/500 error body is silently treated as an `AppConfig`. The parsed JSON is also unchecked, so callers get an object that may lack `port`/`dbUrl` (typed as `AppConfig` via `any`).
  - Fix: check `res.ok` and throw a descriptive error otherwise; optionally validate/coerce fields before returning, e.g.:
    ```ts
    if (!res.ok) throw new Error(`fetchRemoteConfig failed: ${res.status} ${res.statusText}`);
    const cfg = await res.json();
    if (typeof cfg?.port !== "number" || typeof cfg?.dbUrl !== "string")
      throw new Error("invalid remote config");
    return cfg;
    ```

- **medium src/config.ts:9-13 — `loadConfig` returns unvalidated JSON**
  - Problem: same issue as above for the local file — `JSON.parse` result is returned unchecked as `AppConfig`, so a malformed config produces confusing failures downstream instead of a clear error at load time.
  - Fix: validate `cfg.port`/`cfg.dbUrl` types (as above) and throw on mismatch; optionally wrap `readFileSync`/`JSON.parse` in try/catch to include `path` in the error message.

- **nit src/config.ts:22-23 — `res.json()` is `Promise<any>` silently matching `AppConfig`**
  - Problem: fine today, but hides the type gap. Covered by the validation fix above; otherwise annotate `const cfg = (await res.json()) as AppConfig` to make the unchecked cast explicit.

### Verdict
request changes — the fd leak in `writeBackup` is a genuine bug, and the unchecked `AppConfig` returns will produce misleading failures in common error paths.

</details>

#### [05-clean-refactor](clean-refactor.md) - 100.0
<details><summary>AI response</summary>

### Summary
The change refactors `OrderTotal` from a manual loop to a LINQ `Sum`, and rewrites `total + total * taxRate` as `subtotal * (1 + taxRate)`. The logic is mathematically equivalent, and the refactor is sound.

### Findings
No issues found. A couple of observations that are not findings:

- The old code returned `total + tax` (two decimal additions); the new returns `subtotal * (1 + taxRate)`. Decimal arithmetic is used throughout, and both forms are equivalent up to normal rounding — no behavioral change of note.
- `items` being `null` would throw in both versions (`foreach` → `NullReferenceException`, `.Sum` → `ArgumentNullException`), so the refactor doesn't change null-safety.
- The added `using System;` is unused (only `System.Collections.Generic` and `System.Linq` are needed), but this is trivial and may already be covered by implicit usings — at most a nit.

### Verdict
approve

</details>

#### [06-typos](typos.md) - 95.0
<details><summary>AI response</summary>

### Summary
Adds an `Account` interface, a `createAccount` function with option defaults and username validation, and a couple of constants. The change is riddled with misspellings — two of them are real bugs (a silently ignored option and a validation check that can never fire), and one misspells a public API field.

### Findings

- **[high] src/accounts.ts:18 — misspelled option key `maxRetires` makes the caller's setting silently ignored**
- Problem: `opts.maxRetires` doesn't match `DEFAULTS.maxRetries` / the `Partial<typeof DEFAULTS>` type. In TypeScript this is a compile error; if it somehow ships, `opts.maxRetires` is always `undefined`, so `??` falls back to the default and `maxRetries` passed by callers is ignored with no error.
- Fix: `const retries = opts.maxRetries ?? DEFAULTS.maxRetries;`

- **[high] src/accounts.ts:21 — `usernam.lenght` breaks the length validation**
- Problem: `string` has no `.lenght` property — this is a TS compile error, and in plain JS it evaluates `undefined < 3`, which is always `false`, so the "at least 3 characters" check would never reject anything.
- Fix: `if (usernam.length < 3) {`

- **[medium] src/accounts.ts:6,29,37-38 — `adress` misspelling baked into the public API**
- Problem: `Account.adress` and `getAdress()` are exported names. Shipping this means every consumer adopts the typo, and renaming later is a breaking change.
- Fix: rename to `address` and `getAddress` before merge.

- **[low] src/accounts.ts:22 — user-facing error message typo**
- Problem: `"Username must be at least 3 charcters long"` — `charcters` → `characters`. Visible to end users.
- Fix: correct the spelling.

- **[nit] comment typos**
- `recieve` → `receive` (line 15), `teh` → `the` in the comment on line 41 (the sample string `"teh quick brown fox"` itself is clearly intentional test data). Also `usernam` (line 19) works but reads as a truncated name — consider `username` or `normalizedUsername`.

### Verdict
request changes — the `maxRetires` and `.lenght` bugs must be fixed, and `adress` should be corrected before it becomes public API.

</details>

---
