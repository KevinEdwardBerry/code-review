# v7 - 2026-10-09 — Detailed results

- Prompt: `prompts/code-review.v7.md`
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **96.4/100** (-2.8 vs v7-00 (99.2))
- Hard fails: 06-typos — fabricated

## What changed
No changes vs the previous evaluated prompt; this is a rerun of the identical `prompts/code-review.v7.md` file.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-csharp-sql-injection | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 |
| 02-off-by-one | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +0.0 |
| 03-race-condition | 3 | 2 | 2 | 3 | 3 | 3 | 3 | 88.3 | -11.7 |
| 04-missing-error-handling | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 |
| 06-typos | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 | -5.0 |


| Category | Found | Total |
|---|---:|---:|
| misspelling | 1 | 1 |
| swap | 3 | 3 |
| missing_letter | 2 | 2 |


## Observations / next changes
Same six fixtures as v7-00, all judged successfully, so per-fixture and overall deltas are valid.

- **03-race-condition dropped -11.7 points:** the review split the `Inc` check-then-act race into two findings (lines 13 and 15) and rated the second one Medium. The expected `race_in_inc` is a single High finding; the extra report lowers Precision and Severity calibration.
- **06-typos now hard-fails on fabricated:** CITATION_CHECK reports the cited `src/accounts.ts:32` does not match any quoted excerpt in that finding, triggering the hard-fail `fabricated` rule and lowering Actionability.
- **02-off-by-one stays at 95.0:** `totalPages` is still rated High (expected Medium) despite the v7 calibration example, matching the v7-00 miss.
- **01, 04, 05 remain 100.0 with no hard fails.**

**Typo recall (06):** all six typos were found; recall per category is unchanged at 1/1 misspelling, 3/3 swap, 2/2 missing_letter.

**Suggested prompt changes:**
1. Require every cited line in a finding to have a matching quoted excerpt; do not allow references like "also update the use at line 32" without quoting that line.
2. In the concurrency rule, explicitly group the check-then-act write and the first-increment write into a single high-severity race finding.
3. Clarify that exported/public-API typos (e.g., `getAdress`) are Medium (breaking-change cost) rather than Low.
4. Add one or two fresh fixtures to test whether the v7 rules generalize beyond the current six.

## Per-fixture results
### [01-csharp-sql-injection](01-csharp-sql-injection.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
The change adds a customer repository whose email lookup is built via string interpolation, introducing a SQL injection vulnerability.

## Findings
[Critical] src/CustomerRepository.cs:14 — SQL injection via interpolated query
`var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`
Impact: `email` is inserted directly into the SQL text, so a value like `' OR '1'='1` (or worse, a stacked statement) lets an attacker bypass the lookup filter or execute arbitrary SQL.
Fix: Use a parameterized query, e.g. `var sql = "SELECT Id, Email FROM Customers WHERE Email = @email";` and `command.Parameters.AddWithValue("@email", email);` (or `command.Parameters.Add("@email", SqlDbType.NVarChar).Value = email;`).

## Verdict
Request changes

</details>

### [02-off-by-one](02-off-by-one.md) — 95.0
<details><summary>Full AI response</summary>

## Summary
The new pagination helpers contain two arithmetic bugs: `getPage` treats the page number as 0-based despite the documented 1-based contract, and `totalPages` truncates instead of rounding up, losing the last partial page.

## Findings
[High] src/pagination.js:7 — Off-by-one makes page 1 skip the first `pageSize` items
> `  7 | +  const start = page * pageSize;`
The docstring states `page` is 1-based, but with `page = 1`, `start = pageSize`, so the first `pageSize` items are never returned and the last page goes out of range. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `Math.floor` drops the final partial page
> ` 16 | +  return Math.floor(items.length / pageSize);`
For 10 items with `pageSize = 3`, this returns 3 instead of 4, so the last page of items is unreachable. Fix: `return Math.ceil(items.length / pageSize);`

## Verdict
Request changes

</details>

