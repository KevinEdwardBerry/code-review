# v4 - 2026-10-07 — Detailed results

- Prompt: `prompts/code-review.v4.md`
- Reviewer: subagent_explore (default subagent model)
- Judge: subagent_general (parent model)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **73.6/100** (-19.7 vs v3)
- Hard fails: 05-clean-refactor (fabricated)

## What changed
```diff
--- /Users/kevinberry/src/code-review/prompts/code-review.v3.md	2026-10-07 16:42:32
+++ /Users/kevinberry/src/code-review/prompts/code-review.v4.md	2026-10-07 17:11:00
@@ -1,31 +1,29 @@
-You are a senior software engineer performing a code review of the diff below.
+You are a senior software engineer performing a thorough code review of the change below.
 
-## Goal
-Find real problems that matter, rank them by impact, and give the author a concrete fix for each. Do not pad the review.
+## Goal and scope
+Find every substantiated, actionable defect introduced or exposed by the change, assess its impact, and suggest a concrete fix. Review every file and hunk; do not stop after finding one issue. The checklist is illustrative, not exhaustive:
+- Correctness, edge cases, API contracts, callers, compatibility, and data or configuration changes.
+- Security, privacy, authorization, and untrusted input.
+- State, concurrency, transactions, data integrity, error handling, recovery, and resource lifetimes.
+- Performance and scalability.
+- Tests, deployment, and operational behavior when they affect correctness or safety.
+- Maintainability and naming when they create a concrete defect or meaningful future risk, including behavior-changing or public API typos.
 
-## Checklist
-1. Correctness: logic errors, off-by-one, null/undefined handling, wrong conditions, edge cases.
-2. Security: injection, unsafe input handling, secrets, authz/authn gaps.
-3. Concurrency and state: races, shared mutable state, missing locks/atomicity. Check every method that reads or writes shared state — including getters and read-only paths — not just mutating methods.
-4. Error handling: swallowed or missing errors, unchecked return values, resource leaks.
-5. Spelling and naming: misspelled, transposed, or missing-letter words in identifiers, config/JSON keys, strings, log messages, comments, and docs. A typo that changes behavior (e.g. a misspelled key or variable that silently resolves to nothing) is a bug, not a nit.
-6. Maintainability: only if it materially affects the change.
+Trace relevant surrounding code, contracts, callers, tests, and configuration when available; distinguish regressions from pre-existing issues. If context is missing, do not present assumptions as facts.
 
 ## Severity
-- **critical**: exploitable vulnerability, data loss, or crash in normal use. Examples: SQL injection via unparameterized queries, auth bypass, unhandled exceptions in core paths, race conditions that corrupt state.
-- **high**: incorrect behavior in common paths that violates documented contracts or breaks normal use for typical inputs. Examples: off-by-one that returns the wrong page for every caller, silently ignored caller options, validation that never fires.
-- **medium**: incorrect behavior confined to edge cases (e.g. remainder/partial results, unusual inputs), or user-facing/public API defects that are costly to fix later. Examples: missing HTTP error checks, unvalidated config, misspelled public API names, a count helper that drops a final partial result.
-- **low**: minor issues, cosmetic user-facing text, or defensive improvements. Examples: typos in error messages, missing null checks for defensive purposes, unused imports.
-- **nit**: style, comments, trivial typos, or observations that are not actionable. Examples: code formatting, comment typos, observations about equivalence.
+- **critical**: exploitable vulnerability, data loss, or crash in normal use (e.g. SQL injection, auth bypass, core-path crash, corrupting race).
+- **high**: documented behavior is wrong on common paths (e.g. wrong pagination for typical inputs, ignored options, ineffective validation).
+- **medium**: incorrect behavior limited to edge cases, or costly user-facing/public API defects (e.g. dropped partial results, missing HTTP error checks, public API typos).
+- **low**: minor user-facing issues or defensive improvements with a concrete benefit (e.g. error-message typos, unused imports).
+- **nit**: non-actionable or cosmetic observations (e.g. formatting or comment typos).
 
 ## Rules
-- Only report issues you can point to in the diff. Cite file and line (new-file line numbers where possible), and quote the relevant code snippet. Derive new-file line numbers from the `@@` hunk headers: the `+start,count` range gives the first new-file line of the hunk; count context and added lines from there.
-- Do not speculate about code you cannot see; if context is missing, say so briefly.
-- Do not flag intentional domain terms, brand names, abbreviations, or deliberate test data as typos — including comments or fixtures that describe intentional misspellings.
-- Do not invent problems. If the change is sound, say so and report only genuine nits (or none).
-- Group multiple typos of the same kind into one finding where sensible; never let nits bury high-impact issues.
-- For optional/validation extras (e.g., input validation, defensive checks): only flag if they materially improve safety or prevent a real failure mode. Do not rate extras higher than must-find issues.
-- Be constructive and concise.
+- Report every distinct, actionable issue attributable to the change; there is no finding limit. Do not omit a real issue because it falls outside the checklist or another issue is more prominent.
+- Judge validation, performance, compatibility, and other concerns by concrete impact: do not dismiss them as optional, and do not report generic improvements without a demonstrated failure mode or meaningful risk.
+- Cite the closest relevant changed line(s), including for missing checks; quote the code and explain impact. Context may support a finding, but do not report pre-existing issues. Derive new-file line numbers from `@@` hunk headers (`+start,count` gives the first new-file line; count context and added lines from there).
+- Do not invent or speculate about issues. Do not flag intentional domain terms, names, abbreviations, or test data as typos. Mention material uncertainty when context is missing.
+- Order findings by severity, keep distinct defects separate, and give each a concrete fix. Be concise without sacrificing coverage.
 
 ## Output format
 ### Summary
@@ -35,8 +33,8 @@
 Ordered from highest to lowest severity. For each:
 - **[severity] file:line - short title**
   - Problem: what is wrong and why it matters.
-  - Fix: concrete suggestion (corrected code or spelling).
-  - Code snippet: quote the problematic line(s) from the diff.
+  - Fix: concrete suggestion.
+  - Code snippet: quote the relevant line(s) from the diff.
 
 If there are none, write "No issues found."
 

```

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-sql-injection | 3 | 2 | 1 | 2 | 3 | 3 | 3 | 78.3 | -6.7 |
| 02-off-by-one | 3 | 3 | 1 | 2 | 2 | 3 | 3 | 81.7 | -8.3 |
| 03-race-condition | 3 | 2 | 1 | 2 | 3 | 3 | 3 | 78.3 | -16.7 |
| 04-missing-error-handling | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +0.0 |
| 05-clean-refactor | 3 | 0 | 0 | 1 | 1 | 3 | 1 | 45.0 | -55.0 |
| 06-typos | 2 | 1 | 2 | 2 | 2 | 3 | 3 | 63.3 | -31.7 |

