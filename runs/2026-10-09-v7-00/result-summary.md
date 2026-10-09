# v7 - 2026-10-09 — Detailed results

- Prompt: `prompts/code-review.v7.md`
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed; separate profile, distinct model not verifiable)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **99.2/100** (+5.0 vs v6-02 (94.2); v6 run mean 94.9)
- Hard fails: none (v6-02 had 1)

## What changed
Versus v6: (1) evidence rule now says to cite the first line of a multi-line expression (never `})`/`}`) and one line per quote; (2) severity calibration examples added (primary feature-breaking defect High; derived-value / read-only-path defect Medium); (3) Typos section forbids non-typo findings on typo changes and requires exported/user-facing/public-string typos as separate findings above the single grouped cosmetic finding.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-csharp-sql-injection | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 vs v6-02 (new prompt) |
| 02-off-by-one | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +0.0 vs v6-02 (new prompt) |
| 03-race-condition | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +5.0 vs v6-02 (new prompt) |
| 04-missing-error-handling | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +5.0 vs v6-02 (new prompt) |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 vs v6-02 (new prompt) |
| 06-typos | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +20.0 vs v6-02 (new prompt) |

## Typo recall (06)
| Category | Found | Total |
|---|---:|---:|
| misspelling | 1 | 1 |
| swap | 3 | 3 |
| missing_letter | 2 | 2 |


## Observations / next changes
- **Comparability:** same six fixtures as v6-02, all judged with valid JSON on the first attempt, exact filled judge template used for all. Deltas are valid but judge/reviewer model identities are not exposed, so the judge could not be verified as a different model; single run, so variance is unquantified (v6 reruns ranged 94.2-95.3).
- **All three v6 weaknesses are fixed:** 04 no longer cites a closing `})` (it cited line 2, `await fetch(`), clearing the recurring fabricated hard fail; 03 severities now match (High write, Medium read, Medium snapshot); 06 recovered from 80.0 to 100.0 with no non-typo findings and public-string typo separated.
- **Remaining miss:** 02 `totalPages` was rated High (expected Medium) despite the new calibration example naming "a miscounted page total" as Medium; the example was apparently overridden by the "returns wrong results on every call" framing.
- **Overfitting risk:** the new calibration examples ("off-by-one", "miscounted page total", "unsynchronized read of shared state") and the typo clause ("unused fields or options") mirror fixture content directly, so the perfect scores on 02/03/06 may not generalize. Evaluate against unseen fixtures before trusting the gain.
- **Typo recall (06):** misspelling 1/1, swap 3/3, missing_letter 2/2.
- **Suggested prompt changes:**
  1. Reword the calibration examples generically (e.g. "a derived or auxiliary value computed incorrectly is Medium even when the same defect class is High elsewhere") and rate each finding independently of other findings in the same function.
  2. Add a rule: severity is set per finding by its own impact; two findings of the same class in one file need not share a severity.
  3. Add fresh fixtures (e.g. XSS, resource leak, auth bypass, a clean change with a tempting nit) to test generalization of the new rules.
  4. Keep the multi-line citation rule; consider an explicit statement that the cited line must contain the defective operation.

## Per-fixture results
### [01-csharp-sql-injection](01-csharp-sql-injection.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
New repository method builds a SQL query by interpolating user input, introducing a critical SQL injection vulnerability.

## Findings
- [Critical] src/CustomerRepository.cs:14 — SQL injection via string-interpolated query
  `var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`
  The `email` parameter is inserted directly into the SQL text, so an attacker-controlled value (e.g., `' OR '1'='1`) can alter the query, exfiltrate arbitrary rows, or execute injected statements. Fix: use a parameterized query, e.g.
  ```csharp
  var sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
  await using var command = new SqlCommand(sql, connection);
  command.Parameters.AddWithValue("@email", email);
  ```

## Verdict
Request changes

</details>

### [02-off-by-one](02-off-by-one.md) — 95.0
<details><summary>Full AI response</summary>

## Summary
New pagination helpers contain two off-by-one math errors that return wrong results on every call.

