# v6 (rerun) - 2026-10-09 — Detailed results

- Prompt: `prompts/code-review.v6.md`
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed; separate profile, distinct concrete model not verifiable)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **94.2/100** (-1.1 vs v6-01 (95.3); -1.0 vs mean of prior v6 runs (95.2))
- Hard fails: 04-missing-error-handling — fabricated (citation `src/webhook.ts:6` quote does not match line `})`)

## What changed
Rerun: `prompts/code-review.v6.md` is unchanged since the prior v6 runs (`diff` against the previously evaluated prompt is empty). Versus v5, v6 adds the "removed lines cannot be cited" rule, the What-to-report / What-to-check checklist, an explicit final evidence re-check, Low-only nits, and "typos must not outrank functional defects".

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-csharp-sql-injection | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 vs v6-01; +0.0 vs mean |
| 02-off-by-one | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +0.0 vs v6-01; +0.0 vs mean |
| 03-race-condition | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +8.3 vs v6-01; +1.7 vs mean |
| 04-missing-error-handling | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 (FAIL) | +0.0 vs v6-01; +7.5 vs mean |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 vs v6-01; +0.0 vs mean |
| 06-typos | 3 | 2 | 2 | 2 | 2 | 3 | 3 | 80.0 | -15.0 vs v6-01; -15.0 vs mean |

## Typo recall (06)
| Category | Found | Total |
|---|---:|---:|
| misspelling | 1 | 1 |
| swap | 3 | 3 |
| missing_letter | 2 | 2 |