### Typo recall (fixture 06)

| Category | Found/Total |
|---|---|
| misspelling | 1/1 |
| swap | 2/2 |
| missing_letter | 2/3 |

## Observations / next changes
### Patterns in misses and false positives
- 05-clean-refactor produced three false positives, including a medium-severity claim about decimal rounding that is explicitly in the must-not-flag list. The model invented a behavior difference in a mathematically-equivalent refactor.
- 01-sql-injection and 03-race-condition over-rated severity: a stray invalid SQL line and the `Inc` race were both ranked `critical` when the expected level is `high`, and several extras were ranked one level too high.
- 06-typos flagged the literal test string `teh` as a low finding, missed the cosmetic local `usernam`, and the line-number references were consistently off.
- 02-off-by-one ranked `totalPages` `high` and an input-validation extra `medium`, both one level above expected.

### Suggested prompt changes
1. Add a concrete clean-refactor example where the only acceptable verdict is `approve` or `approve with nits` and rewrites must be treated as behavior-preserving unless a real failure mode is demonstrated.
2. Add a worked severity-boundary example distinguishing `high` (wrong for typical inputs) from `medium` (wrong only on edge/remainder cases) using the pagination and SQL fixtures.
3. Clarify that literal string data, test fixtures, and intentional domain/British spellings must not be flagged, and that consistently-used local variable abbreviations are nits, not bugs.
4. Include a step-by-step `@@` hunk-header line-number example and reinforce that `file:line` citations must point at the exact buggy line, not the function header.

