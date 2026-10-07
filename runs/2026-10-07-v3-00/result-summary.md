# v3 - 2026-10-07 — Detailed results

- Prompt: `prompts/code-review.v3.md`
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **93.3/100** (-0.6 vs v2)
- Hard fails: none

## What changed
Diff vs `code-review.v2.md`:
- Concurrency checklist: now explicitly tells reviewers to check every method that reads or writes shared state — including getters and read-only paths — not just mutating methods.
- Severity section header no longer says "(with examples)"; definitions are slightly reworded. High now says "typical inputs"; medium now explicitly mentions "remainder/partial results" and "unusual inputs".
- Spelling checklist: dropped the explicit "A misspelled public API name is costly to fix later" example line; that example is now only in the medium severity definition.
- Rules: added explicit instruction to derive new-file line numbers from diff `@@` hunk headers (`+start,count`), replaced "If context is missing, say so briefly instead of guessing" with "Do not speculate...; if context is missing, say so briefly.", and extended the must-not-flag typo rule to "comments or fixtures that describe intentional misspellings."

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-sql-injection | 3 | 2 | 2 | 3 | 2 | 3 | 3 | 85.0 | -10.0 |
| 02-off-by-one | 3 | 3 | 2 | 2 | 3 | 3 | 3 | 90.0 | -5.0 |
| 03-race-condition | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +10.0 |
| 04-missing-error-handling | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | -5.0 |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 |
| 06-typos | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 | +6.7 |

Typo recall (06-typos): misspelling 1/1, swap 2/2, missing_letter 3/3.

## Observations / next changes
- **Concurrency prompt change worked**: 03 recall jumped from 2→3 and the hard fail cleared. The reviewer now explicitly captured the `Count` read race together with `Inc` in the thread-safety finding, and flagged `Snapshot` leaking the internal dictionary as a separate high finding.
- **Severity calibration still off on secondary issues**: 01's "alternative vulnerable line" was reframed as high instead of the expected low/nit; 04's fd leak was rated high (expected medium); 02's `totalPages` floor remains high (expected medium). The high/medium boundary clarification did not fully land.
- **Line-number drift persists**: reviewers quote snippets consistently but still cite lines off by 1–4 (02, 06). The new `@@` hunk-header instruction did not eliminate the drift; the actionability scores on 02 and 06 are capped at 2 because of it.
- **Typos fixture improved significantly**: precision recovered to 3/3 (no `teh`/`Colour` false positives, no doc-claim noise), ranking is exact, and the two behavioral typos are listed first. Recall is perfect across all three typo categories.
- **Suggested prompt changes**:
  1. Severity boundary: add a worked example showing "high = wrong for every typical input" vs "medium = wrong only for edge/remainder cases" (e.g., `totalPages` floor and `fd_leak`).
  2. Line numbers: include a concrete worked example of counting new-file lines from a sample `@@` hunk header, not just the abstract rule.
  3. Clarify that leftover documentation-only vulnerable snippets (like the "alternative vulnerable approach" line) are acceptable to note as low/nit, not high-severity defects.
  4. Encourage reviewers to split bundled typo findings (one finding per distinct defect) to improve actionability granularity.

## Per-fixture results
#### [01-sql-injection](01-sql-injection.md) - 85.0
<details><summary>AI response</summary>

### Summary
The diff adds a stored procedure that builds a SQL query via string concatenation and executes it with `sp_executesql`, plus a commented/loose "alternative" line that shows the same concatenation pattern. This introduces a clear, exploitable SQL injection vulnerability.

### Findings

