# v6 (rerun) - 2026-10-09 — Detailed results

- Prompt: `prompts/code-review.v6.md`
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed; chosen as a separate profile, but a distinct concrete model could not be verified)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **95.3/100** (+0.3 vs v6-00; nominal delta against prior same-version mean)
- Hard fails: 04-missing-error-handling — fabricated (citation quote does not match cited line)

## What changed
Compared with v5, v6 explicitly says removed lines cannot be cited; reframes the former review principles as “What to report” and adds a focused checklist for security, correctness, reliability, and separate concurrent access paths. It adds an explicit final evidence re-check, makes the exclusion of future-growth concerns explicit, requires nits to be Low, and says typos must not outrank functional defects. The three-heading response contract remains.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 01-csharp-sql-injection | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 (v6-00 100.0) |
| 02-off-by-one | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +0.0 (v6-00 95.0) |
| 03-race-condition | 3 | 3 | 2 | 2 | 2 | 3 | 3 | 86.7 | -13.3 (v6-00 100.0) |
| 04-missing-error-handling | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 | +15.0 (v6-00 80.0) |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 (v6-00 100.0) |
| 06-typos | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +0.0 (v6-00 95.0) |

All six fixtures match the prior run's fixture set and all judges returned schema-valid JSON. Totals use the prescribed weights, round each fixture to one decimal, then average fixture totals. The numeric deltas are nominal: evaluation fidelity differed from the prior run because the exact filled judge template and full rubric were used for fixture 01, while fixtures 02–06 received a condensed paraphrase of the judge instructions/rubric. The profile is known but model identity is not exposed. Treat small changes as indicative, not a controlled comparison.

## Typo recall
| Category | Found | Total |
|---|---:|---:|
| misspelling | 1 | 1 |
| swap | 3 | 3 |
| missing_letter | 2 | 2 |

## Observations / next changes
- **Full seeded recall and no unseeded findings:** all expected items were matched, and no judge marked any false positives. The clean-refactor fixture remained clean.
- **Citation precision caused the sole hard fail:** fixture 04 identified the right unchecked-HTTP-status issue and proposed the right fix, but cited `src/webhook.ts:6` and quoted `})`; the mechanical check confirmed the quote does not match that line. Cite the actual unchecked `fetch` expression at line 2 and quote that line.
- **Severity/actionability patterns:** the second pagination issue on 02 and the `Count` race on 03 were rated High instead of the expected Medium. The 03 write finding also suggested `Interlocked` as an option even though it does not make unsynchronized `Dictionary` access safe. On 06, all six typos were recalled, but the public-string typo was grouped with cosmetic typos rather than preserving the expected impact ordering.
- **Suggested prompt changes:**
  1. Require the cited line to be the operation that demonstrates the defect (not a nearby closing line), then verify that each quote is the exact cited line before retaining a finding.
  2. Add severity examples distinguishing limited page-count/read defects (Medium) from primary feature-breaking defects (High), and explicitly rank public-string typos above local/comment nits.
  3. For concurrency findings, require suggested synchronization to protect the collection itself; avoid presenting `Interlocked` alone as a remedy for concurrent `Dictionary` access.

## Per-fixture results
### 01-csharp-sql-injection — 100.0
[01-csharp-sql-injection.md](01-csharp-sql-injection.md)

<details><summary>Full AI response</summary>

## Summary
Adds a new `CustomerRepository` with a SQL injection vulnerability in email lookup — high-risk change.

## Findings

[Critical] src/CustomerRepository.cs:14 — SQL injection via string-interpolated query
```
var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";
```
The `email` parameter is interpolated directly into the SQL text. An attacker can supply input like `' OR '1'='1` to bypass the email filter or `'; DROP TABLE Customers;--` to execute arbitrary statements, depending on the SQL Server configuration. This exposes customer data and allows destructive queries.

Fix: use a parameterized query:
```csharp
var sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
await using var command = new SqlCommand(sql, connection);
command.Parameters.AddWithValue("@email", email);
```

## Verdict
Request changes

</details>

### 02-off-by-one — 95.0
[02-off-by-one.md](02-off-by-one.md)

<details><summary>Full AI response</summary>

## Summary
New pagination helpers contain two off-by-one/correctness bugs: `getPage` ignores its documented 1-based contract, and `totalPages` rounds down, dropping the last partial page.

## Findings

