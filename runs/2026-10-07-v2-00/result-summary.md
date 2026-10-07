# v2 - 2026-10-07 — Detailed results

- Prompt: `prompts/code-review.v2.md`
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **93.9/100** (-1.1 vs v1)
- Hard fails: 03-race-condition (`missed_critical` — unlocked read in `Count` not found)

## What changed
Diff vs `code-review.v1.md`:
- Severity section renamed "Severity (with examples)"; each level now carries a tightened definition plus concrete examples (e.g. high = "off-by-one in pagination, silently ignored caller options"; medium = "misspelled public API names").
- Rules: file:line citations must now be accompanied by a quoted code snippet.
- New rule: optional/validation extras may only be flagged if they materially improve safety or prevent a real failure mode, and must not be rated above must-find issues.
- Output format: each finding must include a "Code snippet" field; Problem/Fix sub-bullets are now indented under the finding title.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-sql-injection | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 | +0.0 |
| 02-off-by-one | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +10.0 |
| 03-race-condition | 2 | 3 | 2 | 3 | 3 | 3 | 3 | 85.0 | -15.0 |
| 04-missing-error-handling | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +5.0 |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 |
| 06-typos | 3 | 2 | 3 | 2 | 3 | 3 | 3 | 88.3 | -6.7 |

Typo recall (06-typos): misspelling 1/1, swap 2/2, missing_letter 3/3.

## Observations / next changes
- **Recall regression on 03 (hard fail)**: the reviewer folded the unsynchronized read in `Count` into the `Inc` race finding ("Dictionary is unsafe for concurrent reads/writes") rather than flagging it separately; the judge counted `unlocked_read` as missed, triggering `missed_critical`. Worth a prompt nudge to evaluate every method/member that touches shared state, not just the obvious writer.
- **Severity calibration improved**: v1's one-level overrating on secondary findings in 01 and 04 is gone (both now 3/3). 02 still rates `totalPages` floor as high vs expected medium — the one remaining calibration miss; the examples apparently helped but "breaks normal use" in the high definition still sweeps in partial-page undercounting.
- **Precision dip on 06**: the new code-snippet requirement didn't stop two noise additions — an unlisted extra finding (JSDoc "sends a welcome email" with no email code) and flagging "teh" in a comment that describes deliberate test data. Correctly spared `Colour` and the `TYPO_SAMPLE` string.
- **Actionability/line refs still drift**: quoted snippets are now required and present, but cited line numbers remain off by 1–4 lines in 01 and 06 (reviewer appears to count added-file lines inconsistently). Line refs, not missing snippets, are now the actionability bottleneck.
- **Suggested prompt changes**:
  1. Add to the Concurrency checklist: "check every method that reads or writes shared state — including getters and read-only paths — not just mutating methods."
  2. Extend the must-not-flag typo rule: "do not flag typos in comments or test fixtures that describe intentional misspellings" (covers the `teh` comment case).
  3. Tell reviewers to derive new-file line numbers from the diff hunk headers (`@@` ranges), since line drift persists even with snippets quoted.
  4. Clarify high vs medium boundary: "high = the documented contract is violated for typical inputs; medium = wrong results only for edge/remainder cases" to fix the `totalPages` overrating.

## Per-fixture results
#### [01-sql-injection](sql-injection.md) - 95.0
<details><summary>AI response</summary>

### Summary
This change adds a stored procedure `FindUserByName` that builds a SQL query via string concatenation of user input, plus a commented-out inline concatenation example. It introduces a classic SQL injection vulnerability.

### Findings

