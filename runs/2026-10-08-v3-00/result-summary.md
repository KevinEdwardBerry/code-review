# v3 - 2026-10-08 — Detailed results

- Prompt: `prompts/code-review.v3.md`
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed; one fixture remained unscored after retry)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **90.3/100** (+2.8 vs v2-01; mean of five successfully judged fixtures, so not directly comparable to the prior six-fixture score)
- Hard fails: 02-off-by-one — `fabricated` (wrong cited line numbers); 06-typos — judge failed, hard-fail status unscored

## What changed

Compared with the previously evaluated prompt v2, v3 now requires new-file line numbering and verifies that cited lines and excerpts match; expands anti-speculation guidance to contract assumptions, latent capacity risks, and decimal non-associativity; directs reviewers to inspect shared-state mutations, reads, snapshots, and demonstrated concurrent call sites separately; tightens evidence and style-nit requirements; and adds explicit ranking of cosmetic typo findings below API and user-facing defects.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 01-sql-injection | 3 | 1 | 3 | 2 | 2 | 3 | 3 | 78.3 | -21.7 |
| 02-off-by-one | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 | +11.7 — FAIL |
| 03-race-condition | 3 | 2 | 3 | 2 | 3 | 3 | 3 | 88.3 | +10.0 |
| 04-missing-error-handling | 3 | 3 | 2 | 2 | 3 | 3 | 3 | 90.0 | -1.7 |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +11.7 |
| 06-typos | — | — | — | — | — | — | — | Judge failed | N/A |

Overall delta: +2.8 points against v2-01's 87.5/100, calculated from the five successfully judged fixture totals. The prior score covers all six fixtures; interpret this delta cautiously. Totals are weighted by rubric criterion weights and rounded to one decimal before averaging. The 06-typos judge returned unusable assessments both initially and on the single retry because its inputs omitted the complete expected findings and reviewer response; it is recorded as judge failed, not assigned zero.

## Typo recall

| Category | Found / total |
|---|---:|
| misspelling | 1/1 (reviewer text only; not judge-scored) |
| swap | 3/3 (reviewer text only; not judge-scored) |
| missing_letter | 2/2 (reviewer text only; not judge-scored) |

The 06-typos reviewer response mentioned each expected typo category item, but the AI judge failed; the category counts above are a manual count of the reviewer text, not a scored result. Its finding references also appear misaligned with the supplied new-file lines, so no formal fixture score or hard-fail determination is available.

## Observations / next changes

- All five judgeable reviews found their seeded issues; the clean refactor received a perfect score. The largest judged regression was SQL injection (-21.7), mainly from an unsupported optional concern about hypothetical future query growth and reduced precision. The config review also fell slightly (-1.7), while off-by-one, concurrency, and clean-refactor scores improved.
- Exact reference validation remains the clearest gap: 02-off-by-one matched both defects but cited lines that did not correspond to the quoted code, triggering a `fabricated` hard fail. Config and concurrency also had imprecise line references that lowered actionability. The v3 instructions request verification, but reviewers did not reliably perform it.
- Precision still suffers from speculative optimization/capacity nits: the SQL query-length comment assumes future changes, while the concurrency review reports a redundant lookup optimization not needed to identify a defect.
- The typo reviewer mentioned all expected categories, but the judge could not evaluate them. Its citations similarly look offset from new-file lines; treat typo recall and hard-fail status as unscored pending a valid judge run.
- Suggested next prompt changes:
  1. Require reviewers to number the new file from the hunk's `+start` line and verify each cited line against the exact quoted expression, not merely a nearby function or hunk position; omit any finding with an unverified anchor.
  2. Explicitly prohibit hypothetical future-growth and micro-optimization findings unless the current diff demonstrates a concrete impact or established contract.
  3. For shared-state findings, cite the mutation/read/snapshot operations directly and keep separate defects anchored to their own source lines.
  4. Keep typo findings concise and prioritize the exported API and user-facing string defects over cosmetic items without allowing citation accuracy to slip.

## Per-fixture results

### [01-sql-injection](01-sql-injection.md) — 78.3/100 (-21.7)
<details><summary>Full AI response</summary>

