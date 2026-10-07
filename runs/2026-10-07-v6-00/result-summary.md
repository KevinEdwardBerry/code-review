# v6 - 2026-10-07 — Detailed results

- Prompt: `prompts/code-review.v6.md`
- Reviewer: subagent_explore (unknown)
- Judge: subagent_general (unknown)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **92.5/100** (+9.4 vs v5)
- Hard fails: none

## What changed
```diff
--- /Users/kevinberry/src/code-review/prompts/code-review.v5.md	2026-10-07 17:34:11
+++ /Users/kevinberry/src/code-review/prompts/code-review.v6.md	2026-10-07 17:53:46
@@ -20,14 +20,14 @@
 - **nit**: non-actionable or cosmetic observation (e.g. formatting, comment typo, consistent local abbreviation).
 
 ### Severity examples
-- A 1-based `getPage` helper that computes `start = page * pageSize` is **high** because every typical caller gets the wrong page.
-- A `totalPages` helper that floors the result is **medium** because it only drops the final partial page.
-- A reachable SQL concatenation in a user-facing query is **critical**.
-- A trailing invalid/non-executable SQL snippet showing the same pattern is **low/nit**, not a separate critical or high finding.
-- A missing HTTP `res.ok` check in a remote fetch is **medium** because it only matters on non-2xx responses.
+- A documented 1-based parameter treated as 0-based is **high** because every typical caller gets the wrong result.
+- A count or total helper that drops the final partial result (e.g. floors a division that should be ceilinged) is **medium**.
+- User input concatenated directly into an executable query or command string in a reachable code path is **critical**.
+- A non-reachable, malformed snippet that merely repeats a vulnerable pattern (e.g. leftover documentation or test data) is **low/nit**, not a separate critical or high finding.
+- A missing status or error check on a remote or I/O call is **medium** because it only matters on failure paths.
 
 ## Citing exact `file:line`
-Cite the new-file line number on which the defect occurs, not the function header or hunk start. Derive it from the `@@` hunk header:
+Every finding must include an exact `file:line` citation in its title (or `file:start-end` if it spans adjacent lines). Cite the new-file line number on which the defect occurs, not the function header or hunk start. Derive it from the `@@` hunk header.
 
 For a hunk like:
 ```
@@ -47,17 +47,52 @@
 - 8 `    raw.close()` (added)
 - 9 `    return content` (added)
 
-If a finding spans adjacent lines, use `file:start-end`; otherwise use a single `file:line`.
+For a second hunk like:
+```
+@@ -0,0 +1,5 @@
++app:
++  host: localhost
++  port: 3306
++  ssl: true
++  timeout: 30
+```
+`+1,5` means new-file line 1 is `app:` and the file runs through line 5; `port: 3306` is at line 3 and `timeout: 30` is at line 5.
 
 ## Rules
 - Report every distinct, actionable issue attributable to the change; there is no finding limit. Do not omit a real issue because it falls outside the checklist or another issue is more prominent.
 - Judge validation, performance, compatibility, and other concerns by concrete impact: do not dismiss them as optional, and do not report generic improvements without a demonstrated failure mode or meaningful risk.
 - Quote the relevant line(s) and explain the impact. Context may support a finding, but do not report pre-existing issues.
 - Do not invent or speculate. If the change is sound, say so and report only genuine nits (or none).
-- A clean, mathematically-equivalent rewrite (e.g. replacing a `foreach` accumulation with `items.Sum(...)` or `total + total*taxRate` with `subtotal * (1 + taxRate)`) is to be treated as behavior-preserving unless a reachable, concrete failure case is demonstrated. If no real defect is shown, the verdict must be `approve` or `approve with nits`, not `request changes`.
-- Do not flag literal string data, test fixtures, intentional domain terms, brand names, British/variant spellings, or consistently-used local variable abbreviations as typos. A typo in an identifier, key, API name, or user-facing string is a bug; a comment typo is a nit.
 - Order findings by severity, keep distinct defects separate, and give each a concrete fix. Be concise without sacrificing coverage.
 
