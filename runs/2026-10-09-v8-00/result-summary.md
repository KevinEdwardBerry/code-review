# v8 - 2026-10-09 — Detailed results

- Prompt: `prompts/code-review.v8.md`
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **99.2/100** (+2.8 vs v7-01 (96.4))
- Hard fails: none

## What changed

v8 refines the concurrency and evidence rules from v7:

- **Concurrency rule:** changed from treating every read/write/snapshot of shared state as its own path to treating each *logical* path as one finding, explicitly making a check-then-act sequence (`if (TryGetValue) ... else ...`) one path and one finding.
- **Evidence rule:** changed from requiring one quote per line as separate citations to allowing multiple relevant lines to be quoted separately inside the same finding, while still not splitting a single defect into multiple findings just to keep one quote per line.

Diff:

```diff
- **Concurrency**: when the diff shows concurrent use of shared state, treat every read, write, and snapshot of that state as its own path. Report each unsynchronized access separately, anchored to that exact line.
+ **Concurrency**: when the diff shows concurrent use of shared state, treat each logical read, write, and snapshot path as its own finding. A check-then-act sequence (e.g., `if (TryGetValue) ... else ...`) that touches the same shared state is one path and one finding. Report each unsynchronized *path* separately, anchored to the key line(s) of that path.

- For every finding, cite the `file:line` of the defective line and quote that line verbatim from the annotated diff. For a multi-line statement, cite the first line of the offending expression (for example the line containing `await fetch(`), never a closing line such as `})` or `}`. If a defect involves several lines, cite each with its own quote, one line per quote; never list several line numbers in one citation. Before answering, re-read each citation against the annotated diff; delete any finding whose line number or quote you cannot confirm.
+ For every finding, cite the `file:line` of the defective line and quote that line verbatim from the annotated diff. For a multi-line statement, cite the first line of the offending expression (for example the line containing `await fetch(`), never a closing line such as `})` or `}`. If a defect involves several lines, quote each relevant line separately inside the same finding; every quote must contain exactly one line and correspond to one `file:line` citation. Do not split a single defect into multiple findings just to keep one quote per line. Before answering, re-read each citation against the annotated diff; delete any finding whose line number or quote you cannot confirm.
```

## Scores (0-3, AI judge)

| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-csharp-sql-injection | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 |
| 02-off-by-one | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +5.0 |
| 03-race-condition | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +11.7 |
| 04-missing-error-handling | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +0.0 |
| 06-typos | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +0.0 |


| Category | Found | Total |
|---|---|---:|
| misspelling | 1 | 1 |
| swap | 3 | 3 |
| missing_letter | 2 | 2 |


## Observations / next changes

Same six fixtures as v7-01, all judged successfully, so per-fixture and overall deltas are valid.

- **03-race-condition recovered to 100.0:** the v8 concurrency rule correctly groups the `Inc` check-then-act as a single High finding, eliminating the duplicate Medium finding from v7.
- **02-off-by-one recovered to 100.0:** `totalPages` is now correctly rated Medium, matching the calibration example.
- **06-typos remains at 95.0** with no hard fail, losing 5 points on severity calibration: the user-facing message typos (`t2_lenght`, `t3_charaters`) and public string typo (`t6_teh_text`) were reported as Medium, while the expected has them as Low.
- **01, 04, 05 remain 100.0 with no hard fails.**

**Typo recall (06):** all six typos were found; recall per category is 1/1 misspelling, 3/3 swap, 2/2 missing_letter.

**Suggested prompt changes:**
1. Add explicit typo severity guidance: user-facing text and public string literals should be Low; exported API names may be Low/Medium.
2. Require the severity of any typo finding to stay strictly below the severity of any functional defect in the same change.
3. Add one or two fresh fixtures (e.g., XSS, resource leak, auth bypass) to test whether the v8 rules generalize beyond the current six.
4. Preserve the new concurrency and evidence wording; they fixed the two largest v7 regressions.

## Per-fixture results

### [01-csharp-sql-injection](01-csharp-sql-injection.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
High-risk change: `FindByEmailAsync` builds its SQL query via string interpolation of user-supplied input, exposing the repository to SQL injection.

## Findings

- [Critical] src/CustomerRepository.cs:14 — SQL injection via interpolated email parameter
  ```
  var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";
  ```
  The `email` argument is concatenated directly into the query text, so a caller supplying input like `' OR '1'='1` (or `'; DROP TABLE Customers;--`) alters the executed SQL. This can leak arbitrary customer data or execute destructive statements. Fix by parameterizing the query:
  ```csharp
  const string sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
  await using var command = new SqlCommand(sql, connection);
  command.Parameters.Add(new SqlParameter("@email", SqlDbType.NVarChar, 256) { Value = email });
  ```

## Verdict
Request changes
</details>