## Per-fixture results
### 01-sql-injection
- [01-sql-injection.md](01-sql-injection.md)

<details><summary>Full AI response for 01-sql-injection</summary>

### Summary
The change adds a SQL Server stored procedure `FindUserByName` that builds a query via string concatenation, plus a stray non-SQL fragment line. Both the procedure and the trailing line contain classic SQL injection, and the trailing line is also invalid SQL that will break the script.

### Findings
- **[critical] src/users.sql:8 - SQL injection via string concatenation in stored procedure**
  - Problem: `@name` is concatenated directly into the query text and executed with `sp_executesql`. A value like `' OR 1=1 --` (or `'; DROP TABLE users --`) lets an attacker read or modify arbitrary data.
  - Fix: Don't use dynamic SQL at all — `SELECT id, name, email FROM users WHERE name = @name` — or, if dynamic SQL is required, parameterize: `SET @query = N'... WHERE name = @p1'; EXEC sp_executesql @query, N'@p1 NVARCHAR(255)', @p1 = @name`.
  - Code snippet:
    ```sql
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **[critical] src/users.sql:12 - Stray line is both invalid T-SQL and SQL injection**
  - Problem: The line `SELECT id, name, email FROM users WHERE name = '" + name + "'` is not valid T-SQL — `name` is an undefined identifier and `"..."` string quoting/concatenation is wrong, so running this script fails outright. It also appears to be a pasted application-code fragment embedding the same injectable concatenation pattern.
  - Fix: Remove the line entirely; the procedure already covers the lookup. If it was meant as a query, replace with `WHERE name = @name` against a declared parameter.
  - Code snippet:
    ```sql
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

- **[low] src/users.sql:7 - DECLARE missing semicolon/terminator robustness**
  - Problem: `DECLARE @query NVARCHAR(MAX)` and `SET`/`EXEC` statements lack semicolons; while currently legal, a `BEGIN...END` block followed by more statements can hit parsing pitfalls (e.g., if a `WITH`/CTE or `THROW` is added later). Minor defensive issue.
  - Fix: Terminate statements with semicolons and initialize in one step: `DECLARE @query NVARCHAR(MAX) = N'...';`.
  - Code snippet:
    ```sql
    DECLARE @query NVARCHAR(MAX)
    ```

### Verdict
request changes

</details>

### 02-off-by-one
- [02-off-by-one.md](02-off-by-one.md)

<details><summary>Full AI response for 02-off-by-one</summary>

### Summary
Adds `getPage` and `totalPages` pagination helpers, but both contain off-by-one/truncation bugs: `getPage` treats `page` as 0-based despite documenting 1-based input, and `totalPages` floors instead of ceiling, dropping the last partial page.

### Findings
- **high src/pagination.js:6 - `getPage` uses 0-based offset despite 1-based contract**
  - Problem: The docstring says `page` is 1-based, but `start = page * pageSize` skips the first `pageSize` items on page 1 and returns the wrong slice for every page (page 1 returns items `pageSize..2*pageSize`, etc.).
  - Fix: Use `const start = (page - 1) * pageSize;`.
  - Code snippet:
    ```js
    const start = page * pageSize;
    ```

- **high src/pagination.js:15 - `totalPages` drops the last partial page**
  - Problem: `Math.floor(items.length / pageSize)` undercounts whenever `items.length` is not an exact multiple of `pageSize` (e.g. 25 items, pageSize 10 → 2 instead of 3), making the final page unreachable.
  - Fix: Use `Math.ceil(items.length / pageSize)`.
  - Code snippet:
    ```js
    return Math.floor(items.length / pageSize);
    ```