## Summary
This change adds a stored procedure that builds a dynamic SQL query by concatenating an unvalidated user parameter, creating a direct SQL injection vulnerability.

## Findings

[Critical] src/users.sql:9-10 — SQL injection via string concatenation in dynamic SQL

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

`@name` is interpolated directly into the query string. An attacker passing `'; DROP TABLE users; --` (or similar) can inject arbitrary SQL, leading to data exfiltration or destructive commands. There is also no escaping or quoting of the input.

Fix: parameterize the dynamic statement instead of concatenating:

```sql
SET @query = N'SELECT id, name, email FROM users WHERE name = @name';
EXEC sp_executesql @query, N'@name nvarchar(255)', @name;
```

Alternatively, if no dynamic SQL is actually needed, run the static `SELECT` directly in the procedure.

[Low] src/users.sql:8 — `nvarchar(1023)` may truncate long `@name` values combined with the query prefix

```sql
DECLARE @query nvarchar(1023);
```

The query literal is ~70 characters; a full-length 255-char `@name` fits, so this is fine as written, but the odd 1023 length is unusual — `nvarchar(max)` or a larger fixed size would be more robust if the query grows. Low severity; optional fix once the injection above is resolved (a parameterized statement makes size requirements clearer).

## Verdict
Request changes

</details>

### [02-off-by-one](02-off-by-one.md) — 95.0/100 (+11.7 — FAIL: fabricated)
<details><summary>Full AI response</summary>

## Summary
Low-risk pagination helper addition, but both functions compute incorrect results relative to the documented 1-based contract.

## Findings

[High] src/pagination.js:5 — `getPage` ignores the documented 1-based page numbering
```js
const start = page * pageSize;
```
The docstring states page numbers are 1-based, but `start = page * pageSize` skips the first `pageSize` items for `page = 1` (e.g., `pageSize=10`, `page=1` returns items 10–19 instead of 0–9). Every caller gets the wrong slice. Fix: `const start = (page - 1) * pageSize;`.

[Medium] src/pagination.js:13 — `totalPages` drops the last partial page
```js
return Math.floor(items.length / pageSize);
```
With 25 items and `pageSize=10`, this returns 2, so items 20–24 are unreachable via `getPage`. Fix: `return Math.ceil(items.length / pageSize);`

## Verdict
Request changes

</details>

### [03-race-condition](03-race-condition.md) — 88.3/100 (+10.0)
<details><summary>Full AI response</summary>

## Summary
New request-stats code is demonstrably raced: `Inc` mutates a non-thread-safe `Dictionary` from concurrent `Task.Run` calls, and `Snapshot` leaks the mutable internal state.

## Findings

**[High] src/counter.cs:33 — unsynchronized concurrent writes to `Dictionary` corrupt state and lose counts**

```csharp
await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));
```

`HandleAllAsync` explicitly invokes `stats.Inc(p)` on multiple thread-pool threads concurrently, while `Inc` (lines 12–16) performs a non-atomic `ContainsKey`/index-set sequence on a plain `Dictionary<string,int>`. Concurrent `Inc` calls can overwrite each other's increments (two threads both seeing `ContainsKey == false`, then both setting `counts[path] = 1`) and, worse, concurrent mutation of `Dictionary` is documented to produce undefined behavior (corrupted internal buckets, exceptions, hangs). Reads via `Count`/`Snapshot` racing with writes are likewise unsafe.

Fix: guard all accesses with a `lock`, use `Interlocked`-safe primitives, or replace `counts` with `ConcurrentDictionary<string,int>` and `AddOrUpdate(path, 1, (_, c) => c + 1)`, and make `Count` use `TryGetValue`.

**[Medium] src/counter.cs:23 — `Snapshot` returns the live mutable dictionary**

```csharp
public Dictionary<string, int> Snapshot()
{
    return counts;
}
```

Callers of `Snapshot` receive the internal `counts` reference, so any external mutation corrupts the stats and any enumeration races with concurrent `Inc` writes (throwing `InvalidOperationException`). Fix: return a copy under the same lock used for mutation, e.g. `return new Dictionary<string,int>(counts);` inside the lock (or materialize a copy from a `ConcurrentDictionary`).

**[Low] src/counter.cs:19 — redundant double dictionary lookup in `Count`**

