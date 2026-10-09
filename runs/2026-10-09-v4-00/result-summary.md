# v4 - 2026-10-09 — Detailed results

- Prompt: `prompts/code-review.v4.md`
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **86.4/100** (-10.3 vs v4; not directly comparable because the previous run scored only three fixtures)
- Hard fails: 03-race-condition — missed_critical, fabricated; 06-typos — fabricated

## What changed
There are no prompt changes versus the previous evaluation: both runs use `prompts/code-review.v4.md` (the v4-to-v4 diff is empty). For context, comparing v4 with the prior prompt version v3 shows that v4 added detailed new-file line reconstruction, a separate rule against speculative future-growth concerns and micro-optimizations, stricter anchors for concurrent access paths, concise grouping guidance for lower-impact cosmetic typos, and exact quoted changed-line requirements.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 01-sql-injection | 3 | 1 | 2 | 3 | 3 | 3 | 3 | 81.7 | -13.3 (prev 95.0) |
| 02-off-by-one | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | 0.0 (prev 95.0) |
| 03-race-condition | 2 | 2 | 2 | 3 | 2 | 3 | 3 | 75.0 | new (previous judge failed) |
| 04-missing-error-handling | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 80.0 | new (previous judge failed) |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | 0.0 (prev 100.0) |
| 06-typos | 3 | 2 | 2 | 3 | 3 | 2 | 3 | 86.7 | new (previous judge failed) |

Overall delta is -10.3 from the prior reported 96.7, but the prior v4 run had successful scores for only three fixtures, so the six-fixture mean here is not directly comparable. Overall score is the mean of the six rounded fixture totals.

Hard-fail flags: 03-race-condition (`missed_critical`, `fabricated`); 06-typos (`fabricated`). No other fixture hard-failed.

## Typo recall
| Category | Found | Total | Recall |
|---|---:|---:|---:|
| misspelling | 1 | 1 | 100% |
| swap | 3 | 3 | 100% |
| missing_letter | 2 | 2 | 100% |

## Observations / next changes

- The model found the prominent defects, but incomplete path coverage caused misses: it omitted the unsynchronized `Count` read in the concurrency fixture and both the HTTP status check and config validation issues in the config fixture.
- The race-condition review and typo review contained incorrect source line anchors; both triggered the rubric's `fabricated` hard fail. The typo fixture found every seeded typo but did not rank the exported API name highest or cosmetic items as nits.
- Precision was also reduced by an unsupported SQL query-buffer concern and a cosmetic get-then-set recommendation in the race fixture. Severity was over-rated for the pagination rounding issue.

Suggested prompt changes:
1. Strengthen the final citation audit: reconstruct every referenced new-file line and require that it points to the quoted changed code; omit any finding whose anchor cannot be verified.
2. Add an explicit coverage pass over each independent function and each shared-state access path (reads, writes, snapshots), and distinguish review of HTTP response status from response-body parsing and config shape validation.
3. Suppress secondary buffer/performance suggestions unless the diff demonstrates an actual impact or requirement; keep the response focused on verified defects.
4. Clarify severity ranking with examples that distinguish a concrete API compatibility concern from cosmetic typos and a pagination completeness defect from a high-severity page-offset defect.

## Per-fixture results

### 01-sql-injection
[Run file](01-sql-injection.md)

<details><summary>Full AI response</summary>

## Summary
The new stored procedure builds SQL by string concatenation, introducing a direct SQL injection vulnerability.

## Findings

[Critical] src/users.sql:10 — SQL injection via concatenated parameter
```
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
```
`@name` is interpolated directly into a dynamic SQL string executed by `sp_executesql` (line 11). A caller passing a value like `x'; DROP TABLE users; --` (or extracting data via `UNION SELECT`) can execute arbitrary SQL. Impact: arbitrary query execution — data exfiltration, modification, or destruction depending on the login's permissions.

Fix: eliminate dynamic SQL entirely; it is unnecessary here since the query is static:
```sql
CREATE OR ALTER PROCEDURE FindUserByName
    @name nvarchar(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id, name, email FROM users WHERE name = @name;
END
```
If dynamic SQL were truly needed, parameterize it: `EXEC sp_executesql N'SELECT id, name, email FROM users WHERE name = @p', N'@p nvarchar(255)', @p = @name;`

[Low] src/users.sql:9 — `nvarchar(1023)` under-length buffer for the dynamic query
```
DECLARE @query nvarchar(1023);
```
`@name` alone can be up to 255 characters; combined with the ~70-char literal it fits today, but the odd length is arbitrary and truncation would silently alter the executed SQL. This is moot if the fix above removes the dynamic SQL; otherwise use `nvarchar(max)` or size it with slack.

## Verdict
Request changes
</details>

### 02-off-by-one
[Run file](02-off-by-one.md)

<details><summary>Full AI response</summary>

## Summary
New pagination helpers contain off-by-one and rounding errors that break their documented 1-based contract.

## Findings

[High] src/pagination.js:7 — `getPage` uses `page * pageSize`, skipping the first page's items

```js
const start = page * pageSize;
```

The docstring says `page` is 1-based, but `getPage(items, 1, 10)` returns items 10–19 instead of 0–9, and item index 0 is unreachable. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `totalPages` undercounts partial last pages

```js
return Math.floor(items.length / pageSize);
```

With 25 items and pageSize 10 it returns 2 instead of 3, dropping the last 5 items from any page count. Fix: `return Math.ceil(items.length / pageSize);`

## Verdict
Request changes
</details>

### 03-race-condition
[Run file](03-race-condition.md)