- **medium src/pagination.js:6-7 - invalid `page`/`pageSize` inputs produce silent wrong results**
  - Problem: `page <= 0` yields a negative `start`, so `items.slice` returns trailing items rather than an error or empty page; `pageSize <= 0` yields `NaN` (`totalPages`) or empty/incorrect slices. With 1-based semantics, page 0 should not silently return data.
  - Fix: Validate inputs, e.g. `if (page < 1) throw/return []` and `if (pageSize < 1) throw/return 0`, or clamp to valid ranges per intended contract.
  - Code snippet:
    ```js
    const start = page * pageSize;
    const end = start + pageSize;
    ```

### Verdict
request changes

</details>

### 03-race-condition
- [03-race-condition.md](03-race-condition.md)

<details><summary>Full AI response for 03-race-condition</summary>

### Summary
The change adds a `RequestStats` class that counts requests per path using a plain `Dictionary<string, int>` with a check-then-act pattern. It is not thread-safe despite clearly being intended for concurrent request tracking, and `Snapshot()` leaks the mutable internal state.

### Findings
- **critical** src/counter.cs:13-21 - Race condition in `Inc` corrupts the dictionary and loses counts
  - Problem: `counts.ContainsKey(path)` followed by `counts[path]++` / `counts[path] = 1` is a non-atomic check-then-act. Concurrent calls can both miss the key and overwrite each other (lost updates), and concurrent writes/reads on a `Dictionary<K,V>` can corrupt internal buckets, throw `NullReferenceException`/`IndexOutOfRangeException`, or hang readers — a real corrupting race for a per-request counter.
  - Fix: Guard all access with a `lock` (or `ReaderWriterLockSlim`), or use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`.
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

- **high** src/counter.cs:27-30 - `Snapshot()` returns the live internal dictionary
  - Problem: Returning `counts` directly exposes mutable internal state: callers can mutate counts, and any caller that enumerates the returned dictionary while `Inc` runs will hit `InvalidOperationException` ("collection was modified") or observe torn data. It also defeats any future locking since readers bypass the lock.
  - Fix: Return a copy under the lock, e.g. `lock (gate) return new Dictionary<string,int>(counts);` (or an `IReadOnlyDictionary` snapshot).
  - Code snippet:
    ```csharp
    public Dictionary<string, int> Snapshot()
    {
        return counts;
    }
    ```

- **medium** src/counter.cs:24-25 - `Count` performs an unsynchronized read
  - Problem: Even if `Inc` were fixed, `Count` reads `counts` without synchronization; concurrent `Dictionary` read+write is undefined and can throw or return garbage. It also does two lookups (`ContainsKey` + indexer) — correct but wasteful.
  - Fix: Read under the same lock and use `TryGetValue`: `lock (gate) { return counts.TryGetValue(path, out var c) ? c : 0; }`
  - Code snippet:
    ```csharp
    return counts.ContainsKey(path) ? counts[path] : 0;
    ```

- **low** src/counter.cs:13 - `Inc` does two dictionary lookups per call
  - Problem: The `ContainsKey` + indexer/setter pattern performs two hash lookups; a single `TryGetValue` (under the lock) is simpler and faster.
  - Fix: `if (counts.TryGetValue(path, out var c)) counts[path] = c + 1; else counts[path] = 1;` — or use `CollectionsMarshal.GetValueRefOrAddDefault` for a single lookup.
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path)) { counts[path]++; }
    ```

### Verdict
request changes

</details>

### 04-missing-error-handling
- [04-missing-error-handling.md](04-missing-error-handling.md)

<details><summary>Full AI response for 04-missing-error-handling</summary>

### Summary
The change adds a `src/config.ts` module with config loading, a file-backup writer, and a remote config fetcher. The code has no error handling, validation, or resource cleanup, so several real defects exist.

### Findings
- **high src/config.ts:20 - `fetchRemoteConfig` never checks the HTTP response status**
  - Problem: `fetch` resolves without throwing for non-2xx responses (404, 500, etc.). The code calls `res.json()` unconditionally, so a server error page or empty body will produce a parse exception or an object that is not an `AppConfig`, propagated to callers as if it were a valid config or an unrelated parse error. Combined with the missing validation, callers can receive a wrong-shaped object on common failure paths.
  - Fix: Check `res.ok` (or `res.status`) before parsing and throw a descriptive error; validate the parsed shape before returning.
  - Code snippet:
    ```
    +  const res = await fetch(url);
    +  return res.json();
    ```

