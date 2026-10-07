# v5 - 2026-10-07 — Detailed results

- Prompt: `prompts/code-review.v5.md`
- Reviewer: subagent_explore (default subagent model)
- Judge: subagent_general (parent model)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **83.1/100** (+9.5 vs v4)
- Hard fails: 03-race-condition (missed_critical), 05-clean-refactor (fabricated)

## What changed
```diff
--- /Users/kevinberry/src/code-review/prompts/code-review.v4.md	2026-10-07 17:11:00
+++ /Users/kevinberry/src/code-review/prompts/code-review.v5.md	2026-10-07 17:34:11
@@ -12,17 +12,50 @@
 Trace relevant surrounding code, contracts, callers, tests, and configuration when available; distinguish regressions from pre-existing issues. If context is missing, do not present assumptions as facts.
 
 ## Severity
-- **critical**: exploitable vulnerability, data loss, or crash in normal use (e.g. SQL injection, auth bypass, core-path crash, corrupting race).
-- **high**: documented behavior is wrong on common paths (e.g. wrong pagination for typical inputs, ignored options, ineffective validation).
-- **medium**: incorrect behavior limited to edge cases, or costly user-facing/public API defects (e.g. dropped partial results, missing HTTP error checks, public API typos).
-- **low**: minor user-facing issues or defensive improvements with a concrete benefit (e.g. error-message typos, unused imports).
-- **nit**: non-actionable or cosmetic observations (e.g. formatting or comment typos).
+Rank by concrete impact. Downgrade if the impact is theoretical or only occurs on edge/failure/remainder cases.
+- **critical**: exploitable vulnerability, data loss, or crash in normal use (e.g. SQL injection, auth bypass, unhandled exception on the common path, a race that corrupts persisted state).
+- **high**: documented behavior is wrong on common, typical inputs; a missing invariant guaranteed to fail for ordinary callers.
+- **medium**: incorrect behavior limited to edge/remainder/failure cases, or costly public-API defects that are expensive to fix later.
+- **low**: minor user-facing issue or defensive improvement with a concrete benefit (e.g. user-facing error-message typo, unused import).
+- **nit**: non-actionable or cosmetic observation (e.g. formatting, comment typo, consistent local abbreviation).
 
+### Severity examples
+- A 1-based `getPage` helper that computes `start = page * pageSize` is **high** because every typical caller gets the wrong page.
+- A `totalPages` helper that floors the result is **medium** because it only drops the final partial page.
+- A reachable SQL concatenation in a user-facing query is **critical**.
+- A trailing invalid/non-executable SQL snippet showing the same pattern is **low/nit**, not a separate critical or high finding.
+- A missing HTTP `res.ok` check in a remote fetch is **medium** because it only matters on non-2xx responses.
+
+## Citing exact `file:line`
+Cite the new-file line number on which the defect occurs, not the function header or hunk start. Derive it from the `@@` hunk header:
+
+For a hunk like:
+```
+@@ -1,4 +5,5 @@
+ def load():
+     raw = open("x")
+-    data = raw.read()
+-    return data
++    content = raw.read()
++    raw.close()
++    return content
+```
+`+5,5` means the hunk starts at new-file line 5. Count every hunk line without the leading `+`, `-`, or space markers:
+- 5 `def load():` (context)
+- 6 `    raw = open("x")` (context)
+- 7 `    content = raw.read()` (added)
+- 8 `    raw.close()` (added)
+- 9 `    return content` (added)
+
+If a finding spans adjacent lines, use `file:start-end`; otherwise use a single `file:line`.
+
 ## Rules
 - Report every distinct, actionable issue attributable to the change; there is no finding limit. Do not omit a real issue because it falls outside the checklist or another issue is more prominent.
 - Judge validation, performance, compatibility, and other concerns by concrete impact: do not dismiss them as optional, and do not report generic improvements without a demonstrated failure mode or meaningful risk.
-- Cite the closest relevant changed line(s), including for missing checks; quote the code and explain impact. Context may support a finding, but do not report pre-existing issues. Derive new-file line numbers from `@@` hunk headers (`+start,count` gives the first new-file line; count context and added lines from there).
-- Do not invent or speculate about issues. Do not flag intentional domain terms, names, abbreviations, or test data as typos. Mention material uncertainty when context is missing.
+- Quote the relevant line(s) and explain the impact. Context may support a finding, but do not report pre-existing issues.
+- Do not invent or speculate. If the change is sound, say so and report only genuine nits (or none).
+- A clean, mathematically-equivalent rewrite (e.g. replacing a `foreach` accumulation with `items.Sum(...)` or `total + total*taxRate` with `subtotal * (1 + taxRate)`) is to be treated as behavior-preserving unless a reachable, concrete failure case is demonstrated. If no real defect is shown, the verdict must be `approve` or `approve with nits`, not `request changes`.
+- Do not flag literal string data, test fixtures, intentional domain terms, brand names, British/variant spellings, or consistently-used local variable abbreviations as typos. A typo in an identifier, key, API name, or user-facing string is a bug; a comment typo is a nit.
 - Order findings by severity, keep distinct defects separate, and give each a concrete fix. Be concise without sacrificing coverage.
 
 ## Output format
@@ -39,7 +72,7 @@
 If there are none, write "No issues found."
 
 ### Verdict
-One of: approve, approve with nits, request changes.
+One of: `approve`, `approve with nits`, `request changes`.
 
 ## Diff
 {{DIFF}}
```