- **[critical] src/users.sql:6-8 — SQL injection via string concatenation in `sp_executesql`**
  - Problem: `@name` is concatenated directly into the query string and executed with `sp_executesql`. Any caller-supplied name like `' OR '1'='1` (or `'; DROP TABLE users; --`) can read/modify arbitrary data. This is a textbook exploitable injection.
  - Fix: Don't use dynamic SQL at all — write a plain parameterized statement inside the procedure:
    ```sql
    CREATE PROCEDURE FindUserByName
        @name NVARCHAR(255)
    AS
    BEGIN
        SELECT id, name, email FROM users WHERE name = @name
    END
    ```
    If dynamic SQL is truly required (it isn't here), use parameter binding: `EXEC sp_executesql @query, N'@name NVARCHAR(255)', @name = @name` with `@name` as a placeholder inside the query string.
  - Code snippet:
    ```
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **[medium] src/users.sql:11 — second injection-prone snippet committed to source**
  - Problem: The trailing line `WHERE name = '" + name + "'"` appears to be leftover application-side pseudocode (the `" + name + "` syntax is not valid T-SQL). Even though it's labeled "Alternative vulnerable approach," it is not a comment — it's invalid SQL in the file and models an unsafe pattern. It will break any attempt to run the script and normalizes the same injection flaw in code that touches the DB.
  - Fix: Delete it, or turn it into an actual comment (`--`) if it's meant as documentation — though there's no reason to ship a known-vulnerable example; keep it out of the file.
  - Code snippet:
    ```
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

### Verdict
request changes

</details>

#### [02-off-by-one](off-by-one.md) - 95.0
<details><summary>AI response</summary>

### Summary
Adds `getPage`/`totalPages` pagination helpers. Both functions have off-by-one errors relative to their documented contracts: `getPage` treats `page` as 0-based despite a 1-based docstring, and `totalPages` floors instead of ceils, undercounting pages whenever there's a remainder.

### Findings
- **high src/pagination.js:7 - `getPage` uses 0-based indexing despite documented 1-based contract**
  - Problem: The doc says "1-based page number," but `start = page * pageSize` means `getPage(items, 1, 10)` returns items 10–19 instead of 0–9, silently skipping the first page of data; `getPage(items, 0, 10)` is what actually returns the first page.
  - Fix: `const start = (page - 1) * pageSize;` (and optionally guard `page < 1`).
  - Code snippet:
    ```js
    const start = page * pageSize;
    ```
- **high src/pagination.js:16 - `totalPages` floors, dropping the last partial page**
  - Problem: `Math.floor(items.length / pageSize)` returns 0 pages for 5 items with pageSize 10, and 2 pages for 25 items with pageSize 10 — the remaining 5 items become unreachable via `getPage`. Should round up.
  - Fix: `return Math.ceil(items.length / pageSize);`
  - Code snippet:
    ```js
    return Math.floor(items.length / pageSize);
    ```
- **low src/pagination.js:16 - no guard for `pageSize <= 0`**
  - Problem: `pageSize = 0` yields `NaN`/`Infinity` from `totalPages` and empty slices from `getPage`; a caller passing a bad config silently gets nonsense.
  - Fix: validate `pageSize > 0` and `Number.isInteger(pageSize)`, throwing or returning a sensible default.
  - Code snippet:
    ```js
    return Math.floor(items.length / pageSize);
    ```

### Verdict
request changes

</details>

#### [03-race-condition](race-condition.md) - 85.0 (HARD FAIL)
<details><summary>AI response</summary>

### Summary
Adds a `RequestStats` class that counts requests per path in a `Dictionary`. Functionally correct for single-threaded use, but two real issues: the type is not thread-safe (a problem for a per-request counter in normal server use), and `Snapshot()` leaks the mutable internal dictionary.

### Findings

- **high src/counter.cs:8-18 - `Inc` is not thread-safe (check-then-act race)**
  - Problem: A request counter is almost always called concurrently. `ContainsKey` then `counts[path]++` is a check-then-act pattern, and `Dictionary` itself is unsafe for concurrent reads/writes — concurrent calls can lose increments or corrupt the internal hashtable (which can hang or throw).
  - Fix: Guard all access with a lock, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate(path, 1, (_, c) => c + 1)` / `GetOrAdd`+interlocked counting.
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    else
    {
        counts[path] = 1;
    }
    ```

- **medium src/counter.cs:25-28 - `Snapshot()` returns the live internal dictionary**
  - Problem: Returning `counts` directly lets callers mutate internal state and iterate it while `Inc` mutates it — a caller doing `foreach` over the snapshot during concurrent writes will get `InvalidOperationException` or torn data. It also violates the implied contract of a "snapshot".
  - Fix: Return a copy under the lock: `lock (gate) return new Dictionary<string,int>(counts);` or use an immutable/read-only view.
  - Code snippet:
    ```csharp
    public Dictionary<string, int> Snapshot()
    {
        return counts;
    }
    ```

- **nit src/counter.cs:10-18 - `Inc` can be simplified**
  - `if (!counts.TryGetValue(path, out var c)) c = 0; counts[path] = c + 1;` avoids double lookup, though this is moot if you switch to `ConcurrentDictionary`.

### Verdict
request changes — the concurrency and encapsulation issues should be fixed before this ships, since the class will almost certainly be used from multiple threads.

</details>

#### [04-missing-error-handling](missing-error-handling.md) - 100.0
<details><summary>AI response</summary>

### Summary
Adds config loading helpers: `loadConfig` (sync file read + JSON parse), `writeBackup` (sync file write), and `fetchRemoteConfig` (HTTP fetch). The change is small but has a real resource leak and missing error handling.

### Findings

- **[medium] src/config.ts:15-18 - `writeBackup` never closes the file descriptor**
  - Problem: `fs.openSync` returns an fd that is never released with `fs.closeSync`. Each call leaks a descriptor; under repeated calls this can exhaust the fd limit and crash the process. Also, if `fs.writeSync` throws, the fd is leaked even on the error path.
  - Fix: use `fs.writeFileSync(path, data)` (simplest), or wrap in try/finally:
    ```ts
    const fd = fs.openSync(path, "w");
    try {
      fs.writeSync(fd, data);
    } finally {
      fs.closeSync(fd);
    }
    ```
  - Code snippet:
    ```ts
    const fd = fs.openSync(path, "w");
    fs.writeSync(fd, data);
    ```

- **[medium] src/config.ts:22 - `fetchRemoteConfig` doesn't check `res.ok`**
  - Problem: `fetch` resolves on HTTP errors (404, 500). `res.json()` on an error page will either throw an opaque parse error or return a non-config body that is silently cast to `AppConfig`. A failed remote fetch produces a malformed config rather than a clear error.
  - Fix:
    ```ts
    const res = await fetch(url);
    if (!res.ok) throw new Error(`fetchRemoteConfig: HTTP ${res.status} from ${url}`);
    return res.json();
    ```
  - Code snippet:
    ```ts
    const res = await fetch(url);
    return res.json();
    ```

- **[low] src/config.ts:7-9 - `loadConfig` returns unvalidated `JSON.parse` output as `AppConfig`**
  - Problem: `cfg` is `any`; a missing or mistyped `port`/`dbUrl` in the file silently propagates as `undefined` into the typed `AppConfig`. Validation here materially improves safety since the config feeds port/DB setup.
  - Fix: validate required fields after parsing, e.g. `if (typeof cfg.port !== "number" || typeof cfg.dbUrl !== "string") throw new Error("invalid config");`
  - Code snippet:
    ```ts
    const cfg = JSON.parse(raw);
    return cfg;
    ```

### Verdict
request changes

</details>

#### [05-clean-refactor](clean-refactor.md) - 100.0
<details><summary>AI response</summary>

### Summary
The change refactors `OrderCalculator` from a manual accumulation loop to `items.Sum(...)` plus `subtotal * (1 + taxRate)`, and adds the required `using` directives (`System.Linq`, `System.Collections.Generic`). The refactor is functionally equivalent — both versions throw on a null `items` argument and both produce identical results for empty and populated lists.

### Findings
No issues found.

The only theoretical concern would be a null `items` argument throwing `NullReferenceException`, but the original code had the exact same behavior, so this is not a regression introduced by the diff. `using System;` is arguably unnecessary (no BCL types outside collections/LINQ are used), which is a nit at most.

### Verdict
approve

</details>

#### [06-typos](typos.md) - 88.3
<details><summary>AI response</summary>

### Summary
Adds an account creation function with normalization, options, and a getter. It contains several functional typos that break behavior (an ignored option key, a `.lenght` typo that disables validation) plus a misspelled public field/API name.

### Findings
- **[high] src/accounts.ts:23 - `opts.maxRetires` is a misspelled key, so caller options are silently ignored**
  - Problem: `Partial<typeof DEFAULTS>` has no `maxRetires` key; any caller-supplied `maxRetries` is ignored and the default is always used. TS may flag the typo at compile time, but if it slips through (e.g., `as any` callers) it silently misbehaves.
  - Fix: `const retries = opts.maxRetries ?? DEFAULTS.maxRetries;`
  - Code snippet: `const retries = opts.maxRetires ?? DEFAULTS.maxRetries;`
- **[high] src/accounts.ts:25 - `usernam.lenght` disables length validation**
  - Problem: `lenght` is undefined, so `usernam.lenght < 3` is always false; the "at least 3 characters" check never fires and invalid usernames are accepted. (At runtime this is `undefined < 3` → false, not a throw.)
  - Fix: `if (usernam.length < 3) {`
  - Code snippet:
    ```
    const usernam = input.username.trim().toLowerCase();
    if (usernam.lenght < 3) {
    ```
- **[medium] src/accounts.ts:7,36,41 - misspelled `adress` becomes part of the public API**
  - Problem: `Account.adress`, `getAdress` bake a typo into the exported interface and function name — costly to fix once consumers depend on it.
  - Fix: rename to `address` / `getAddress` everywhere (interface, `createAccount` body, getter).
  - Code snippet:
    ```
    adress: string;
    export function getAdress(account: Account): string {
    ```
- **[low] src/accounts.ts:24,31 - typos in identifier, error message, and comment**
  - Problem: `usernam` should be `username`; "charcters" in the user-facing error message should be "characters"; "recieve" in the doc comment should be "receive"; "teh" in the comment on line ~45 should be "the" (the `"teh quick brown fox"` string itself appears to be deliberate test data).
  - Fix: correct each spelling.
  - Code snippet:
    ```
    throw new Error("Username must be at least 3 charcters long");
    // We recieve the raw form input
    // tolerates teh common typo
    ```
- **[low] src/accounts.ts:1 - doc claim not implemented**
  - Problem: JSDoc says the function "sends a welcome email" but no email logic exists. Either implement or correct the comment.
  - Code snippet: `* Creates a new account and sends a welcome email.`

### Verdict
request changes

</details>

---