- **medium src/config.ts:15 - file descriptor in `writeBackup` is never closed**
  - Problem: `fs.openSync` returns an `fd` that is written to but never `fs.closeSync`'d. Each call leaks a file descriptor; under repeated calls this exhausts the process fd limit, and on some platforms buffered data may not be fully flushed before process exit.
  - Fix: Use `fs.writeFileSync(path, data)` instead, or wrap `writeSync` in a `try/finally` that calls `fs.closeSync(fd)`.
  - Code snippet:
    ```
    +  const fd = fs.openSync(path, "w");
    +  fs.writeSync(fd, data);
    ```

- **medium src/config.ts:10 - `JSON.parse` result returned unvalidated against `AppConfig`**
  - Problem: `JSON.parse` returns `any`, which is silently cast to `AppConfig`. A config file missing `port`/`dbUrl` or containing the wrong types (e.g. `port` as a string) will be returned as a valid `AppConfig`, deferring failure to downstream consumers where it is harder to diagnose. TypeScript's return type provides no runtime guarantee here.
  - Fix: Validate the parsed object (e.g. check `typeof cfg.port === "number"` and `typeof cfg.dbUrl === "string"`, or use a schema validator like zod) and throw a clear error on mismatch.
  - Code snippet:
    ```
    +  const cfg = JSON.parse(raw);
    +  return cfg;
    ```

- **low src/config.ts:9 - no error context when reading/parsing the config file fails**
  - Problem: If the file is missing or contains invalid JSON, `readFileSync`/`JSON.parse` throw raw errors (`ENOENT`, `SyntaxError`) with no indication that the failure came from loading config at `path`, making operational debugging harder.
  - Fix: Wrap the read/parse in try/catch and rethrow a wrapped error including `path`, e.g. `throw new Error(\`Failed to load config from ${path}: ${err.message}\`)`.
  - Code snippet:
    ```
    +  const raw = fs.readFileSync(path, "utf8");
    +  const cfg = JSON.parse(raw);
    ```

### Verdict
request changes

</details>

### 05-clean-refactor
- [05-clean-refactor.md](05-clean-refactor.md)

<details><summary>Full AI response for 05-clean-refactor</summary>

### Summary
The change refactors `OrderCalculator.OrderTotal` from an explicit accumulation loop to a LINQ `Sum`, and replaces `total + total * taxRate` with `subtotal * (1 + taxRate)`. The refactor is cleaner, but the tax computation reordering can produce different rounding results for `decimal` arithmetic.

### Findings
- **medium** src/totals.cs:12 - Reordered tax calculation can yield different decimal rounding
  - Problem: The original computed `total + (total * taxRate)`; the new code computes `subtotal * (1 + taxRate)`. These are mathematically equivalent but not computally equivalent for `decimal`, which has finite (~28–29 digit) precision and rounds intermediate results. The original rounds `total * taxRate` first and then adds; the new version adds `1 + taxRate` and rounds a single product. For subtotals/rates whose products exceed the precision limit (large totals or rates with many significant digits), the two expressions can differ by a cent, silently changing billing output compared to the prior released behavior.
  - Fix: If bit-for-bit parity with the previous behavior matters, keep the two-step form: `decimal tax = subtotal * taxRate; return subtotal + tax;`. Otherwise, add/verify unit tests covering rounding-sensitive totals and confirm the new rounding is acceptable.
  - Code snippet:
    ```
    +        decimal subtotal = items.Sum(item => item.Price * item.Quantity);
    +        return subtotal * (1 + taxRate);
    ```