## Scores (0-3, AI judge)

| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|---|
| 01-sql-injection | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 | +16.7 |
| 02-off-by-one | 3 | 2 | 3 | 2 | 3 | 3 | 3 | 88.3 | +6.6 |
| 03-race-condition | 1 | 3 | 3 | 2 | 3 | 3 | 3 | 75.0 | -3.3 |
| 04-missing-error-handling | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +5.0 |
| 05-clean-refactor | 3 | 1 | 2 | 2 | 1 | 3 | 3 | 70.0 | +25.0 |
| 06-typos | 2 | 1 | 3 | 2 | 3 | 3 | 2 | 70.0 | +6.7 |

### Typo recall (fixture 06)

| Category | Found/Total |
|---|---|
| misspelling | 1/1 |
| swap | 2/2 |
| missing_letter | 2/3 |

## Observations / next changes

### Patterns in misses and false positives
- 03-race-condition: the prompt already tells the reviewer to check state, concurrency, and data integrity, but it still missed the `Count` unsynchronized read. The model treated the `Inc` race and `Snapshot` leak as sufficient and did not review the read-only `Count` accessor.
- 05-clean-refactor: despite the new behavior-preserving rule, the reviewer fabricated a nit about unnecessary `using` directives and mis-cited `src/totals.cs:2`, showing the clean-refactor rule still needs reinforcement.
- 06-typos: the reviewer flagged `teh` in a string constant and invented a `console.log` side-effect finding, and missed the consistent local `usernam` abbreviation. The must-not-flag list is still being ignored for literal data and local abbreviations.
- Line numbers remain off in 02, 03, and 06, indicating the new hunk-header example needs to be more explicit or reinforced.

### Suggested prompt changes
1. Add a concrete, worked clean-refactor example and explicitly forbid style/usings findings on behavior-preserving rewrites.
2. Strengthen the concurrency checklist to explicitly require reviewing all read-only accessors and getters that touch shared mutable state, not just mutators.
3. Add a second `@@` hunk-header counting example and make exact `file:line` citations a stated requirement for every finding.
4. Clarify that literal string constants, test fixtures, British spellings in proper names, and consistently-used local abbreviations are not actionable typos (only nits if flagged at all).

## Per-fixture results

### 01-sql-injection

- [01-sql-injection.md](01-sql-injection.md)