- **critical src/users.sql:8-10 — SQL injection via dynamic SQL string concatenation**
  - Problem: `@name` is interpolated directly into a query string and executed. Input like `'; DROP TABLE users; --` escapes the quoted literal and runs arbitrary SQL. This is the classic SQLi pattern — parameterization must be used, not string building.
  - Fix: use a parameterized query, e.g.
    ```sql
    CREATE PROCEDURE FindUserByName
        @name NVARCHAR(255)
    AS
    BEGIN
        SELECT id, name, email FROM users WHERE name = @name
        -- or, if dynamic SQL is truly needed:
        -- EXEC sp_executesql N'SELECT id, name, email FROM users WHERE name = @p', N'@p NVARCHAR(255)', @p = @name
    END
    ```
  - Code snippet:
    ```sql
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **high src/users.sql:15 — invalid SQL committed to the file**
  - Problem: the line `SELECT ... WHERE name = '" + name + "'`" is not valid T-SQL — it's application-level concatenation pseudocode left in a .sql file. It will break anything that executes this file (migrations, schema apply scripts). Even as a "documentation" of the vulnerable pattern, it shouldn't ship.
  - Fix: delete the line entirely; do not retain vulnerable example code in the repo.
  - Code snippet:
    ```sql
    -- Alternative vulnerable approach
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

- **medium src/users.sql:9 — `DECLARE @query` missing semicolon/termination robustness**
  - Problem: minor — `NVARCHAR(MAX)` for a fixed-shape query and absence of `SET NOCOUNT ON` / error handling is noise compared to the injection, but worth cleaning up while fixing the procedure.
  - Fix: once the procedure is rewritten as a direct parameterized SELECT, this disappears.

### Verdict
request changes — the change introduces an exploitable SQL injection and an invalid SQL statement; both must be fixed before merge.

</details>

#### [02-off-by-one](02-off-by-one.md) - 90.0
<details><summary>AI response</summary>

### Summary
Adds `getPage` and `totalPages` pagination helpers. Both functions have off-by-one/rounding bugs that produce wrong results for typical inputs.

### Findings
- **high src/pagination.js:6 - off-by-one in `getPage` for 1-based pages**
  - Problem: The doc says `page` is 1-based, but `start = page * pageSize` treats it as effectively skipping the first page — page 1 returns items `[pageSize, 2*pageSize)` instead of `[0, pageSize)`. Every caller gets the wrong page.
  - Fix: `const start = (page - 1) * pageSize;`
  - Snippet:
    ```js
    const start = page * pageSize;
    ```

- **high src/pagination.js:14 - `totalPages` drops the final partial page**
  - Problem: `Math.floor` means `totalPages([1,2,3], 2)` returns 1 instead of 2, and any non-empty list shorter than `pageSize` returns 0 pages — a caller iterating pages 1..totalPages would never see those items.
  - Fix: `return Math.ceil(items.length / pageSize);`
  - Snippet:
    ```js
    return Math.floor(items.length / pageSize);
    ```

- **low src/pagination.js:6 - no validation for `page`/`pageSize`**
  - Problem: `pageSize <= 0` yields `NaN`/`Infinity` from `totalPages` and odd `slice` behavior; `page = 0` (with the corrected formula) yields a negative start that `slice` interprets relative to the end of the array, returning wrong data. Optional but cheap defensive guard.
  - Fix: validate `page >= 1` and `pageSize >= 1`, throwing a `RangeError` otherwise.
  - Snippet:
    ```js
    function getPage(items, page, pageSize) {
      const start = page * pageSize;
    ```

### Verdict
request changes

</details>

#### [03-race-condition](03-race-condition.md) - 95.0
<details><summary>AI response</summary>

### Summary
Adds a `RequestStats` class that tracks per-path request counts in a plain `Dictionary<string,int>`. The logic is simple and correct in single-threaded use, but `Snapshot()` leaks the live mutable dictionary and nothing is thread-safe for what is presumably a request-tracking use case.

### Findings

- **high** src/counter.cs:26 - `Snapshot()` returns the internal dictionary, exposing mutable shared state
  - Problem: Returning `counts` directly hands callers a live reference to the private field. Any caller can add, remove, or `Clear()` entries, silently corrupting stats; they can also observe mutations in real time and hit `InvalidOperationException` if they enumerate while `Inc` writes. This defeats the encapsulation the `private` field is supposed to provide.
  - Fix: Return a copy, e.g. `return new Dictionary<string, int>(counts);` or expose `IReadOnlyDictionary<string,int>` over a defensive copy.
  - Code snippet:
    ```csharp
    public Dictionary<string, int> Snapshot()
    {
        return counts;
    }
    ```