```csharp
return counts.ContainsKey(path) ? counts[path] : 0;
```

Two lookups where `TryGetValue` suffices (`counts.TryGetValue(path, out var c) ? c : 0`). Minor, but halves lookups and avoids an extra bounds check per call.

## Verdict
Request changes — the demonstrated concurrent `Inc` calls make the shared `Dictionary` unsafe; this needs a lock or `ConcurrentDictionary` before merging.

</details>

### [04-missing-error-handling](04-missing-error-handling.md) — 90.0/100 (-1.7)
<details><summary>Full AI response</summary>

## Summary
Low-to-moderate risk change adding config helpers to `src/config.ts`; the main defect is an unclosed file descriptor in `writeBackup`.

## Findings

- **[Medium] src/config.ts:14 — File descriptor never closed in `writeBackup`**
  ```ts
  const fd = fs.openSync(path, "w")
  fs.writeSync(fd, data)
  ```
  `fd` is opened but never `fs.closeSync`'d. Each call leaks a file descriptor; on repeated writes (e.g., periodic backups) the process will exhaust its fd limit and start failing with `EMFILE`. Additionally, if `writeSync` throws, the fd leaks immediately. Fix: wrap in try/finally and call `fs.closeSync(fd)`, or simply use `fs.writeFileSync(path, data)` which handles open/write/close atomically.

- **[Low] src/config.ts:21 — `fetchRemoteConfig` ignores HTTP status**
  ```ts
  const res = await fetch(url)
  return res.json()
  ```
  A non-2xx response (e.g., a 404 HTML error page) is passed straight to `res.json()`, producing a confusing parse error rather than a clear failure. Fix: check `res.ok` and throw an error including `res.status` before parsing. (Also, the return value is unvalidated `any` cast to `AppConfig`, same as `loadConfig` — flagging once here as low severity since no validation contract is established in the diff.)

## Verdict
Approve with nits — the fd leak should ideally be fixed before merge, but the change is small and the impact is limited to repeated-write scenarios.

</details>

### [05-clean-refactor](05-clean-refactor.md) — 100.0/100 (+11.7)
<details><summary>Full AI response</summary>

## Summary
Low-risk behavior-equivalent refactor replacing a manual accumulation loop with LINQ `Sum` and a single multiplication for tax.

## Findings
None.

The rewritten method computes `items.Sum(item => item.Price * item.Quantity)` and returns `subtotal * (1 + taxRate)`, which is arithmetically equivalent to the previous `total + total * taxRate` for `decimal` operands at this scale. Per the review guidelines, speculative decimal non-associativity differences are not reportable without a demonstrated contract or defect.

## Verdict
Approve

</details>

### [06-typos](06-typos.md) — Judge failed (score and delta unavailable)
<details><summary>Full AI response</summary>

## Summary
Low-risk addition of an account-creation helper; the change is functionally sound but contains several typos, including a misspelled exported function name and a user-facing error message.

## Findings

[Medium] src/accounts.ts:41 — Exported function name `getAdress` is misspelled
```
export function getAdress(account: Account): string {
```
This is a public API name; the misspelling will propagate to all callers and fixing it later is a breaking change. Rename to `getAddress` before this ships.

[Low] src/accounts.ts:23 — User-facing error message contains two misspellings
```
throw new Error("Username lenght must be at least 3 charaters.")
```
Should read "Username length must be at least 3 characters."

[Low] src/accounts.ts:44 — Exported string literal `TEXT` contains a typo
```
export const TEXT = "teh quick brown fox"
```
"teh" should be "the" unless the misspelling is intentional (e.g., test fixture).

[Low] src/accounts.ts:16 — Local variable `retires` is misspelled
```
const retires = opts.maxRetries ?? DEFAULTS.maxRetries
```
Should be `retries`. Cosmetic, but it also appears in the log message at line 31.

[Low] src/accounts.ts:13 — Comment typo "recieve"
```
 * We recieve the raw form input and normalize it.
```
Should be "receive". (`LABEL`'s "Colour" is a valid spelling variant — not a defect.)

## Verdict
Approve with nits. The `getAdress` export name is the most consequential item — worth fixing before release since renaming later breaks callers, but none of the typos affect runtime correctness.

</details>

---