### [02-off-by-one](02-off-by-one.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
New pagination helpers contain two correctness bugs: off-by-one page indexing and floor instead of ceil for page count.

## Findings

[High] src/pagination.js:7 — off-by-one on 1-based page numbers
`  const start = page * pageSize;`
The docstring says `page` is 1-based, but page 1 computes `start = pageSize`, skipping the first `pageSize` items on every call, and the last page indexes past the end. Fix: `const start = (page - 1) * pageSize;`

[Medium] src/pagination.js:16 — `totalPages` undercounts partial pages
`  return Math.floor(items.length / pageSize);`
With 10 items and pageSize 3, this returns 3 instead of 4, so the last item is unreachable. Fix: `Math.ceil(items.length / pageSize)`.

## Verdict
Request changes
</details>

### [03-race-condition](03-race-condition.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
The new `RequestStats` uses a plain `Dictionary` mutated from `Task.Run` calls in `HandleAllAsync`, creating unsynchronized read/write paths and exposing the live dictionary via `Snapshot`.

## Findings
[High] src/counter.cs:12 — Unsynchronized check-then-act increment on shared `Dictionary`
> `        if (counts.TryGetValue(path, out var count))`
`Task.Run(() => stats.Inc(p))` at line 35 invokes `Inc` concurrently; the non-atomic TryGetValue-then-set can lose increments and concurrent dictionary writes can corrupt internal state (exceptions / torn data). Fix: guard with a `lock`, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd` + `Increment`.

[Medium] src/counter.cs:20 — Unsynchronized read of `counts` while writers mutate it
> `        return counts.TryGetValue(path, out var count) ? count : 0;`
`Count` may run concurrently with `Inc` writes; `Dictionary` reads during mutation can throw or return stale/torn results. Fix: take the same lock (or use `ConcurrentDictionary`).

[Medium] src/counter.cs:25 — `Snapshot` returns the live mutable dictionary and iterates without synchronization
> `        return counts;`
Callers get direct mutable access to shared state and any enumeration races with concurrent `Inc` writes. Fix: return a copy under the lock (e.g., `new Dictionary<string,int>(counts)` inside the lock, or `ToDictionary` on a `ConcurrentDictionary`).

## Verdict
Request changes
</details>

### [04-missing-error-handling](04-missing-error-handling.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
Adds a webhook delivery helper that POSTs a payload via fetch; low risk but it silently ignores non-2xx responses.

## Findings

[Medium] src/webhook.ts:2 — HTTP error responses are not checked, so failed deliveries are reported as success
```
  await fetch(url, {
```
`fetch` only rejects on network failures; a 4xx/5xx response resolves normally, so the caller cannot detect a failed webhook delivery. Fix: capture the response and throw or return a result when `!res.ok` (e.g., `const res = await fetch(...); if (!res.ok) throw new Error(\`Webhook failed: ${res.status}\`)`).

## Verdict
Request changes
</details>

### [05-clean-refactor](05-clean-refactor.md) — 100.0
<details><summary>Full AI response</summary>

## Summary
Low-risk refactor that replaces a manual accumulation loop with `Enumerable.Sum` and algebraically equivalent tax computation (`total + total * taxRate` ≡ `subtotal * (1 + taxRate)`).

## Findings
None.

## Verdict
Approve
</details>

### [06-typos](06-typos.md) — 95.0
<details><summary>Full AI response</summary>

## Summary
Low-risk new account module containing several misspellings, including an exported function name and a user-facing error message; no functional defects.

## Findings
[Medium] src/accounts.ts:36 — Exported function name misspelled (`getAdress`)
> `export function getAdress(account: Account): string {`
The typo becomes part of the public API; consumers must call `getAdress`, and fixing later is a breaking change. Rename to `getAddress` before release.

[Medium] src/accounts.ts:23 — User-facing error message contains misspellings
> `    throw new Error("Username lenght must be at least 3 charaters.")`
"lenght" and "charaters" are misspelled in text shown to users. Fix to `"Username length must be at least 3 characters."`

[Low] src/accounts.ts:40 — Public string literal misspelled
> `export const TEXT = "teh quick brown fox"`
"teh" should be "the" in an exported constant. Fix to `"the quick brown fox"`.

[Low] src/accounts.ts — Grouped cosmetic typos in local identifiers and comment
> ` * We recieve the raw form input and normalize it.` (src/accounts.ts:16)
> `  const retires = opts.maxRetries ?? DEFAULTS.maxRetries` (src/accounts.ts:19)
> `  console.log(`Created account for ${account.username}, retrying up to ${retires} times`)` (src/accounts.ts:32)
"recieve" → "receive"; local variable "retires" → "retries" (and its use at line 32). No runtime impact.

## Verdict
Approve with nits
</details>

---
