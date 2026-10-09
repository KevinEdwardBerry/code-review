# v1 - 2026-10-09 (rerun) — Detailed results

- Prompt: `prompts/code-review.v1.md`
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed (the judge could not be set to a different model; same-model judging is possible))
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **75.3/100** (-18.6 vs v4 run 2026-10-09-v4-01 (93.9); +4.7 vs prior v1 run 70.6 (fixture 01 differs))
- Hard fails: None

## What changed
Run against `v4` for context: v1 is the bare prompt ("You are a senior software engineer performing a code review of the change below." + diff). v4 adds ~40 lines: concise/no-assumption instruction, `file:line` references, severity level definitions, review principles (exact new-file line reconstruction, no speculation, concurrency paths, behavior-equivalent refactors), typo ranking rules, and a required Summary/Findings/Verdict format.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-csharp-sql-injection | 3 | 1 | 3 | 2 | 3 | 2 | 2 | 78.3 | -21.7 (v4-01 100.0); +6.6 (v1-00 71.7) |
| 02-off-by-one | 3 | 2 | 2 | 3 | 3 | 1 | 2 | 83.3 | -6.7 (v4-01 90.0); +6.6 (v1-00 76.7) |
| 03-race-condition | 2 | 1 | 2 | 2 | 2 | 2 | 2 | 60.0 | -30.0 (v4-01 90.0); -13.3 (v1-00 73.3) |
| 04-missing-error-handling | 3 | 2 | 2 | 2 | 2 | 2 | 2 | 76.7 | -13.3 (v4-01 90.0); +10.0 (v1-00 66.7) |
| 05-clean-refactor | 3 | 3 | 3 | 2 | 3 | 2 | 2 | 91.7 | -6.6 (v4-01 98.3); +20.0 (v1-00 71.7) |
| 06-typos | 3 | 1 | 1 | 2 | 2 | 1 | 1 | 61.7 | -33.3 (v4-01 95.0); -1.6 (v1-00 63.3) |

## Typo recall
| Category | Found | Total | Recall |
|---|---:|---:|---:|
| misspelling | 1 | 1 | 100% |
| swap | 3 | 3 | 100% |
| missing_letter | 2 | 2 | 100% |

## Observations / next changes
- **Format drift is the main structural miss.** No review followed Summary / Findings / Verdict (format scores 1-2 everywhere; 02 and 06 scored 1). Reviews are ordered inconsistently and the typos review mixes cosmetic typos with speculative bugs.
- **Precision is the largest loss (avg 1.7/3).** Recurrent false positives: speculative extras (ConfigureAwait, SingleRow, uniqueness, email validation on 01; unused `timeoutMs`, shorthand property, semicolons, trivial getter on 06), self-negating bullets ("actually, the current form is fine"), and must-not-flag items (async disposal on 01, `Task.Run` on 03, "Colour" on 06).
- **Recall is strong (6/6 on 01, 02, 04, 06) but 03 only mentions the unsynchronized `Count` read in passing** (`unlocked_read` missed; not a hard fail since `snapshot_leak` was found).
- **Severity:** the pagination `totalPages` bug and config findings are labelled Critical/must-fix (expected medium); on 06 `retires` (cosmetic) is listed before `getAdress` (public API), violating ranking.
- **Citations:** the mechanical check passed on all six (only 01 cites a line, `:15`; the vulnerable line is 14, which the checker did not flag but the judge penalised actionability). Most findings carry no `file:line` at all.
- **Per-typo-category recall:** misspelling 1/1, swap 3/3, missing_letter 2/2 (100%).
- **Comparability:** deltas vs v4-01 use the same six fixtures, all judged. Note v4-01 was judged before the mechanical citation check was added to the judge prompt, and both runs are single samples; v4 had four fabricated hard fails while v1 has none, so the v1 score is lower mostly on precision/format, not on citation hard fails. Versus the prior v1 run (70.6, mean of prior v1 runs) fixture 01 differs (earlier `01-sql-injection`), so that comparison is indicative only: +4.7.
- Judge quirk: the 03 judge rationale cites diff line numbers (80-96) that do not exist (the file is 39 lines); this did not affect scoring. No human override applied.