<details><summary>Full AI response for 01-sql-injection</summary>



### Summary
The change adds a SQL Server stored procedure that builds a query by concatenating an input parameter directly into a dynamic SQL string, plus a trailing invalid SQL fragment. The dynamic SQL is trivially injectable.

### Findings
- **[critical] src/users.sql:8 — SQL injection via string concatenation in `FindUserByName`**
  - Problem: `@name` is interpolated into the SQL text executed by `sp_executesql`. Any caller-supplied value like `' OR 1=1 --` escapes the string literal and executes arbitrary SQL, exposing/dropping data. This is a textbook SQL injection reachable through the procedure's only parameter.
  - Fix: Either use a plain static statement (`SELECT id, name, email FROM users WHERE name = @name`) or parameterize the dynamic SQL: `EXEC sp_executesql N'SELECT ... WHERE name = @n', N'@n NVARCHAR(255)', @n = @name`.
  - Code snippet:
    ```sql
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **[low] src/users.sql:12 — invalid, non-executable SQL fragment left in file**
  - Problem: `SELECT id, name, email FROM users WHERE name = '" + name + "'"` is not valid SQL — it looks like a pasted application-layer snippet (e.g. C# string concatenation) and will cause a syntax error if the file is executed as a script. It also mirrors the same injectable pattern.
  - Fix: Remove the line, or if it documents a query to be implemented elsewhere, move it into the proper parameterized statement.
  - Code snippet:
    ```sql
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

### Verdict
`request changes`



</details>



### 02-off-by-one

- [02-off-by-one.md](02-off-by-one.md)



<details><summary>Full AI response for 02-off-by-one</summary>



### Summary
Adds two pagination helpers. Both contain off-by-one errors: `getPage` treats the documented 1-based page as 0-based, and `totalPages` floors instead of ceiling.

### Findings
- **[high] src/pagination.js:5-6 - 1-based `page` used as 0-based**
  - Problem: The docblock says `page` is 1-based, but `start = page * pageSize` skips the first `pageSize` items for page 1. Every typical caller receives the wrong page; the last page becomes unreachable.
  - Fix: `const start = (page - 1) * pageSize;`
  - Code snippet:
    ```
    function getPage(items, page, pageSize) {
      const start = page * pageSize;
    ```

- **[medium] src/pagination.js:15 - `totalPages` floors the result**
  - Problem: `Math.floor(items.length / pageSize)` drops the final partial page, so e.g. 10 items with pageSize 4 reports 2 pages instead of 3. Wrong only when `items.length % pageSize !== 0`.
  - Fix: `return Math.ceil(items.length / pageSize);`
  - Code snippet:
    ```
    return Math.floor(items.length / pageSize);
    ```

- **[low] src/pagination.js:15 - `totalPages` ignores empty-array edge case**
  - Problem: For `items.length === 0` the function returns `0`; many consumers expect at least 1 page (or handle 0 explicitly). With `Math.ceil` it still returns 0, which may be acceptable — just flag it.
  - Fix: Document the contract or `return Math.max(1, Math.ceil(items.length / pageSize));` if a minimum of 1 is desired.
  - Code snippet:
    ```
    return Math.floor(items.length / pageSize);
    ```

### Verdict
`request changes`



</details>



### 03-race-condition

- [03-race-condition.md](03-race-condition.md)



<details><summary>Full AI response for 03-race-condition</summary>



### Summary
The change adds a `RequestStats` class that counts requests per path using a plain `Dictionary<string, int>`. It is simple and correct for single-threaded use, but it has two real defects: it is not thread-safe and `Snapshot` leaks the mutable internal state.

### Findings
- **[high] src/counter.cs:10-17 - `Inc` is not thread-safe**
  - Problem: A request counter is almost always invoked concurrently. `Dictionary` does not tolerate concurrent mutation; two simultaneous `Inc` calls can lose increments, and concurrent write/read can corrupt internal buckets (in older runtimes this could even hang or throw). No locking or `ConcurrentDictionary` is used.
  - Fix: Use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or guard all accesses with a `lock`.
  - Code snippet:
    ```
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    ```

- **[medium] src/counter.cs:29 - `Snapshot` returns the mutable internal dictionary**
  - Problem: `return counts;` hands callers a live reference to private state. Callers can mutate it (corrupting stats), and iterating it while `Inc` runs throws `InvalidOperationException` — making it both an encapsulation break and a crash vector combined with the thread-safety issue above.
  - Fix: Return a copy, e.g. `return new Dictionary<string, int>(counts);` (under the lock / after `ToArray` if made concurrent), or expose `IReadOnlyDictionary` over a copied snapshot.
  - Code snippet:
    ```
    return counts;
    ```

### Verdict
request changes



</details>



### 04-missing-error-handling

- [04-missing-error-handling.md](04-missing-error-handling.md)



<details><summary>Full AI response for 04-missing-error-handling</summary>



### Summary
The change adds a new `src/config.ts` module with an `AppConfig` interface and three helpers: `loadConfig` (sync file read + JSON parse), `writeBackup` (sync file write), and `fetchRemoteConfig` (fetch + JSON parse). The logic is mostly straightforward, but `writeBackup` leaks its file descriptor and `fetchRemoteConfig` doesn't check the response status before parsing.

### Findings
- **[medium] src/config.ts:15-16 - File descriptor never closed in `writeBackup`**
  - Problem: `fs.openSync` returns a descriptor that is written to but never closed. Repeated calls (e.g., periodic backups) will leak descriptors and can eventually exhaust the process's file-descriptor limit; on some platforms writes may also not be fully flushed before the descriptor is GC'd. There is no `try/finally`, so even the write path doesn't guarantee cleanup.
  - Fix: Wrap in `try/finally` with `fs.closeSync(fd)`, or simply use `fs.writeFileSync(path, data)` which handles open/write/close atomically.
  - Code snippet:
    ```ts
    const fd = fs.openSync(path, "w");
    fs.writeSync(fd, data);
    ```

- **[medium] src/config.ts:20-21 - `fetchRemoteConfig` ignores HTTP error status**
  - Problem: `fetch` does not reject on non-2xx responses, so a 404/500 HTML error page will be passed to `res.json()`, producing either a confusing `SyntaxError` or silently wrong parsed data returned as `AppConfig`. Callers can't distinguish "server returned an error" from "server returned config".
  - Fix: Check `res.ok` (or `res.status`) before parsing and throw a descriptive error including the status and URL.
  - Code snippet:
    ```ts
    const res = await fetch(url);
    return res.json();
    ```

- **[low] src/config.ts:10-11 - `loadConfig` returns unvalidated `JSON.parse` result**
  - Problem: `JSON.parse` returns `any`; a well-formed JSON file missing `port`/`dbUrl` or with wrong types (e.g. `port: "abc"`) is returned as a valid `AppConfig`, so misconfiguration surfaces later as confusing failures rather than at load time.
  - Fix: Validate the parsed object (e.g., check `typeof cfg.port === "number"` and `typeof cfg.dbUrl === "string"`, or use a schema validator) and throw a descriptive error on mismatch.
  - Code snippet:
    ```ts
    const cfg = JSON.parse(raw);
    return cfg;
    ```

### Verdict
`request changes`



</details>



### 05-clean-refactor

- [05-clean-refactor.md](05-clean-refactor.md)



<details><summary>Full AI response for 05-clean-refactor</summary>



### Summary
The change rewrites `OrderTotal` from a manual `foreach` accumulation (`total + total * taxRate`) to a LINQ `Sum` (`subtotal * (1 + taxRate)`) in C#. For `decimal` arithmetic this is behavior-preserving: LINQ `Sum` uses the same `checked` decimal accumulation, throws `ArgumentNullException` on a null `items` just as `foreach` would, and `subtotal * (1 + taxRate)` produces identical results to `total + (total * taxRate)` given decimal's rounding semantics.

### Findings
- **[nit] src/totals.cs:2** - `System.Collections.Generic` and `System` usings may be unnecessary
  - Problem: `List<Item>` is used in the signature, so `System.Collections.Generic` is required; `System.Linq` is required for `Sum`. `System` itself is unused unless other members of the file need it. Harmless either way.
  - Fix: Remove `using System;` if unused.
  - Code snippet: `+using System;`

No functional defects identified — the rewrite is mathematically equivalent for `decimal`, and edge cases (null list, empty list, overflow) behave the same as before.

### Verdict
`approve`



</details>



### 06-typos

- [06-typos.md](06-typos.md)



<details><summary>Full AI response for 06-typos</summary>



### Summary
The change adds an `Account` interface and a `createAccount`/`getAdress` API to `src/accounts.ts`. It contains multiple typos in identifiers, two of which (`opts.maxRetires`, `usernam.lenght`) are outright compile errors (or runtime failures in untyped usage), and the `adress` field propagates a misspelling into the public API surface.

### Findings
- **[high] src/accounts.ts:26 - `usernam.lenght` is a typo; property `lenght` does not exist**
  - Problem: `string` has no `lenght` property. This is a TypeScript compile error (or `undefined < 3` → always-false validation / NaN comparisons in untyped JS), so the username-length check is broken on every call.
  - Fix: Rename to `usernam.length`.
  - Code snippet:
    ```ts
    if (usernam.lenght < 3) {
    ```
- **[high] src/accounts.ts:19 - `opts.maxRetires` does not match `DEFAULTS.maxRetries`**
  - Problem: `opts` is typed `Partial<typeof DEFAULTS>`, which only has `maxRetries`. Accessing `maxRetires` is a compile error; even if it compiled, the caller-supplied retry option would never be honored, silently falling back to the default.
  - Fix: Use `opts.maxRetries ?? DEFAULTS.maxRetries`.
  - Code snippet:
    ```ts
    const retries = opts.maxRetires ?? DEFAULTS.maxRetries;
    ```
- **[medium] src/accounts.ts:6 - Public interface field misspelled `adress`**
  - Problem: `Account.adress` bakes a misspelling into the public API; consumers must write `adress` forever, and fixing it later is a breaking change.
  - Fix: Rename to `address` (and update `input.adress`, `account.adress`, and `getAdress` accordingly).
  - Code snippet:
    ```ts
    adress: string;
    ```
- **[medium] src/accounts.ts:39 - Exported function name misspelled `getAdress`**
  - Problem: Same misspelling propagated to a public function name; renaming later breaks callers.
  - Fix: Rename to `getAddress`.
  - Code snippet:
    ```ts
    export function getAdress(account: Account): string {
    ```
- **[low] src/accounts.ts:23 - User-facing error message typo "charcters"**
  - Problem: `"Username must be at least 3 charcters long"` is shown to users with a typo.
  - Fix: `"Username must be at least 3 characters long"`.
  - Code snippet:
    ```ts
    throw new Error("Username must be at least 3 charcters long");
    ```
- **[low] src/accounts.ts:34 - `console.log` side effect in `createAccount`**
  - Problem: The function logs on every account creation; in a service this spams logs/stdout and may leak account identifiers. A library function should not log directly.
  - Fix: Remove the log or inject a logger.
  - Code snippet:
    ```ts
    console.log(`Created account for ${account.username}, retrying up to ${retries} times`);
    ```
- **[nit] src/accounts.ts:16 - Comment typo "recieve"**
  - Fix: "receive".
- **[nit] src/accounts.ts:43 - `TEXT = "teh quick brown fox"`** — likely a typo in a string constant; flag only if this isn't intentional fixture data.

### Verdict
`request changes`



</details>