- **low** src/totals.cs:11 - `items.Sum` changes the null-argument failure mode slightly
  - Problem: With a null `items` argument, both versions throw, but `Enumerable.Sum` throws `ArgumentNullException` (documented, via `ArgumentNullException.ThrowIfNull`) whereas the old `foreach` threw `NullReferenceException`. Any caller or test asserting `NullReferenceException` would break. This is a minor contract surface change; also note `Sum` on an empty list returns `0m`, matching the old loop, so no issue there.
  - Fix: No code change strictly required; consider an explicit `ArgumentNullException.ThrowIfNull(items)` at the top for clarity, and update any tests that assert the old exception type.
  - Code snippet:
    ```
    +        decimal subtotal = items.Sum(item => item.Price * item.Quantity);
    ```

- **nit** src/totals.cs:1-3 - New `using System;` may be unnecessary
  - Problem: `using System;` was added but nothing in the shown code obviously requires it beyond `ArgumentNullException`/`Console`-type members; `List<>` needs `System.Collections.Generic` and `Sum` needs `System.Linq`. In a file-scoped snippet this is likely harmless, but if the project treats unused usings as warnings it could flag.
  - Fix: Remove `using System;` if it is genuinely unused, or keep it if `Item`/other members in the file require it (context is truncated).
  - Code snippet:
    ```
    +using System;
    ```

### Verdict
approve with nits

</details>

### 06-typos
- [06-typos.md](06-typos.md)

<details><summary>Full AI response for 06-typos</summary>

### Summary
The change adds an `Account` interface and `createAccount`/`getAdress` functions to `src/accounts.ts`. It contains several typos, two of which break runtime behavior: an option override that is silently ignored and a validation check that can never fire.

### Findings
- **high src/accounts.ts:21 - `usernam.lenght` typo disables username length validation**
  - Problem: `String` has no `.lenght` property, so `usernam.lenght` is `undefined` and `undefined < 3` is always `false`. The minimum-length check never throws; in plain JS/compiled output any username (e.g. `""` after trimming) passes validation.
  - Fix: Rename to `usernam.length < 3`.
  - Code snippet: `if (usernam.lenght < 3) {`

- **high src/accounts.ts:18 - `opts.maxRetires` typo means the option is silently ignored**
  - Problem: `DEFAULTS` defines `maxRetries`, but the code reads `opts.maxRetires`. Since `opts` is typed `Partial<typeof DEFAULTS>`, this is a TypeScript error, and at runtime it is always `undefined`, so callers passing `maxRetries` get the default of 3 regardless.
  - Fix: Change to `opts.maxRetries ?? DEFAULTS.maxRetries`.
  - Code snippet: `const retries = opts.maxRetires ?? DEFAULTS.maxRetries;`

- **medium src/accounts.ts:6 - `adress` typo propagates through the public API**
  - Problem: The `Account` interface field `adress` (missing a 'd') is a public API typo repeated at `adress: input.adress` (line 28), in `getAdress` (line 35), and `return account.adress` (line 36). Renaming later is a breaking change for consumers.
  - Fix: Rename the field to `address` and the accessor to `getAddress` everywhere before this ships.
  - Code snippet:
    ```ts
    adress: string;
    ...
    export function getAdress(account: Account): string {
      return account.adress;
    }
    ```

- **low src/accounts.ts:22 - typo in user-facing error message**
  - Problem: `"charcters"` is misspelled in the thrown error message shown to callers.
  - Fix: Change to `"Username must be at least 3 characters long"`.
  - Code snippet: `throw new Error("Username must be at least 3 charcters long");`

- **low src/accounts.ts:39 - typo in exported constant value**
  - Problem: `TEXT` contains `"teh"` instead of `"the"`. If this string is user-facing or used in tests/snapshots, the typo is baked into output. (Flagged with uncertainty since it may be intentional test data.)
  - Fix: If not intentional, change to `"the quick brown fox"`.
  - Code snippet: `export const TEXT = "teh quick brown fox";`

- **nit src/accounts.ts:15 - typo in doc comment**
  - Problem: `"recieve"` should be `"receive"`.
  - Fix: Correct the spelling in the JSDoc.
  - Code snippet: `* We recieve the raw form input and normalize it.`

(Note: `usernam` as a local variable name and `"Colour"` in `LABEL` appear to be stylistic/intentional domain spelling and are not flagged.)

### Verdict
request changes

</details>

---