## Observations / next changes
- **Comparability:** same six fixtures, all judged with valid JSON, and this run used the exact filled judge template for every fixture (the prior rerun used a condensed paraphrase for 02–06). Deltas are shown but remain indicative; reviewer/judge model identities are not exposed, so the judge could not be verified as a different model.
- **Recall is stable:** every seeded issue matched on all fixtures; the clean refactor stayed clean.
- **Recurring hard fail on 04:** the reviewer again cited `src/webhook.ts:6` and quoted `})` instead of the `fetch` call at line 2. Same failure as v6-01 (v6-00 did not trip it), so it is a real instability, not noise.
- **Severity:** High was used for `totalPages` (02, expected Medium) and the `Count` read race (03, expected Medium); same pattern as before.
- **06 dropped to 80.0 (-15):** the reviewer added a non-typo finding (`timeoutMs` unused), grouped the public string typo `TEXT` with cosmetic nits (ranking violation), and cited "line 32" in a grouped finding. (Note: line 32 does exist in the diff — it uses `retires` in the console.log — so the judge's "doesn't exist" remark is arguably wrong; a human override could lift precision/actionability.) Typo recall remained 6/6.
- **Suggested prompt changes:**
  1. For single-statement findings, cite the first line of the offending expression (e.g. the `await fetch(` line) and require the quoted text to be exactly that line; never cite a closing `})`/`}` line.
  2. Add severity examples: page-count and read-only-race defects are Medium; primary feature-breaking defects are High.
  3. In the Typos section, forbid non-typo findings on typo-only changes and require exported/public-string typos to be listed as separate findings above the grouped cosmetic ones.
  4. Require grouped findings to cite one line per quoted excerpt, not comma-separated line lists.

## Per-fixture results
### [01-csharp-sql-injection](01-csharp-sql-injection.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
New `CustomerRepository` that builds a SQL query via string interpolation, introducing a SQL injection vulnerability.

## Findings
[Critical] src/CustomerRepository.cs:14 — SQL injection via interpolated `email`
> `var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`

`email` is an unvalidated caller-supplied string interpolated directly into the SQL text. A value such as `' OR '1'='1` (or a `'; DROP TABLE ...--` payload) alters the query, allowing arbitrary data reads or destructive statements depending on connection permissions. Fix by parameterizing:

```csharp
const string sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
await using var command = new SqlCommand(sql, connection);
command.Parameters.AddWithValue("@email", email);
```

## Verdict
Request changes

</details>

### [02-off-by-one](02-off-by-one.md) — 95.0
<details><summary>Full AI response</summary>

## Summary
New pagination helpers contain two correctness bugs: a 1-based off-by-one in `getPage` and use of `Math.floor` instead of `Math.ceil` in `totalPages`.

## Findings
[High] src/pagination.js:7 — `getPage` skips the first `pageSize` items on page 1
> `  const start = page * pageSize;`
The docstring states `page` is 1-based, so `page=1` yields `start = pageSize` instead of `0`, skipping the first page's items. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `totalPages` undercounts when items don't divide evenly
> `  return Math.floor(items.length / pageSize);`
With 11 items and pageSize 10, this returns 1, so the last item is unreachable. Fix: `Math.ceil(items.length / pageSize);`

## Verdict
Request changes

</details>

### [03-race-condition](03-race-condition.md) — 95.0
<details><summary>Full AI response</summary>

## Summary
The new `RequestStats` counter is used from multiple threads by `HandleAllAsync` but wraps a plain `Dictionary` with no synchronization, so all reads and writes are racy.

## Findings
[High] src/counter.cs:12 — unsynchronized read/write of shared `counts` during concurrent `Inc`
`        if (counts.TryGetValue(path, out var count))`
`Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))))` invokes `Inc` on multiple threads over a non-thread-safe `Dictionary`. Races cause lost increments and can corrupt the dictionary's internal buckets (leading to exceptions or hangs). Fix: use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or guard all accesses with a `lock`.

[High] src/counter.cs:20 — unsynchronized read of `counts` in `Count`
`        return counts.TryGetValue(path, out var count) ? count : 0;`
`Total` can be called while `HandleAllAsync` is mutating the dictionary; a `TryGetValue` concurrent with a write/resize is undefined and may throw or return stale/corrupted results. Fix: same as above (`ConcurrentDictionary` or lock on every access).

[Medium] src/counter.cs:25 — `Snapshot` returns the live mutable dictionary
`        return counts;`
Callers receive the internal `Dictionary`, so they can observe or mutate it concurrently with `Inc`, reintroducing races and breaking encapsulation. Fix: return a copy (`new Dictionary<string,int>(counts)` under the lock / `ConcurrentDictionary.ToArray()`-based snapshot).

## Verdict
Request changes

</details>

### [04-missing-error-handling](04-missing-error-handling.md) — 95.0 (hard fail)
<details><summary>Full AI response</summary>

## Summary
A new webhook delivery helper that POSTs a payload but ignores the HTTP response status, so failed deliveries go undetected; otherwise low-risk.

## Findings
[Medium] src/webhook.ts:6 — HTTP response status is never checked, so failed deliveries are silently treated as success
`  })
`fetch` resolves without throwing for non-2xx responses (e.g., 404, 500), and the return value is discarded, so `deliverWebhook` reports success even when the endpoint rejected or failed the request. Impact: callers cannot distinguish delivered from failed webhooks. Fix: capture the response and check `res.ok` (and/or the status code), throwing or returning an error when delivery fails, e.g. `const res = await fetch(...); if (!res.ok) throw new Error(\`Webhook failed: ${res.status}\`)`.

## Verdict
Request changes

</details>

### [05-clean-refactor](05-clean-refactor.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
Low-risk behavior-equivalent refactor replacing a manual accumulation loop with LINQ `Sum`.

## Findings
None.

## Verdict
Approve

</details>

### [06-typos](06-typos.md) — 80.0
<details><summary>Full AI response</summary>

## Summary
Low-risk new account creation helper, but it ships several misspellings including an exported API name and a user-facing error message.

## Findings
- [Medium] src/accounts.ts:36 — Misspelled exported function name `getAdress`
  `export function getAdress(account: Account): string {`
  Callers must use the misspelled name; renaming later is a breaking API change. Fix: rename to `getAddress`.
- [Low] src/accounts.ts:23 — Misspellings in user-facing error message
  `throw new Error("Username lenght must be at least 3 charaters.")`
  Fix: `"Username length must be at least 3 characters."`
- [Low] src/accounts.ts:16,19,40 — Cosmetic typos grouped: comment "We recieve", local variable `retires` (lines 19 and 32), public string `"teh quick brown fox"` (line 40).
  `* We recieve the raw form input and normalize it.`
  `const retires = opts.maxRetries ?? DEFAULTS.maxRetries`
  `export const TEXT = "teh quick brown fox"`
  Fix: `receive`, `retries`, `"the quick brown fox"`. Note "Colour" at line 42 is a valid spelling variant and is not flagged.
- [Low] src/accounts.ts:11 — `timeoutMs` declared but never used; `createAccount` accepts it via `opts` yet ignores it, which may mislead callers expecting a timeout.
  `timeoutMs: 5000`
  Fix: either apply the timeout or remove the option.

## Verdict
Approve with nits

</details>


---