Suggested prompt changes:
1. Add the required `## Summary` / `## Findings` / `## Verdict` format with severity ordering (largest format and tone gain).
2. Add a "do not report speculative/best-practice suggestions; do not argue with yourself" rule to cut precision losses.
3. Require a separate finding for each unsynchronized access path when concurrent use is shown (fixes the 03 `Count` miss).
4. Add typo ranking/grouping and a "do not flag proper names or variant spellings (e.g. Colour in a brand name)" rule, plus severity definitions so cosmetic items are not ranked above API typos.

## Per-fixture results
### 01-csharp-sql-injection — 78.3
[Run file](01-csharp-sql-injection.md)

<details><summary>Full AI response</summary>

# Code Review: CustomerRepository

## Critical

**1. SQL Injection (blocking)** — `src/CustomerRepository.cs:15`

```csharp
var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";
```

`email` is interpolated directly into the SQL string. An attacker can supply a crafted email such as `' OR '1'='1` to bypass filters, or worse, run stacked queries depending on driver settings. This must be parameterized:

```csharp
const string sql = "SELECT Id, Email FROM Customers WHERE Email = @Email";
await using var command = new SqlCommand(sql, connection);
command.Parameters.Add("@Email", SqlDbType.NVarChar, 256).Value = email;
```

Note: specifying `SqlDbType` and length avoids parameter-size mismatches that can hurt plan cache reuse for `NVarChar` columns.

## Suggestions

**2. Implicit `IDisposable` behavior with `await using`** — lines 11, 16, 17

This is correct (`SqlConnection`, `SqlCommand`, `SqlDataReader` all support async dispose), so no change needed — but worth confirming the project targets a framework where `IAsyncDisposable` is implemented on these types (netstandard2.1+/net5+). If the package version is old, `await using` won't compile.

**3. `ExecuteReaderAsync` without `CommandBehavior.SingleRow`** — line 17

Since the method returns at most one `Customer`, passing `CommandBehavior.SingleRow | CommandBehavior.SingleResult` lets the provider optimize and documents intent. Optional, but cheap.

**4. Uniqueness assumption on `Email`** — line 15

`FindByEmailAsync` silently returns the *first* matching row. If `Email` isn't backed by a unique constraint in the database, duplicates produce nondeterministic results. Recommend adding `WHERE ... AND ...` semantics clarification or at minimum documenting/enforcing uniqueness at the schema level.

**5. Missing email validation** — line 8

Not strictly required since parameterization makes it safe, but a cheap guard (`string.IsNullOrWhiteSpace` → `ArgumentException`) avoids useless DB round-trips and clearer error semantics.

**6. Minor: no `ConfigureAwait(false)` / library conventions**

If this is shared library code, consider whether the codebase convention calls for `ConfigureAwait(false)`. Skipped in many modern ASP.NET Core codebases; check project norms.

## Verdict

**Request changes.** The SQL injection vulnerability is a hard blocker — everything else is secondary polish. The structure (sealed types, async throughout, proper disposal, nullable return) is otherwise solid.

</details>

### 02-off-by-one — 83.3
[Run file](02-off-by-one.md)

<details><summary>Full AI response</summary>

# Code Review: `src/pagination.js`

**Verdict: Request changes** — both functions contain correctness bugs.

## Critical issues

### 1. Off-by-one error in `getPage` (line ~7)
The docstring says pages are 1-based, but the math is 0-based:

```js
const start = page * pageSize;   // BUG
const start = (page - 1) * pageSize;  // correct for 1-based
```

As written, `getPage(items, 1, 10)` skips the first 10 items and returns items 10–19. Page 1 would silently drop data — the worst kind of pagination bug since nothing crashes.

### 2. `totalPages` drops the partial last page (line ~15)