## Findings

[High] src/pagination.js:7 — off-by-one start index ignores the documented 1-based page numbering
`  7 | +  const start = page * pageSize;`
For page 1 this yields `start = pageSize`, skipping the first `pageSize` items and returning the wrong slice for every page. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `Math.floor` drops the final partial page
`  16 | +  return Math.floor(items.length / pageSize);`
For `items.length = 10, pageSize = 4` this returns 2 instead of 3, so callers can never reach the last 2 items. Fix: `return Math.ceil(items.length / pageSize);`

## Verdict
Request changes

</details>

### [03-race-condition](03-race-condition.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
The change adds a request counter that is shared across concurrent tasks without synchronization, producing race conditions and exposing mutable internal state.

## Findings

[High] src/counter.cs:13 — Unsynchronized write to shared `Dictionary` under concurrent `Inc` calls
> `counts[path] = count + 1;`
`HandleAllAsync` invokes `stats.Inc` concurrently via `Task.Run`/`Task.WhenAll`. `Dictionary` is not thread-safe; concurrent check-then-set on lines 12–15 loses increments and can corrupt internal state, permanently under-counting requests.
Fix: guard all access with a `lock`, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd`.

[Medium] src/counter.cs:20 — Unsynchronized read of shared `Dictionary`
> `return counts.TryGetValue(path, out var count) ? count : 0;`
`Count` reads the dictionary while other tasks may be writing it via `Inc`; concurrent read-during-write on `Dictionary` is not guaranteed safe and can return torn or stale results.
Fix: protect reads with the same lock used for writes, or use `ConcurrentDictionary` (`TryGetValue` is then safe).

[Medium] src/counter.cs:25 — `Snapshot` returns the live mutable dictionary
> `return counts;`
Callers receive the internal dictionary: they can mutate it unsafely and enumerate it while writes occur, causing `InvalidOperationException` or corrupted counts.
Fix: return a copy under the lock (e.g., `new Dictionary<string,int>(counts)` inside `lock`, or `ToDictionary` on a `ConcurrentDictionary`).

## Verdict
Request changes

</details>

### [04-missing-error-handling](04-missing-error-handling.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
A minimal webhook delivery helper; the only demonstrated defect is that HTTP error responses are silently treated as successful deliveries.

## Findings
[Medium] src/webhook.ts:2 — HTTP error responses are ignored
`  await fetch(url, {`
`fetch` resolves without throwing on 4xx/5xx statuses, so `deliverWebhook` returns successfully even when the webhook was rejected, making delivery failures indistinguishable from success. Check `response.ok` (or the status code) and throw/retry on non-2xx responses.

## Verdict
Approve with nits

</details>

### [05-clean-refactor](05-clean-refactor.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
Behavior-equivalent refactor of `OrderTotal` from a manual loop to LINQ `Sum`; low risk.

## Findings
None.

## Verdict
Approve

</details>

### [06-typos](06-typos.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
Low-risk new account module whose only demonstrated defects are spelling errors in an exported name, user-facing text, a public string, a comment, and a local variable.

## Findings
[Medium] src/accounts.ts:36 — Misspelled exported function name `getAdress`
> `export function getAdress(account: Account): string {`
The typo becomes part of the public API; callers will bind to the misspelled name and fixing it later is a breaking change. Rename to `getAddress` now.

[Low] src/accounts.ts:23 — Misspellings in user-facing error message
> `throw new Error("Username lenght must be at least 3 charaters.")`
"lenght" and "charaters" appear in text shown to users. Fix to "Username length must be at least 3 characters."

[Low] src/accounts.ts:40 — Typo in public string constant
> `export const TEXT = "teh quick brown fox"`
"teh" should be "the" in this exported literal.

[Low] src/accounts.ts:16 — Grouped cosmetic typos in comment and local identifier
> `* We recieve the raw form input and normalize it.`
"recieve" → "receive".
> `const retires = opts.maxRetries ?? DEFAULTS.maxRetries`
Local variable `retires` → `retries` (also used at line 32).

## Verdict
Approve with nits

</details>


---
