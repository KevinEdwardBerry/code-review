# v4 - 2026-10-08 — Detailed results

- Prompt: `prompts/code-review.v4.md`
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed; judge failed after retry for 03, 04, and 06)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **96.7/100** (+6.4 vs v3; mean of three successfully judged fixtures, not directly comparable to v3's five judged fixtures)
- Hard fails: none confirmed among scored fixtures; 03-race-condition, 04-missing-error-handling, and 06-typos are unscored (judge failed)

## What changed

Compared with the previously evaluated prompt v3, v4 adds a step-by-step new-file line-number reconstruction rule, explicitly discourages hypothetical future-growth and micro-optimization nits, strengthens concurrent read/write/snapshot issue anchoring, expands typo guidance to group lower-impact cosmetic issues, and requires exact quoted lines and separate citations for multi-location findings.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 01-sql-injection | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 | +16.7 |
| 02-off-by-one | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | 0.0 |
| 03-race-condition | — | — | — | — | — | — | — | Judge failed | N/A |
| 04-missing-error-handling | — | — | — | — | — | — | — | Judge failed | N/A |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | 0.0 |
| 06-typos | — | — | — | — | — | — | — | Judge failed | N/A |

Overall delta is +6.4 against v3's 90.3/100, but this run scored only three fixtures versus five in v3. The score is a mean of fixture totals rounded to one decimal. All three schema-valid judgments returned no hard-fail flags. Failed judgments are not assigned scores or hard-fail status.

## Typo recall

| Category | Reviewer text mentions / total | Judge status |
|---|---:|---|
| misspelling | 1/1 | Unscored |
| swap | 3/3 | Unscored |
| missing_letter | 2/2 | Unscored |

The reviewer text mentions all six expected typo items, but 06-typos is unscored because both judge outputs failed schema validation; its citations are also offset from the actual new-file lines.

## Observations / next changes

- The three successfully judged fixtures averaged 96.7. The clean refactor was correctly approved with no findings; SQL injection and pagination issues were both identified. Compared with v3, 01-sql-injection improved by 16.7, while 02-off-by-one and 05-clean-refactor were unchanged.
- Exact line anchoring remains a weakness despite v4's added instructions. The SQL finding points to line 9 instead of the concatenation at line 10. The pagination return finding points to line 16 rather than the `Math.floor` return at line 15; the judge did not catch this error. The unscored config and typo reviews also cite lines that do not identify the quoted code.
- The concurrency review identifies the concurrent mutation and leaked snapshot, but does not separately report the unsynchronized `Count` read. The initial judge noted this omission; the fixture remains unscored because both judge responses failed schema validation.
- Three of six fixture judgments failed schema validation, so this result has limited coverage. The typo reviewer text mentions all categories, but the citations are inaccurate and typo scoring could not be verified. The reviewer also raises an unsupported concern that the docstring promises a welcome email that is not implemented.
- Suggested next changes:
  1. Keep every finding's quote and line reference in a single directly verifiable unit; require omission unless the quoted defect itself maps to the cited new-file line, and check every finding independently.
  2. In concurrent code, report each demonstrated unsafe access path separately (mutation, read, and snapshot), anchoring each to its own operation and the concrete concurrent caller.
  3. Require typo/API observations to retain correct new-file locations and impact-based ordering; avoid adding unrelated documentation-contract concerns unless the diff establishes their effect.
  4. Tighten judge task construction and schema validation in the evaluation workflow so each judge receives the complete expected list and review, and judge failures do not erase fixture coverage.

## Per-fixture results

### [01-sql-injection](01-sql-injection.md) — 95.0/100 (+16.7)
<details><summary>Full AI response</summary>

## Summary
The new stored procedure builds dynamic SQL by concatenating a user-supplied name directly into the query string, creating a direct SQL injection vulnerability.

## Findings

[Critical] src/users.sql:9 — SQL injection via string concatenation into `sp_executesql`

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

The `@name` parameter is concatenated verbatim into the executed SQL text. Any caller-supplied value containing a single quote (e.g., `' OR 1=1; --`) escapes the string literal and executes as SQL, allowing unauthorized data access or modification (depending on the executing principal's permissions). There is no escaping of `@name` and no use of `sp_executesql`'s parameter-binding capability.

Fix: use a parameterized query instead of concatenation:

```sql
EXEC sp_executesql
    N'SELECT id, name, email FROM users WHERE name = @name',
    N'@name nvarchar(255)',
    @name = @name;
```

Alternatively, remove the dynamic SQL entirely and run the `SELECT` as a plain statement in the procedure body, since nothing here requires dynamic SQL.

## Verdict
Request changes

</details>

### [02-off-by-one](02-off-by-one.md) — 95.0/100 (0.0)
<details><summary>Full AI response</summary>

## Summary
New pagination helpers contain two correctness bugs: an off-by-one page indexing mismatch and page-count truncation.

## Findings

[Medium] src/pagination.js:7 — Off-by-one between documented 1-based contract and 0-based implementation
```js
const start = page * pageSize;
```
The docstring at line 4 states "Returns the items for a 1-based page number", but `page * pageSize` treats `page` as 0-based: `getPage(items, 1, 10)` skips the first 10 items instead of returning items 0–9. Either fix the implementation to `const start = (page - 1) * pageSize;` or correct the documentation if 0-based was intended.

[Medium] src/pagination.js:16 — `totalPages` truncates partial pages
```js
return Math.floor(items.length / pageSize);
```
`Math.floor` drops the final partial page: 25 items with `pageSize` 10 yields 2 pages, losing access to the last 5 items. Use `Math.ceil(items.length / pageSize)` so every item is reachable.

## Verdict
Request changes

</details>

### [03-race-condition](03-race-condition.md) — Judge failed (delta unavailable)
<details><summary>Full AI response</summary>

## Summary
The new `RequestStats` counter is not thread-safe but is driven concurrently by `HandleAllAsync`, making the code racy by construction.

## Findings

[High] src/counter.cs:34 — concurrent unsynchronized mutation of `Dictionary<string,int>`
```csharp
await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));
```
`HandleAllAsync` explicitly fans out `stats.Inc(p)` calls across the thread pool, while `Inc` (lines 11–15, `counts[path]++;`) performs a read-modify-write on a plain `Dictionary`, which is not thread-safe. Impact: lost increments (inaccurate counts) and potential internal dictionary corruption/exceptions under concurrent writes. Fix: use a `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)` (or `Interlocked`/`lock` on the existing dictionary).

[Medium] src/counter.cs:26 — `Snapshot()` returns the live internal dictionary
```csharp
        return counts;
```
Callers receive the mutable backing store rather than a snapshot: they can mutate counts or observe it mid-mutation while `HandleAllAsync` is running. Fix: return `new Dictionary<string,int>(counts)` under the same lock used for mutation (or materialize a copy from a `ConcurrentDictionary`).

## Verdict
Request changes

</details>

### [04-missing-error-handling](04-missing-error-handling.md) — Judge failed (delta unavailable)
<details><summary>Full AI response</summary>

## Summary
Adds config loading helpers with a file-descriptor leak in `writeBackup` and missing error/response handling in `fetchRemoteConfig`; overall moderate risk.

## Findings

- **[Medium] src/config.ts:15 — `openSync` file descriptor is never closed**
  ```ts
  const fd = fs.openSync(path, "w")
  fs.writeSync(fd, data)
  ```
  `writeBackup` opens `fd` but never calls `fs.closeSync(fd)`. Each call leaks a descriptor; repeated calls (or a `writeSync` throw) accumulate leaked handles and can exhaust the process fd limit. Fix: wrap in try/finally with `fs.closeSync(fd)`, or use `fs.writeFileSync(path, data)`.

- **[Medium] src/config.ts:21 — HTTP error responses are silently parsed as config**
  ```ts
  const res = await fetch(url)
  return res.json()
  ```
  `fetch` resolves on non-2xx responses, so a 404/500 HTML or error body is passed to `res.json()` — producing either an opaque `SyntaxError` or an `AppConfig`-typed object that isn't a valid config. Fix: check `res.ok` and throw a descriptive error (including `res.status`) before parsing.

- **[Low] src/config.ts:7 — parsed JSON returned without validation against `AppConfig`**
  ```ts
  const cfg = JSON.parse(raw)
  return cfg
  ```
  Any well-formed JSON (e.g. a string, array, or missing `port`/`dbUrl`) is returned typed as `AppConfig`, pushing malformed-config failures to distant consumers. Fix: validate `cfg.port`/`cfg.dbUrl` types (or use a schema) and throw on mismatch. (Same applies to `fetchRemoteConfig`, which shares the unchecked-cast pattern.)

## Verdict
Request changes

</details>

### [05-clean-refactor](05-clean-refactor.md) — 100.0/100 (0.0)
<details><summary>Full AI response</summary>

## Summary
Low-risk refactor of `OrderTotal` from a manual accumulation loop to `Enumerable.Sum` with an algebraically equivalent tax computation.

## Findings
None.

## Verdict
Approve

</details>

### [06-typos](06-typos.md) — Judge failed (delta unavailable)
<details><summary>Full AI response</summary>

## Summary
Low-risk additive change introducing an account module; the only concrete issues are spelling errors in an exported identifier, a user-facing error message, and public string/comment text.

## Findings
- [Low] src/accounts.ts:36 — Typo in exported function name: `export function getAdress(account: Account): string {`. "Adress" should be "Address"; this misspelling becomes part of the public API and is hard to fix later without breaking callers. Rename to `getAddress` before merge.
- [Low] src/accounts.ts:23 — Typos in user-facing error message: `throw new Error("Username lenght must be at least 3 charaters.")`. "lenght" → "length", "charaters" → "characters".
- [Low] src/accounts.ts:40 — Typo in public string literal: `export const TEXT = "teh quick brown fox"`. "teh" → "the".
- [Low] src/accounts.ts:19 — Misspelled local identifier: `const retires = opts.maxRetries ?? DEFAULTS.maxRetries` (also used at line 32 in the `console.log`). "retires" → "retries"; the log message will read "retrying up to N times" correctly but the variable name is misleading.
- [Low] src/accounts.ts:16 — Comment typo: ` * We recieve the raw form input and normalize it.` "recieve" → "receive". Also, the docstring claims the function "sends a welcome email," but no email is sent — either implement it or correct the doc.

## Verdict
Approve with nits

</details>

---