[High] src/pagination.js:7 — `getPage` computes a 0-based offset despite the documented 1-based page number
> `  7 | +  const start = page * pageSize;`
The JSDoc states the page is 1-based, but `start = page * pageSize` means `getPage(items, 1, size)` returns items starting at index `size`, skipping the first page entirely. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `totalPages` floors the division, undercounting pages
> ` 16 | +  return Math.floor(items.length / pageSize);`
With `items.length = 10` and `pageSize = 3`, this returns 3 instead of 4, losing access to the last item(s). Fix: use `Math.ceil(items.length / pageSize)`.

## Verdict
Request changes

</details>

### 03-race-condition — 86.7
[03-race-condition.md](03-race-condition.md)

<details><summary>Full AI response</summary>

## Summary
New code introduces a `RequestStats` counter and a handler that increments it concurrently via `Task.Run`, but the underlying `Dictionary` is accessed without any synchronization, making the feature racy and the returned snapshot mutable.

## Findings

[High] src/counter.cs:13 — unsynchronized concurrent write to shared Dictionary
`counts[path] = count + 1;` (also `  15 | +counts[path] = 1;`, enabled by `  35 | +await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));`)
`Task.Run` invokes `Inc` on multiple threads; `Dictionary<K,V>` is not thread-safe for concurrent writes. This can corrupt the internal structure, lose increments, or throw. Fix: guard all accesses with a `lock`, use `Interlocked`, or switch to `ConcurrentDictionary<string,int>` with `AddOrUpdate`.

[High] src/counter.cs:20 — unsynchronized concurrent read of shared Dictionary
`return counts.TryGetValue(path, out var count) ? count : 0;`
`Total` → `Count` reads the dictionary while `HandleAllAsync` may be writing it; reads concurrent with writes are undefined and can return stale/corrupt data or throw. Fix: synchronize this read under the same lock or use `ConcurrentDictionary`.

[Medium] src/counter.cs:25 — Snapshot returns the live internal dictionary
`return counts;`
Callers receive the mutable backing collection: they can read it while writes occur (unsafe enumeration can throw `InvalidOperationException`) and can mutate it directly, bypassing any synchronization. Fix: return a copy under the lock, e.g. `return new Dictionary<string,int>(counts);` or an immutable/read-only snapshot.

## Verdict
Request changes

</details>

### 04-missing-error-handling — 95.0 (FAIL: fabricated citation)
[04-missing-error-handling.md](04-missing-error-handling.md)

<details><summary>Full AI response</summary>

## Summary
A minimal webhook delivery helper; the only demonstrated defect is that HTTP failures are silently ignored.

## Findings
[Medium] src/webhook.ts:6 — Response status never checked, so failed deliveries are silently reported as success
```
  })
```
`deliverWebhook` resolves successfully whenever `fetch` itself does not throw, meaning HTTP error responses (4xx/5xx, e.g., a 500 from the receiver or a 404 from a bad URL) are indistinguishable from a successful delivery. Callers cannot detect or retry failed deliveries. Fix: capture the response and throw or return its status when `!res.ok`, e.g. `const res = await fetch(...); if (!res.ok) throw new Error(\`Webhook delivery failed: ${res.status}\`)`.

## Verdict
Request changes

</details>

### 05-clean-refactor — 100.0
[05-clean-refactor.md](05-clean-refactor.md)

<details><summary>Full AI response</summary>

## Summary
Low-risk refactor replacing a manual accumulation loop with `Enumerable.Sum` and an equivalent tax expression.

## Findings
None.

## Verdict
Approve

</details>

### 06-typos — 95.0
[06-typos.md](06-typos.md)

<details><summary>Full AI response</summary>

## Summary
Low-risk addition of an account creation function with several spelling mistakes in user-facing strings, comments, and an exported function name.

## Findings
- [Low] src/accounts.ts:36 — Exported function name misspelled `getAdress`
  `export function getAdress(account: Account): string {` — part of the public API; consumers will be stuck with the typo. Fix: rename to `getAddress`.
- [Low] src/accounts.ts:23 — Misspellings in user-facing error message
  `throw new Error("Username lenght must be at least 3 charaters.")` — "lenght" → "length", "charaters" → "characters". Fix: `"Username length must be at least 3 characters."`
- [Low] src/accounts.ts — Cosmetic typos in comment, local variable, and public string
  `src/accounts.ts:16` `We recieve the raw form input and normalize it.` — "recieve" → "receive".
  `src/accounts.ts:19` `const retires = opts.maxRetries ?? DEFAULTS.maxRetries` — "retires" → "retries" (also used at line 32).
  `src/accounts.ts:40` `export const TEXT = "teh quick brown fox"` — "teh" → "the" (public string literal; "Colour" at line 42 is a valid variant and not flagged).

## Verdict
Approve with nits

</details>

---