+### Concurrency
+When a change introduces shared mutable state, review every method, property, getter, and read-only accessor that touches that state — not just mutators. Read-only paths need the same synchronization as writes; an unsynchronized read against a concurrent write can corrupt a non-thread-safe collection or throw (e.g. concurrent read and write to a shared map or list).
+
+### Behavior-preserving rewrites
+A clean, mathematically-equivalent rewrite is to be treated as behavior-preserving unless a reachable, concrete failure case is demonstrated. If no real defect is shown, the verdict must be `approve` or `approve with nits`, not `request changes`.
+
+**Worked example:** A diff that replaces
+```
+if user is None:
+    return "guest"
+return user.name
+```
+with
+```
+return "guest" if user is None else user.name
+```
+is a behavior-preserving refactor. Do not flag the conditional expression, the formatting, or any added `using` / `import` as a defect. Only point out genuine nits with a concrete failure mode.
+
+### Typos
+Check every text token in the diff — identifiers, keys, API names, user-facing strings, literal string data, and comments — for typos. A typo in an identifier, key, API name, or user-facing string is a bug. A typo in a comment is a nit. A typo in literal string data is actionable only when the string is user-facing or otherwise semantically meaningful; literal test data, fixtures, and example strings are not actionable even if misspelled.
+
+Do not flag terms in the Known acceptable typos list, brand names, British/variant spellings in proper names, or consistently-used local abbreviations.
+
+## Known acceptable typos
+If a project-specific exception list is provided below, do not flag those terms. If the list is absent or empty, use the defaults in the Typos rule.
+
+{{TYPO_EXCEPTIONS}}
+
 ## Output format
 ### Summary
 One or two sentences on what the change does and your overall assessment.

