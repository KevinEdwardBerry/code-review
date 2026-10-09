# v4 - 2026-10-09 — Detailed results

- Prompt: `prompts/code-review.v4.md`
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **93.9/100** (+7.5 vs previous v4 run)
- Hard fails: 02-off-by-one — fabricated; 03-race-condition — missed_critical; 05-clean-refactor — fabricated; 06-typos — fabricated

## What changed
The v3-to-v4 prompt diff adds explicit `file:line` and severity-level instructions; detailed new-file line reconstruction and exact quote/anchor requirements; a rule against speculative future-growth and micro-optimization findings; stricter citations for concurrent access paths; more concise grouping guidance for cosmetic typos; and more precise line-specific evidence requirements in the response format.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 01-csharp-sql-injection | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +18.3 (prev 81.7; prior label: 01-sql-injection) |
| 02-off-by-one | 3 | 3 | 3 | 1 | 3 | 3 | 3 | 90.0 | -5.0 (prev 95.0) |
| 03-race-condition | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 90.0 | +15.0 (prev 75.0) |
| 04-missing-error-handling | 2 | 3 | 3 | 3 | 3 | 3 | 3 | 90.0 | +10.0 (prev 80.0) |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 2 | 3 | 98.3 | -1.7 (prev 100.0) |
| 06-typos | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 | +8.3 (prev 86.7) |

Overall delta is +7.5 from the previous v4 run's 86.4. Both runs scored the same six fixtures; the SQL injection fixture is matched to the prior run's `01-sql-injection` label.