<details><summary>Full AI response</summary>

## Summary
`RequestStats` uses a non-thread-safe `Dictionary` that `RequestHandler.HandleAllAsync` mutates from multiple concurrent `Task.Run` calls, and `Snapshot()` leaks the mutable internal dictionary — together these create real correctness and race-condition defects.

## Findings

**[High] src/counter.cs:30 — Concurrent `Dictionary` mutation is not thread-safe**

```csharp
await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));
```

`HandleAllAsync` fans out `stats.Inc(p)` across thread-pool threads that run concurrently. `Dictionary<string,int>` is not thread-safe for concurrent writes; the read-modify-write in `Inc` (`src/counter.cs:11-13`) can lose increments and, under concurrent structural modification, can corrupt internal state or throw. Fix: use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or serialize access with a lock.

**[Medium] src/counter.cs:22 — `Snapshot()` returns the live internal dictionary**

```csharp
return counts;
```

Callers receive a mutable reference to the internal state: they can read it while `Inc` concurrently mutates it (risk of `InvalidOperationException` during enumeration, torn reads) and can write to it, bypassing the class's encapsulation. Fix: return a copy, e.g., `return new Dictionary<string,int>(counts);` (with the concurrency issue above fixed, `new Dictionary<string,int>(counts)` on a `ConcurrentDictionary` is a safe snapshot).

**[Low] src/counter.cs:10 — Unnecessary manual get-then-set in `Inc`**

```csharp
if (counts.TryGetValue(path, out var count))
```

`counts[path] = counts.GetValueOrDefault(path) + 1` (or `CollectionsMarshal.GetValueRefOrAddDefault`) expresses the same logic in one lookup; strictly cosmetic/perf nit, but worth folding into the thread-safety fix.

## Verdict
Request changes
</details>

### 04-missing-error-handling
[Run file](04-missing-error-handling.md)

<details><summary>Full AI response</summary>

## Summary
Adds config loading, backup writing, and remote config fetching helpers; the backup writer leaks its file descriptor, which is a concrete reliability defect.

## Findings

**[Medium] src/config.ts:15 — file descriptor never closed in `writeBackup`**

```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```

`fs.openSync` returns a descriptor that must be released with `fs.closeSync(fd)`. As written, every call to `writeBackup` leaks a descriptor; repeated calls can exhaust the process's file-descriptor limit, and on an exception from `writeSync` the descriptor is leaked unconditionally. Fix: either use `fs.writeFileSync(path, data)` (the simple fix), or wrap in `try/finally` with `fs.closeSync(fd)`.

**[Low] src/config.ts:16 — `writeSync` result ignored**

```ts
fs.writeSync(fd, data)
```

`fs.writeSync` returns the number of bytes actually written and is not guaranteed to write the entire buffer in one call. If a partial write occurs, the backup is silently truncated. Fix: if keeping the raw-sync approach, loop until all bytes are written; simplest is switching to `fs.writeFileSync`, which also resolves the leak above.

## Verdict
Request changes
</details>

### 05-clean-refactor
[Run file](05-clean-refactor.md)

<details><summary>Full AI response</summary>

## Summary
Low-risk refactor replacing a manual accumulation loop with LINQ `Sum` and an algebraically equivalent tax expression; no behavioral difference for the demonstrated code path.

## Findings
None.

The change is behaviorally equivalent:

- `items.Sum(item => item.Price * item.Quantity)` (src/totals.cs:8) accumulates the same per-item `Price * Quantity` values in order into a `decimal`, identical to the removed `total = total + item.Price * item.Quantity` loop — including the same overflow semantics (`Sum` on `decimal` throws `OverflowException`, as would the `checked`-equivalent accumulation in the original context).
- `subtotal * (1 + taxRate)` (src/totals.cs:9) computes the same `subtotal + subtotal * taxRate`; per Review Guidelines, speculative decimal non-associativity concerns are not raised absent a demonstrated rounding requirement.
- `null` handling is unchanged in effect: the original `foreach` would throw `NullReferenceException` on a null `items`; `Sum` throws `ArgumentNullException`. This is a different exception type, but no contract for null input is established in the diff, so it is not a defect.

## Verdict
Approve
</details>

### 06-typos
[Run file](06-typos.md)

<details><summary>Full AI response</summary>

## Summary
New account service code with several typos, including a misspelled exported function name and a garbled user-facing error message; no functional defects demonstrated.

## Findings
[Low] src/accounts.ts:40 — misspelled exported identifier
```
export function getAdress(account: Account): string {
```
"getAdress" is a misspelling of "getAddress" in a public API name; callers will bind to the typo, making later correction a breaking change. Rename to `getAddress` now (or export both).

[Low] src/accounts.ts:24 — multiple typos in user-facing error message
```
    throw new Error("Username lenght must be at least 3 charaters.")
```
"lenght" → "length", "charaters" → "characters". This text is surfaced to users on validation failure. Fix the string literal.

[Low] src/accounts.ts:42 — typo in exported string constant
```
export const TEXT = "teh quick brown fox"
```
"teh" → "the". If this is display/test fixture text, correct the literal.

[Low] src/accounts.ts:18, 14, 33 — cosmetic typos in comment and local identifiers
```
 * We recieve the raw form input and normalize it.
  const retires = opts.maxRetries ?? DEFAULTS.maxRetries
  console.log(`Created account for ${account.username}, retrying up to ${retires} times`)
```
"recieve" → "receive" (comment), "retires" → "retries" (local variable, also interpolated into the log line, which reads confusingly). Rename the local and fix the comment.

## Verdict
Approve with nits
</details>

---