```

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-sql-injection | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | 5.0 |
| 02-off-by-one | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | 11.7 |
| 03-race-condition | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | 20.0 |
| 04-missing-error-handling | 3 | 3 | 3 | 3 | 2 | 3 | 3 | 96.7 | -3.3 |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 2 | 2 | 96.7 | 26.7 |
| 06-typos | 3 | 1 | 1 | 2 | 2 | 3 | 2 | 66.7 | -3.3 |

### Typo recall (fixture 06)

| Category | Found/Total |
|---|---|
| misspelling | 1/1 |
| swap | 2/2 |
| missing_letter | 2/2 |

## Observations / next changes
### Patterns in misses and false positives
- 06-typos: the review still flags the must-not-flag local abbreviation `usernam` and the literal `TEXT` (`teh`) as typos, and over-ranks `lenght` to critical (expected high) and `adress` to high (expected medium). The must-not-flag examples are still not specific enough.
- 03-race-condition: the reviewer identified all three concurrency issues but collapsed the `Inc` race and the unsynchronized `Count` read into a single medium finding. Expected high severity for non-atomic check-then-write and unlocked read was not fully respected.
- 02-off-by-one and 04-missing-error-handling are near-perfect; the prompt's severity examples and hunk-header guidance worked.
- 05-clean-refactor now correctly reports no issues, fixing the previous fabricated `using` complaint.

### Suggested prompt changes
1. Add worked examples showing that non-atomic `Inc` and unsynchronized `Count`/`Snapshot` on a shared `Dictionary` are high (not medium) because they can corrupt or throw under normal concurrent use.
2. Add concrete must-not-flag typo examples: a consistently-used local abbreviation like `usernam`, an exported literal constant like `TEXT = "teh ..."`, and British/brand spellings like `Colour` in a proper name.
3. Clarify that behavior-changing typos causing logic to silently fail (e.g., `lenght`) are `high`, not `critical`, unless they introduce a crash, data loss, or security issue.
4. Make exact `file:line` citations a hard requirement: a finding without a `file:line` or with a wrong one should be considered not actionable.

## Per-fixture results
### 01-sql-injection

- [01-sql-injection.md](01-sql-injection.md)

<details><summary>Full AI response for 01-sql-injection</summary>

### Summary
The change adds a SQL Server stored procedure `FindUserByName` that builds a query via string concatenation of user input, plus a stray appended line of non-SQL text that mixes code fragments into the file. The procedure contains a critical SQL injection vulnerability; the trailing line is malformed and only mirrors the same vulnerable pattern.

### Findings

- **[critical] src/users.sql:9 - SQL injection via string concatenation in dynamic SQL**
  - Problem: The user-supplied `@name` is concatenated directly into `@query` and executed via `sp_executesql`. An input like `'; DROP TABLE users; --` executes arbitrary SQL — the textbook injection pattern in a reachable, callable procedure.
  - Fix: Either use a plain parameterized statement (`SELECT id, name, email FROM users WHERE name = @name`) — no dynamic SQL is needed here — or parameterize properly: `EXEC sp_executesql @query, N'@name NVARCHAR(255)', @name = @name`.
  - Code snippet:
    ```
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **[low] src/users.sql:12 - stray malformed non-SQL line appended to file**
  - Problem: `SELECT id, name, email FROM users WHERE name = '" + name + "'"` is not valid T-SQL — it looks like a leftover application-code fragment (`name` is not a SQL identifier/string concatenation here). It will cause a syntax error if the file is executed as a script, and it merely repeats the vulnerable pattern without being reachable. Likely committed by accident.
  - Fix: Remove the line entirely.
  - Code snippet:
    ```
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

### Verdict
`request changes`


</details>

### 02-off-by-one

- [02-off-by-one.md](02-off-by-one.md)

<details><summary>Full AI response for 02-off-by-one</summary>

### Summary
The change adds two pagination helpers (`getPage` and `totalPages`). Both contain off-by-one/math errors that make them wrong for ordinary callers.

### Findings

- **[high] src/pagination.js:7 - `getPage` treats the documented 1-based `page` as 0-based**
  - Problem: The docstring says the function takes "a 1-based page number," but `const start = page * pageSize` computes the offset as if `page` were 0-based. For `page = 1`, `start = pageSize`, so the first page of results is skipped entirely; `page = 0` returns the first page. Every typical caller gets the wrong slice.
  - Fix: Use `const start = (page - 1) * pageSize;` (and optionally validate `page >= 1`).
  - Code snippet:
    ```
    function getPage(items, page, pageSize) {
      const start = page * pageSize;
    ```

- **[medium] src/pagination.js:15 - `totalPages` drops the final partial page**
  - Problem: `Math.floor(items.length / pageSize)` undercounts when `items.length` is not an exact multiple of `pageSize` (e.g. 25 items, pageSize 10 → 2 instead of 3). The last partial page becomes unreachable via `getPage`.
  - Fix: Use `Math.ceil(items.length / pageSize)`. Note that for `pageSize <= 0` this yields `Infinity`/`NaN`; consider validating `pageSize > 0` (also protects `getPage`).
  - Code snippet:
    ```
    function totalPages(items, pageSize) {
      return Math.floor(items.length / pageSize);
    ```

### Verdict
`request changes`


</details>

### 03-race-condition

- [03-race-condition.md](03-race-condition.md)

<details><summary>Full AI response for 03-race-condition</summary>

### Summary
The change adds a `RequestStats` class wrapping a `Dictionary<string, int>` to count requests per path. The core counting logic is correct, but `Snapshot()` leaks the internal mutable dictionary and the class is unsafe under concurrent access, which is a realistic scenario for per-request statistics.

### Findings

- **medium** src/counter.cs:27 — `Snapshot()` returns the live internal dictionary, exposing mutable internal state
  - Problem: Returning `counts` directly gives every caller a reference to the private dictionary. Callers can add, remove, or clear entries, silently corrupting the stats; they can also mutate it while `Inc`/`Count` run, which can throw or corrupt the non-thread-safe `Dictionary`. It also breaks the encapsulation the class is trying to provide.
  - Fix: Return a copy: `return new Dictionary<string, int>(counts);` (or expose `IReadOnlyDictionary<string, int>` backed by a copied dictionary).
  - Code snippet:
    ```
    public Dictionary<string, int> Snapshot()
    {
        return counts;
    }
    ```

- **medium** src/counter.cs:9-18 — No synchronization on a per-request counter; `Dictionary` is not thread-safe
  - Problem: For a request-statistics type, `Inc` will plausibly be called from multiple request-handling threads. Concurrent `Inc`/`Count`/`Snapshot` calls on a shared `Dictionary` can corrupt internal buckets or throw `IndexOutOfRangeException`/`InvalidOperationException`. If the class is only ever used single-threaded this is fine, but nothing documents or enforces that.
  - Fix: Guard all three methods with a `lock` on a private object, or use `ConcurrentDictionary<string, int>` with `AddOrUpdate`/`GetOrAdd` (note `ConcurrentDictionary.GetEnumerator` is snapshot-safe, which also fixes the `Snapshot` issue).
  - Code snippet:
    ```
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    ```

- **low** src/counter.cs:11-18 — Double dictionary lookup in `Inc` (`ContainsKey` then indexer)
  - Problem: `ContainsKey` + indexer performs two hash lookups per call; on a hot request path this is wasteful. Same pattern in `Count`.
  - Fix: Use a single lookup: `counts.TryGetValue(path, out var n); counts[path] = n + 1;` (or `CollectionsMarshal.GetValueRefOrAddDefault` on .NET Core for zero extra lookups).
  - Code snippet:
    ```
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    ```

### Verdict
`request changes`


</details>

### 04-missing-error-handling

- [04-missing-error-handling.md](04-missing-error-handling.md)

<details><summary>Full AI response for 04-missing-error-handling</summary>

### Summary
Adds a config module with `loadConfig`, `writeBackup`, and `fetchRemoteConfig`. The change is small but leaves a file-descriptor leak and lacks response validation on the remote fetch path.

### Findings
- **[medium] src/config.ts:15-16 - `writeBackup` never closes the file descriptor**
  - Problem: `fs.openSync` returns an fd that is written to but never closed. Repeated calls leak descriptors until process limits are hit; also, without a `try/finally`, a `writeSync` throw leaks the fd immediately.
  - Fix: wrap in `try { fs.writeSync(fd, data); } finally { fs.closeSync(fd); }`, or simpler, use `fs.writeFileSync(path, data)`.
  - Code snippet:
    ```ts
    const fd = fs.openSync(path, "w");
    fs.writeSync(fd, data);
    ```
- **[medium] src/config.ts:21-22 - `fetchRemoteConfig` ignores HTTP status**
  - Problem: `res.json()` is returned regardless of `res.ok`; a 404/500 body is parsed and returned as `AppConfig`, or `res.json()` rejects with an opaque parse error. Also, no timeout means the promise can hang indefinitely.
  - Fix: check `if (!res.ok) throw new Error(...)` before parsing, and consider an `AbortSignal`/timeout.
  - Code snippet:
    ```ts
    const res = await fetch(url);
    return res.json();
    ```
- **[low] src/config.ts:11 - `loadConfig` returns unvalidated JSON as `AppConfig`**
  - Problem: `JSON.parse` result is returned unchecked; a config missing `port`/`dbUrl` silently produces a malformed `AppConfig` and `undefined` downstream rather than failing at load time.
  - Fix: validate required fields/types after parsing and throw a descriptive error.
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
The change refactors `OrderTotal` from a manual accumulation loop to a LINQ `Sum` and algebraically rewrites `total + total * taxRate` as `subtotal * (1 + taxRate)`. The two formulations are mathematically equivalent over `decimal` arithmetic, and LINQ `Sum` on an empty list returns 0, matching the old behavior. This is a behavior-preserving rewrite.

### Findings
No issues found.

Minor observations (not defects):
- The rewrite `subtotal * (1 + taxRate)` performs one fewer multiplication, which can infinitesimally change rounding in pathological decimal cases, but this is not a reachable, concrete failure mode — the result is equally correct.
- `items.Sum(...)` throws `ArgumentNullException` if `items` is null, same as the prior `foreach` (which threw `NullReferenceException`) — same failure domain, not a regression.
- The `using System;` import appears unused, but removing it is cosmetic at most.

### Verdict
`approve`


</details>

### 06-typos

- [06-typos.md](06-typos.md)

<details><summary>Full AI response for 06-typos</summary>

### Summary
Adds an account-creation service with an `Account` interface, defaults, and helpers. The change contains multiple typos, several of which are behavior-breaking: a property access on a misspelled field that will crash at runtime, and a misspelled option key that silently ignores caller input.

### Findings

- **critical src/accounts.ts:22 - `usernam.lenght` is a typo'd property access that throws on every call**
  - Problem: `lenght` is not a property of `string`; `usernam.lenght` is `undefined`, and `undefined < 3` evaluates to `false` — so the validation silently never fires rather than throwing. Wait — correction: it doesn't throw, it silently disables the length check entirely, so any username (including empty) is accepted.
  - Fix: rename to `usernam.length`.
  - Code snippet:
    ```ts
    if (usernam.lenght < 3) {
    ```

- **high src/accounts.ts:6 - Public `Account` field misspelled `adress`**
  - Problem: `adress` becomes part of the public API surface (interface field, constructor input, `getAdress` accessor). Callers must use the misspelled key; fixing later is a breaking change. `email`/`username` are correctly spelled, so this is a typo, not a convention.
  - Fix: rename to `address` everywhere (`Account.adress`, `input.adress`, `account.adress`, `getAdress` → `getAddress`) before this ships.
  - Code snippet:
    ```ts
    adress: string;
    ```

- **high src/accounts.ts:19 - Option key `maxRetires` never matches caller input**
  - Problem: `opts` is typed `Partial<typeof DEFAULTS>`, whose key is `maxRetries`. `opts.maxRetires` is always `undefined` (and a type error under strict TS), so any caller-supplied `maxRetries` is silently ignored and the default is always used.
  - Fix: use `opts.maxRetries ?? DEFAULTS.maxRetries`.
  - Code snippet:
    ```ts
    const retries = opts.maxRetires ?? DEFAULTS.maxRetries;
    ```

- **low src/accounts.ts:24 - User-facing error message misspells "characters"**
  - Problem: `"Username must be at least 3 charcters long"` is shown to users.
  - Fix: correct to "characters".
  - Code snippet:
    ```ts
    throw new Error("Username must be at least 3 charcters long");
    ```

- **low src/accounts.ts:40 - Exported literal `TEXT` contains "teh"**
  - Problem: `"teh quick brown fox"` is exported constant data; if used in user-facing output this is a visible typo. If it's dead/test data, impact is minimal — flagging as low given the export makes it plausibly meaningful.
  - Fix: correct to "the" or remove if unused.
  - Code snippet:
    ```ts
    export const TEXT = "teh quick brown fox";
    ```

- **nit src/accounts.ts:16 - Comment typo "recieve"**
  - Problem: JSDoc says "We recieve the raw form input…".
  - Fix: correct to "receive".
  - Code snippet:
    ```ts
     * We recieve the raw form input and normalize it.
    ```

- **nit src/accounts.ts:20 - Local variable `usernam` is misspelled**
  - Problem: Internal-only misspelling of `username`; harmless but propagates the typo pattern.
  - Fix: rename to `username` (and rename the `Account` field usage accordingly).

### Verdict
`request changes`


</details>

---