```js
return Math.floor(items.length / pageSize);  // BUG
return Math.ceil(items.length / pageSize);   // correct
```

With 25 items and pageSize 10, this returns 2 instead of 3, so the last 5 items are unreachable. Combined with bug 1, data loss in both directions.

## Additional concerns

- **No input validation**: `pageSize <= 0` yields `Infinity`/`NaN` from `totalPages` and odd slices from `getPage`. `page < 1` produces negative indices (`slice` silently wraps to end-of-array — very surprising behavior). Consider throwing on `page < 1`, `pageSize < 1`, or non-integer inputs.
- **Out-of-range `page`**: returns `[]` silently, which may be acceptable, but worth documenting.
- **Naming**: `totalPages` takes `items` (the array) rather than a count — fine, but naming the param `items` while `getPage` also takes `items` is consistent, so OK. Just flagging that a `count`-based variant is often more reusable.
- **Mutability/copy**: `slice` returns a shallow copy — good, but the JSDoc should specify return type (`Array`, `number`) and `@param`/`@returns` tags for consistency with typical doc style.

## Suggested fix

```js
function getPage(items, page, pageSize) {
  if (pageSize < 1) throw new RangeError('pageSize must be >= 1');
  if (page < 1) throw new RangeError('page must be >= 1');
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

function totalPages(items, pageSize) {
  if (pageSize < 1) throw new RangeError('pageSize must be >= 1');
  return Math.ceil(items.length / pageSize);
}
```

**Tests to add before merging**: page 1 boundary, last partial page, empty array, `pageSize` > length, and invalid inputs. These are exactly the cases that would have caught both bugs.

</details>

### 03-race-condition — 60.0
[Run file](03-race-condition.md)

<details><summary>Full AI response</summary>

# Code Review: `src/counter.cs`

## Summary
The code compiles and works correctly in single-threaded use, but `RequestHandler.HandleAllAsync` explicitly invokes `stats.Inc` from multiple threads via `Task.Run`/`Task.WhenAll`. That makes the underlying `Dictionary` race-prone — this is the central defect.

## Findings

### 🔴 Critical — `Dictionary<string,int>` is not thread-safe (lines 7–16, 32–36)
`Inc` performs a read-modify-write (`TryGetValue` then indexed set) and `HandleAllAsync` runs it concurrently. Consequences:
- **Lost updates**: two threads can both read count `N` and both write `N+1`.
- **Corruption**: concurrent writes during a dictionary resize can corrupt internal buckets, leading to infinite loops or `IndexOutOfRangeException` on later reads — a well-documented failure mode for `Dictionary`.
- Even `Count`/`Snapshot` reading while another thread writes is unsafe.