Hard-fail flags: 02-off-by-one (`fabricated`, due incorrect cited lines); 03-race-condition (`missed_critical`, Count's unsynchronized read was missed); 05-clean-refactor (`fabricated`, incorrect line references in verification notes); 06-typos (`fabricated`, cited line numbers do not match the cited code). No other fixture hard-failed.

## Typo recall
| Category | Found | Total | Recall |
|---|---:|---:|---:|
| misspelling | 1 | 1 | 100% |
| swap | 3 | 3 | 100% |
| missing_letter | 2 | 2 | 100% |

## Observations / next changes

- The reviewer found every seeded issue in the SQL injection, pagination, and typo fixtures, but missed `Count`'s unsynchronized read in the race fixture and `loadConfig` validation/error-context issues in the config fixture.
- Citation accuracy remains the clearest weakness: incorrect line numbers lowered actionability on pagination and typos and triggered fabricated hard fails on pagination, the clean refactor's verification notes, and typos. The refactor response also added verification commentary beyond the requested three-heading structure.
- Independent citation spot-check found a judge blind spot on 01-csharp-sql-injection: the review cites line 14, but the interpolated SQL is at new-file line 15. The schema-valid judge JSON was retained without a human override, so the official score and hard-fail flag above remain the judge's output.
- Relative to the previous run, pagination regressed by 5.0 points and the clean-refactor fixture by 1.7; the former also newly hard-failed for fabricated line references. The race and config fixture scores improved, though race remains a hard fail.

Suggested prompt changes:
1. Require a final mechanical audit that maps each quoted excerpt to its actual new-file line number; omit every finding or verification note whose anchor does not match exactly.
2. Add a completeness pass over every independent function and shared-state read, write, and snapshot path before finalizing.
3. Explicitly prohibit extra post-findings verification sections; for clean diffs, use only the required headings and state `None.` when appropriate.
4. Require config reviews to separately check resource closure, HTTP status, and parsed configuration shape/error reporting when those paths appear in the diff.

## Per-fixture results

### 01-csharp-sql-injection
[Run file](01-csharp-sql-injection.md)

<details><summary>Full AI response</summary>

## Summary
New repository class introduces a critical SQL injection vulnerability by interpolating user input directly into a query.

## Findings

- [Critical] src/CustomerRepository.cs:14 — SQL injection via string interpolation
  - Evidence: ``var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";``
  - Impact: The `email` parameter is concatenated into the SQL text unescaped, allowing arbitrary SQL execution (data exfiltration, modification, or authentication bypass depending on caller input).
  - Fix: Use a parameterized query, e.g.:
    ```csharp
    var sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
    await using var command = new SqlCommand(sql, connection);
    command.Parameters.AddWithValue("@email", email);
    ```

## Verdict
Request changes
</details>

### 02-off-by-one
[Run file](02-off-by-one.md)

<details><summary>Full AI response</summary>

## Summary
The new pagination helpers contain an off-by-one error in `getPage` and a page-count truncation bug in `totalPages`, both contradicting the documented contract.

## Findings
- [High] src/pagination.js:5 — `getPage` treats a 1-based page number as 0-based. `const start = page * pageSize;` skips the first `pageSize` items for `page=1` (it returns the second page), and always returns the wrong slice. Fix: `const start = (page - 1) * pageSize;`.
- [Medium] src/pagination.js:14 — `totalPages` uses `Math.floor`, so a trailing partial page is not counted (e.g., 5 items with pageSize 2 yields 2 instead of 3), and the last items are unreachable via `totalPages`. Fix: `return Math.ceil(items.length / pageSize);`

## Verdict
Request changes
</details>

### 03-race-condition
[Run file](03-race-condition.md)

<details><summary>Full AI response</summary>

## Summary
The change adds a request-stats counter that is mutated from parallel tasks via a non-thread-safe `Dictionary`, and exposes its internal mutable state through `Snapshot`.

## Findings

[High] src/counter.cs:35 — `await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));` — `Inc` is invoked concurrently from multiple thread-pool threads, but `counts` is a plain `Dictionary` guarded by no lock. `Dictionary` is not thread-safe for concurrent writes: simultaneous `TryGetValue`/indexer-set pairs can lose increments (read-modify-write race at src/counter.cs:13-16, `counts[path] = count + 1;`), and concurrent structural mutations can corrupt the internal buckets, causing exceptions or infinite loops in readers. Fix: use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or serialize access with a `lock`.

[Medium] src/counter.cs:26 — `return counts;` in `Snapshot()` returns the live internal dictionary rather than a copy. Callers can mutate the stats state directly, and enumerating the returned dictionary while `Inc` writes to it throws `InvalidOperationException`. Fix: `return new Dictionary<string, int>(counts);` (taken under the same lock/concurrent collection used for writes).

## Verdict
Request changes
</details>

### 04-missing-error-handling
[Run file](04-missing-error-handling.md)

<details><summary>Full AI response</summary>

## Summary
Adds config loading, file backup writing, and remote config fetch helpers; main risks are a leaked file descriptor and unchecked HTTP response status.

## Findings

[Medium] src/config.ts:16 — file descriptor never closed in `writeBackup`
```ts
fs.writeSync(fd, data)
```
`fs.openSync` returns an fd that is never passed to `fs.closeSync`, leaking a descriptor on every call (including on `writeSync` throw). Fix: wrap in try/finally with `fs.closeSync(fd)`, or simply use `fs.writeFileSync(path, data)`.

[Medium] src/config.ts:21 — `fetchRemoteConfig` ignores HTTP error status
```ts
return res.json()
```
On non-2xx responses (e.g. 404/500 returning an HTML error page or unrelated JSON), this either throws a confusing parse error or silently returns data that isn't an `AppConfig`. Fix: check `if (!res.ok) throw new Error(...)` before parsing.

## Verdict
Request changes
</details>

### 05-clean-refactor
[Run file](05-clean-refactor.md)

<details><summary>Full AI response</summary>

## Summary
Low-risk refactor replacing a manual accumulation loop with LINQ `Sum` and algebraically combining the tax calculation; the behavior is equivalent.

## Findings
None.

Verification notes (no defects found):
- `src/totals.cs:9` — `items.Sum(item => item.Price * item.Quantity)`: for `decimal`, LINQ `Sum` returns `0m` for an empty sequence, identical to the previous `var total = 0m;` initialization. Null `items` throws `ArgumentNullException` vs. the old `NullReferenceException` — a marginally better exception type, not a defect.
- `src/totals.cs:10` — `return subtotal * (1 + taxRate);` is algebraically equivalent to `total + total * taxRate`; decimal multiplication distributes exactly here (no rounding ambiguity beyond the single multiplication already present). `1 + taxRate` promotes `1` to decimal, so no int arithmetic issue.
- The `using System.Linq;` addition at `src/totals.cs:2` is required and correct.

## Verdict
Approve
</details>

### 06-typos
[Run file](06-typos.md)

<details><summary>Full AI response</summary>

## Summary
Low-risk addition of an `Account` service with several spelling defects in exported identifiers and user-facing strings, but no functional or security defects.

## Findings

- [Low] src/accounts.ts:33 — Misspelled exported function name `getAdress` (should be `getAddress`).
  ```ts
  export function getAdress(account: Account): string {
  ```
  Impact: typo is baked into the public API; renaming later is a breaking change. Fix: rename to `getAddress` before release.

- [Low] src/accounts.ts:37 — Typo in exported string constant: `"teh quick brown fox"` (should be `"the quick brown fox"`).
  Impact: user-facing/public string contains a misspelling. Fix: correct to `"the quick brown fox"`.

- [Low] src/accounts.ts:21 — Typos in user-facing error message: `"Username lenght must be at least 3 charaters."` (should be `"length"` and `"characters"`).
  Impact: misspelled message shown to users/logging consumers. Fix: correct spelling.

- [Low] src/accounts.ts:15 — Docstring typo: `"We recieve the raw form input and normalize it."` (should be `"receive"`).

- [Low] src/accounts.ts:17 — Local variable typo `retires` (should be `retries`), also referenced at line 29 in the `console.log` template.
  ```ts
  const retires = opts.maxRetries ?? DEFAULTS.maxRetries
  ```
  Impact: cosmetic; rename for clarity. Also note the documented "welcome email" behavior in the docstring (line 14) is not implemented — either implement it or remove the claim from the comment.

## Verdict
Approve with nits
</details>

---