- **medium** src/counter.cs:9-22 - No thread-safety despite request-counting context
  - Problem: `Dictionary<,>` is not thread-safe. If `Inc`/`Count`/`Snapshot` are ever called from concurrent request handlers (the class name implies a web/request context), the `ContainsKey` + index pattern in `Inc` is a check-then-act race, and a `Snapshot` copy concurrent with writes can corrupt the dictionary or throw. This is only a must-fix if the class is shared across threads — the diff alone doesn't show usage, but "request stats" strongly suggests it.
  - Fix: Use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, n) => n + 1);` and `TryGetValue`/`GetValueOrDefault` in `Count`, or guard all access with a `lock`.
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    ```

- **low** src/counter.cs:9 - `Inc(null)` throws `ArgumentNullException`
  - Problem: `Dictionary` forbids null keys, so `Inc(null)` and `Count(null)` throw. If `path` can plausibly be null (e.g., unmatched route), decide explicitly whether to reject or normalize rather than relying on the incidental exception.
  - Fix: Add `ArgumentNullException.ThrowIfNull(path);` for a clear contract, or map null/empty to a sentinel like `""`.
  - Code snippet:
    ```csharp
    public void Inc(string path)
    ```

- **nit** src/counter.cs:10 - Redundant `ContainsKey` + indexer double lookup
  - Problem: Two hash lookups per increment; `TryGetValue` does it in one. Purely a micro-optimization.
  - Fix: `counts[path] = counts.TryGetValue(path, out var n) ? n + 1 : 1;`
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    ```

### Verdict
request changes (the `Snapshot()` encapsulation leak is a real defect; thread-safety should be addressed or documented before merge).

</details>

#### [04-missing-error-handling](04-missing-error-handling.md) - 95.0
<details><summary>AI response</summary>

### Summary
Adds a small config module with file load/backup-write and remote fetch helpers. Straightforward, but `writeBackup` leaks its file descriptor and `fetchRemoteConfig` never checks the HTTP status.

### Findings

- **high src/config.ts:16-19 - `writeBackup` never closes the file descriptor**
  - Problem: `fs.openSync` returns an fd that is never passed to `fs.closeSync`. Every call leaks a descriptor; under repeated calls the process can exhaust fds and crash. It also leaves data durability/flush semantics ambiguous.
  - Fix: close in a `finally`, or just use `fs.writeFileSync(path, data)`.
  - Code snippet:
    ```ts
    const fd = fs.openSync(path, "w");
    fs.writeSync(fd, data);
    ```

- **medium src/config.ts:21-24 - `fetchRemoteConfig` ignores HTTP errors and return type mismatch**
  - Problem: `res.json()` is parsed even on 4xx/5xx (often returning an error page/body that isn't valid config), and `Response.json()` returns `Promise<any>` — fine, but without an `ok` check a failed fetch silently produces garbage config. A non-JSON error body will also throw an unhelpful parse error instead of a status error.
  - Fix:
    ```ts
    const res = await fetch(url);
    if (!res.ok) throw new Error(`fetchRemoteConfig failed: ${res.status}`);
    return res.json();
    ```

- **low src/config.ts:9-12 - `loadConfig`/`fetchRemoteConfig` trust JSON shape**
  - Problem: `cfg`/`res.json()` are returned as `AppConfig` with no validation; a config file missing `port`/`dbUrl` (or with wrong types) propagates silently and fails later in confusing ways.
  - Fix: validate required fields/types after parsing and throw a descriptive error.

- **low src/config.ts:9-12 - `loadConfig` throws raw errors**
  - Problem: `readFileSync`/`JSON.parse` throw on missing file or malformed JSON with no context about which config path failed. Not a bug, but a cheap improvement for operability.
  - Fix: wrap in try/catch and rethrow with `path` included.

### Verdict
request changes (fd leak must be fixed).

</details>

#### [05-clean-refactor](05-clean-refactor.md) - 100.0
<details><summary>AI response</summary>

### Summary
The change refactors `OrderTotal` from a manual accumulation loop to a LINQ `Sum` and folds the tax computation into a single expression. The arithmetic is mathematically equivalent and preserves the same decimal semantics; no behavioral change for valid inputs.

### Findings

- **[nit] src/totals.cs:9 - null `items` throws differently**
  - Problem: Both old and new code fail on a null `items` list, but `foreach` over null throws `NullReferenceException` while `items.Sum(...)` throws `ArgumentNullException`. This is a marginal improvement, not a regression — flagging only as an observation; a defensive `ArgumentNullException.ThrowIfNull(items)` would make the contract explicit.
  - Code snippet: `decimal subtotal = items.Sum(item => item.Price * item.Quantity);`

No correctness, security, concurrency, or spelling issues. The refactor is equivalent: `total + total * taxRate` ≡ `subtotal * (1 + taxRate)` for decimal arithmetic, and `Sum` handles empty lists identically (returns 0m).

### Verdict
approve

</details>

#### [06-typos](06-typos.md) - 95.0
<details><summary>AI response</summary>

### Summary
Adds an `Account` interface, a `createAccount` function with username validation and retry options, and an address getter. The change is riddled with typos, two of which are functional bugs: validation that never fires and a silently ignored caller option.

### Findings
- **[high] src/accounts.ts:24 — `usernam.lenght` makes length validation a no-op**
  - Problem: `lenght` is undefined on a string, so `usernam.lenght < 3` is always `false`. Usernames of any length (including empty) pass validation; the error is unreachable.
  - Fix: `if (usernam.length < 3)`.
  - Code snippet: `if (usernam.lenght < 3) {`

- **[high] src/accounts.ts:19 — `opts.maxRetires` silently ignores the caller's option**
  - Problem: The options type is `Partial<typeof DEFAULTS>` which has `maxRetries`, not `maxRetires`. Callers passing `maxRetries` will be ignored (the misspelled property is always `undefined`), so `retries` is always 3. TypeScript will likely flag reads of a nonexistent property, but even if it compiles the option never works.
  - Fix: `const retries = opts.maxRetries ?? DEFAULTS.maxRetries;`.
  - Code snippet: `const retries = opts.maxRetires ?? DEFAULTS.maxRetries;`

- **[medium] src/accounts.ts:5,38 — misspelled public API name `adress` / `getAdress`**
  - Problem: `adress` appears in the `Account` interface, `createAccount`'s returned object, and the exported `getAdress` function. This is a public API surface; shipping a misspelled property/function name is costly to correct later. (Note `email`/`adress` are also copied without normalization or validation, but that's out of scope.)
  - Fix: Rename to `address` / `getAddress` everywhere before this ships.
  - Code snippet:
    ```ts
    adress: string;
    ...
    export function getAdress(account: Account): string {
      return account.adress;
    ```

- **[low] src/accounts.ts — typos in comments, strings, and local names**
  - Problem: `recieve` (doc comment), `charcters` (user-facing error message), `usernam` (local variable, consistent but confusing). `TYPO_SAMPLE` and its comment intentionally use "teh" — do not change. "Colour" in `BRAND` is an intentional brand name — do not change.
  - Fix: `receive`, `characters`, and rename `usernam` → `username` (shadowing `account.username` field name is fine, or use `normalizedUsername`).
  - Code snippet:
    ```ts
    // We recieve the raw form input and normalize it.
    throw new Error("Username must be at least 3 charcters long");
    const usernam = input.username.trim().toLowerCase();
    ```

### Verdict
Request changes — the length validation never fires and the retry option is silently ignored; both must be fixed before merge.

</details>

---