**Fix options:**
- Use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)` or `Interlocked` on the value.
- Or guard all access with a `lock`.
- Better still: since `Task.Run` parallelism here buys nothing for a cheap increment, just iterate sequentially — the simplest correct code.

### 🟠 Major — `Snapshot()` returns the live mutable dictionary (lines 25–28)
Callers get a direct reference to internal state: they can mutate it, and their reads race with concurrent `Inc` calls (enumerating a `Dictionary` during mutation throws `InvalidOperationException`). Return a copy:
```csharp
public Dictionary<string,int> Snapshot()
{
    lock (gate) return new Dictionary<string,int>(counts);
}
```
(or `ToDictionary`/`IReadOnlyDictionary`).

### 🟡 Minor — Parallelism overhead
`Task.Run` per path for an O(1) increment will usually be *slower* than a sequential loop due to thread-pool scheduling. If `paths` is large, consider `Parallel.ForEach` with partitioned local counters merged at the end.

### 🟡 Minor — `Inc` can be simplified
Single-indexer form is equivalent and avoids a double lookup... actually, the current two-step form is fine, but `counts[path] = counts.GetValueOrDefault(path) + 1;` is cleaner. Style only.

### ℹ️ Note — `counts` isn't marked `readonly`
`private readonly Dictionary<...> counts` would prevent accidental reassignment.

## Recommendation
Request changes. At minimum: replace the dictionary with `ConcurrentDictionary` + `AddOrUpdate`, make `Snapshot` return a copy, and seriously consider dropping `Task.Run` entirely unless there's real CPU-bound work to parallelize.

</details>

### 04-missing-error-handling — 76.7
[Run file](04-missing-error-handling.md)

<details><summary>Full AI response</summary>

# Code Review: `src/config.ts`

Thanks for the addition — a few issues here that I'd want addressed before merge, ranging from correctness bugs to missing validation.

## 🔴 Bugs / Correctness

**1. `writeBackup` leaks the file descriptor**
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
The file descriptor is never closed via `fs.closeSync(fd)`. Under repeated calls this leaks FDs and on some platforms can produce incomplete writes or `EMFILE` errors. If you want the simpler API, `fs.writeFileSync(path, data)` does the same thing in one call without the leak. If you keep `openSync`, wrap in `try/finally` with `fs.closeSync(fd)`.

**2. `loadConfig` returns untyped, unvalidated data**
```ts
const cfg = JSON.parse(raw)
return cfg
```
`JSON.parse` returns `any`, so this silently satisfies the `AppConfig` return type while providing no guarantee the file actually contains `port`/`dbUrl` — a missing or mistyped field becomes a runtime failure far downstream. Either validate explicitly, or use a schema validator (zod, valibot, etc.). If you don't want a dependency, a manual check like `typeof cfg.port === "number"` before returning goes a long way.

**3. `fetchRemoteConfig` ignores HTTP errors and lacks validation**
```ts
const res = await fetch(url)
return res.json()
```
- No check of `res.ok` — a 404/500 HTML error page will be passed to `res.json()` and produce a confusing `SyntaxError` instead of a meaningful message.
- `res.json()` also returns `any`, so same unvalidated-shape problem as `loadConfig`.
- Consider a timeout (`AbortSignal.timeout(...)`) — a hung remote will otherwise block indefinitely.
- `res.json()` returns `Promise<any>` and you're returning it directly into `Promise<AppConfig>`; fine, but see the type-safety note below.

## 🟡 Minor / Consistency

**4. Sync vs async mixing**
`loadConfig` and `writeBackup` are synchronous while `fetchRemoteConfig` is async. If `loadConfig` is called at startup that's defensible, but `writeBackup` doing synchronous I/O on a hot path will block the event loop. Worth a comment or making it async (`fs.promises.writeFile`).

**5. Style inconsistency**
The file mixes `;` and no-`;` line endings (`port: number;` vs `import ... "fs"`). Pick whichever matches the project convention.

**6. Unhandled errors**
`JSON.parse` on malformed config throws a bare `SyntaxError`; consider wrapping with context like `Failed to load config at ${path}: ...` — debugging "Unexpected token" with no filename is painful.

## Suggested shape

```ts
export function loadConfig(path: string): AppConfig {
  const raw = fs.readFileSync(path, "utf8")
  const cfg: unknown = JSON.parse(raw)
  if (typeof cfg !== "object" || cfg === null
      || typeof (cfg as AppConfig).port !== "number"
      || typeof (cfg as AppConfig).dbUrl !== "string") {
    throw new Error(`Invalid config at ${path}`)
  }
  return cfg as AppConfig
}
```

**Verdict:** Request changes — the FD leak and the two unchecked `any` → `AppConfig` casts are the must-fixes.

</details>

### 05-clean-refactor — 91.7
[Run file](05-clean-refactor.md)

<details><summary>Full AI response</summary>

## Code Review

**Verdict: Approve — behavior is equivalent, no blocking issues.**

### Correctness
- `items.Sum(item => item.Price * item.Quantity)` is semantically identical to the `foreach` accumulation. `Enumerable.Sum` with `decimal` selector accumulates in `decimal` without loss of precision.
- `subtotal * (1 + taxRate)` is algebraically identical to `total + total * taxRate`. The literal `1` is an `int`, but it implicitly converts to `decimal` in the expression, so there's no type error.
- `Sum` returns `0m` for an empty sequence, matching the old `total = 0m` initialization — no behavioral change for empty lists.
- Null `items` threw `NullReferenceException` before (foreach) and throws `ArgumentNullException` now (LINQ guards it) — slightly different exception type, but unlikely to matter.

### Minor suggestions (non-blocking)
1. **`1m` literal for clarity** — `subtotal * (1m + taxRate)` makes the decimal intent explicit and avoids relying on implicit int→decimal conversion. Cosmetic, but consistent with the old `0m` style.
2. **Overflow behavior** — same as before (`decimal` accumulates without checked context in both versions), so no change, just noting `Sum` uses `checked` internally; if individual line items can be extreme, `item.Price * item.Quantity` could throw `OverflowException`. That's a pre-existing characteristic worth being aware of.
3. Consider whether `List<Item>` could be `IEnumerable<Item>` or `IReadOnlyList<Item>` — LINQ removes the last reason to require a concrete `List`.

No changes required to merge.

</details>

### 06-typos — 61.7
[Run file](06-typos.md)

<details><summary>Full AI response</summary>

# Code Review

## Summary
Adds an `Account` interface, a `createAccount` function, a `getAdress` getter, and a couple of string constants. The structure is reasonable, but there are several typos, a logic gap, and a spelling-consistency issue worth addressing.

## Issues

### Bugs / Correctness

1. **`createAccount` never validates or normalizes `email`** — The JSDoc says "We recieve the raw form input and normalize it," but only `username` is trimmed/lowercased. `email` is stored verbatim (whitespace, casing, invalid format all preserved). Either normalize/validate it or fix the doc comment.

2. **`timeoutMs` is accepted but unused** — `opts.timeoutMs` is destructured via `Partial<typeof DEFAULTS>` but only `maxRetries` is read. Either use it or don't accept it yet. Accepting dead options is misleading.

3. **`maxRetries` is computed but never used for retrying** — `retires` only appears in a `console.log`. The function implies retry behavior that doesn't exist. Also, JSDoc promises "sends a welcome email" — no email is sent anywhere.

### Typos

4. **`retires`** should be `retries` (variable name, line with `opts.maxRetries ?? DEFAULTS.maxRetries`).
5. **`getAdress`** should be `getAddress` — this is a public API name, so the typo will propagate to every caller. Fix before this ships.
6. **Error message:** `"Username lenght must be at least 3 charaters."` → "length", "characters". User-facing strings with typos look sloppy.
7. **Doc comment:** "recieve" → "receive".
8. **`TEXT = "teh quick brown fox"`** → "the". If this is intentional placeholder/test data, fine — but it looks like a typo.

### Style / Consistency

9. **`LABEL = "Acme Colour Labs"`** — British "Colour" while the rest of the file uses American spelling ("normalize"). Fine if it's a brand name; flag it in case it's accidental.
10. **Inconsistent semicolons** — `DEFAULTS` and most statements omit semicolons; the file header doesn't establish a convention. Match the repo's lint config.
11. **Shorthand property:** `{ username: username }` can be `{ username }`.
12. **`getAdress` is a trivial getter** — `account.address` is already public on the interface; the wrapper adds no value unless you plan to add formatting/lookup logic.

### Minor

13. **Missing semicolon/brace style consistency** and no newline issues aside, consider trimming `input.address` too if "normalize" is the contract.
14. **No tests or validation of `opts` bounds** — e.g., `maxRetries: -1` or `timeoutMs: 0` would pass silently.

## Recommendations

- Rename `getAdress` → `getAddress` and `retires` → `retries` before merge (API surface).
- Either implement the promised email send + retry/timeout behavior, or narrow the JSDoc and drop `timeoutMs`.
- Fix error-message and comment typos.
- Normalize (or validate) `email` to match the documented contract.

**Verdict:** Request changes — mostly cosmetic, but the public `getAdress` typo and the doc/behavior mismatch should be fixed before this lands.

</details>

---