### [03-race-condition](03-race-condition.md) — 88.3
<details><summary>Full AI response</summary>

## Summary
The change adds a request counter that mutates a plain `Dictionary` from parallel tasks, making it thread-unsafe.

## Findings
[High] src/counter.cs:13 — Unsynchronized write to shared dictionary
`            counts[path] = count + 1;`
`Inc` is invoked via `Task.Run` inside `Task.WhenAll` (line 35), so multiple threads concurrently mutate `counts`. `Dictionary<TKey,TValue>` is not thread-safe; concurrent writes can lose increments and corrupt internal state, potentially throwing on later reads/writes. Fix: guard `Inc`/`Count`/`Snapshot` with a lock, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd`.

[Medium] src/counter.cs:15 — Second unsynchronized write path
`            counts[path] = 1;`
Same race as above for the first-increment path; must be under the same lock or use `ConcurrentDictionary`.

[Medium] src/counter.cs:20 — Unsynchronized read of shared dictionary
`        return counts.TryGetValue(path, out var count) ? count : 0;`
`Count` can read `counts` while another thread is writing it, which is undefined behavior for `Dictionary` (torn reads/exceptions possible). Fix: take the same lock, or use `ConcurrentDictionary`.

[Medium] src/counter.cs:25 — Snapshot returns the live dictionary and reads it unsynchronized
`        return counts;`
This exposes the mutable internal dictionary to callers and returns it while other threads may be mutating it. Fix: return a copy under the lock (e.g., `new Dictionary<string,int>(counts)`) or use `ConcurrentDictionary` and return a snapshot copy.

## Verdict
Request changes

</details>

### [04-missing-error-handling](04-missing-error-handling.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
Adds a small helper that POSTs a payload to a URL; the only demonstrated defect is that it silently ignores HTTP-level delivery failures.

## Findings
[Medium] src/webhook.ts:2 — HTTP error responses are silently treated as successful delivery
`  await fetch(url, {`
`fetch` resolves without throwing on non-2xx responses (4xx/5xx), so `deliverWebhook` reports success to callers even when the webhook was rejected, making failures invisible. Check `res.ok`/`res.status` and throw or return an error so callers can handle failed deliveries.

## Verdict
Approve with nits

</details>

### [05-clean-refactor](05-clean-refactor.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
Low-risk refactor replacing a manual accumulation loop with LINQ `Sum`; behavior is equivalent.

## Findings
None.

## Verdict
Approve

</details>

### [06-typos](06-typos.md) — 95.0
<details><summary>Full AI response</summary>

## Summary
Low-risk addition of account creation helpers; the only demonstrated defects are spelling errors in an exported function name, a user-facing error message, a public string constant, and comments/local identifiers.

## Findings
[Low] src/accounts.ts:36 — Misspelled exported function name `getAdress`
`export function getAdress(account: Account): string {`
Callers must use the misspelled name `getAdress`; renaming later becomes a breaking change.
Fix: rename to `getAddress` (keep an alias if the name is already consumed).

[Low] src/accounts.ts:23 — Misspellings in user-facing error message ("lenght", "charaters")
`    throw new Error("Username lenght must be at least 3 charaters.")`
Users see a misspelled validation message.
Fix: `"Username length must be at least 3 characters."`

[Low] src/accounts.ts:40 — Misspelling in exported public string constant ("teh")
`export const TEXT = "teh quick brown fox"`
The exported constant contains a typo.
Fix: `"the quick brown fox"` (unless intentionally testing typo data).

[Low] src/accounts.ts — Grouped cosmetic typos in comment and local identifier ("recieve", "retires")
` * We recieve the raw form input and normalize it.` (src/accounts.ts:16)
`  const retires = opts.maxRetries ?? DEFAULTS.maxRetries` (src/accounts.ts:19)
Comment and local variable misspellings reduce readability; no functional impact.
Fix: "receive" and `retries` (also update the use at src/accounts.ts:32).

## Verdict
Approve with nits

</details>



---
