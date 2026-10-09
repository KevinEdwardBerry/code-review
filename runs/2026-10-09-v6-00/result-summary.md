# v6 - 2026-10-09 — Detailed results

- Prompt: `prompts/code-review.v6.md`
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **95.0/100** (+19.7 vs v1-00)
- Hard fails: None

## What changed
Prompt diff (`v1` → `v6`):

```diff
--- /Users/kevinberry/src/code-review/prompts/code-review.v1.md	2026-10-09 13:18:20
+++ /Users/kevinberry/src/code-review/prompts/code-review.v6.md	2026-10-09 15:11:10
@@ -1,4 +1,43 @@
 You are a senior software engineer performing a code review of the change below.
 
+Be thorough in analysis but concise in your responses. Do not make assumptions about context you cannot see.
+
+The diff is annotated: each context or added line is prefixed with its new-file line number (`  14 | +code`). Use those numbers verbatim as `file:line` references; never count lines yourself. Removed lines have no new-file number and cannot be cited.
+
+## Review Guidelines
+
+### What to report
+- Report only defects that the diff itself demonstrates: incorrect behavior, security flaws, broken error or resource handling, races, and clear misspellings. Each finding needs a concrete impact and a specific fix.
+- Do not report hypothetical callers, missing tests, style or naming preferences, speculative performance or capacity concerns, future-growth concerns, or contract concerns the diff does not establish. If a finding depends on code or requirements you cannot see, omit it.
+- Do not invent APIs, behavior, requirements, or surrounding code.
+- If a change is a behavior-equivalent refactor, compare it against the code it replaces; if nothing observable changed and no defect is visible in the new code, report no findings. Do not describe diff churn as a defect.
+
+### What to check
+Read each changed function independently and look for the following wherever they apply:
+- **Security**: injection (string-built queries, commands, paths), missing authentication or authorization, unvalidated input, exposed sensitive data.
+- **Correctness**: boundary and off-by-one errors, wrong operators or conditions, incorrect return values.
+- **Reliability**: ignored or swallowed errors, unchecked status codes or return values, missing validation, resources that are not released on every path.
+- **Concurrency**: when the diff shows concurrent use of shared state, treat every read, write, and snapshot of that state as its own path. Report each unsynchronized access separately, anchored to that exact line.
+
+### Evidence rule
+For every finding, cite the `file:line` of the defective line and quote that line verbatim from the annotated diff. If a defect involves several lines, cite each with its own quote. Before answering, re-read each citation against the annotated diff; delete any finding whose line number or quote you cannot confirm.
+
+### Severity Levels
+Use the lowest severity that accurately reflects the demonstrated impact.
+- **Critical**: Severe security vulnerability, data loss, auth flaw, injection, or memory-safety issue.
+- **High**: Major functionality failure, broadly broken feature, or severe reliability issue.
+- **Medium**: Concrete, limited-scope functional or reliability defect, or a maintainability problem with demonstrated impact.
+- **Low**: Minor, directly evidenced issue with limited impact, including optional nits. Label nits Low.
+
+### Typos
+Flag clear misspellings in exported identifiers, user-facing text, and public string literals. Rank exported API names first, then user-facing text, public strings, then local identifiers and comments. Do not flag proper names, brand names, or valid spelling variants. Group low-impact cosmetic typos in one finding, keeping each exact reference. Typos must not outrank functional defects.
+
+## Response Format
+Use exactly these headings in this order and nothing else: `## Summary`, `## Findings`, `## Verdict`.
+
+- **Summary**: One sentence describing the change's overall risk.
+- **Findings**: Highest to lowest severity. Format each as `[Severity] path/to/file:line — title`, followed by the quoted line, concrete impact, and a specific fix. If there are no findings, write only `None.` with no extra commentary.
+- **Verdict**: `Approve`, `Approve with nits`, or `Request changes`, consistent with the findings. Do not add new concerns.
+
 ## Diff
 {{DIFF}}

```

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-csharp-sql-injection | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +21.7 (v1-00 78.3) |
| 02-off-by-one | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +11.7 (v1-00 83.3) |
| 03-race-condition | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +40.0 (v1-00 60.0) |
| 04-missing-error-handling | 1 | 3 | 3 | 3 | 3 | 3 | 3 | 80.0 | +3.3 (v1-00 76.7) |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | +8.3 (v1-00 91.7) |
| 06-typos | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | +33.3 (v1-00 61.7) |

## Typo recall
| Category | Found | Total |
|---|---|---|
| misspelling | 1 | 1 |
| swap | 3 | 3 |
| missing_letter | 2 | 2 |

## Observations / next changes
- **04 misses the two expected I/O handling issues**: the review catches the file-descriptor leak but does not flag `fetchRemoteConfig` missing `res.ok` or `loadConfig` returning unvalidated JSON. Add an explicit HTTP/validation checklist (status checks, parsed-output validation) for I/O changes.
- **Severity calibration is the only remaining point loss**: the `totalPages` floor bug was over-ranked from Medium to High on 02, the user-facing message typos were over-ranked to Medium on 06, and the cosmetic typos were not kept at nit/low. Tighten the "use the lowest severity that accurately reflects demonstrated impact" rule with concrete examples for page-counting, string typos, and local identifiers.
- **Format and reasoning are now strong**: the required `Summary / Findings / Verdict` structure held for all six fixtures, citations were mechanically correct, and the concurrency paths were reported separately.
- **Suggested prompt changes**:
  1. Add an explicit remote-fetch/JSON-validation checklist to catch missing `res.ok` and unvalidated return types.
  2. Provide severity examples for off-by-one helpers and typo impact so low/cosmetic items are not over-ranked.
  3. Keep the existing annotated-diff evidence and no-speculation rules; they cut fabricated findings to zero.


## Per-fixture results
### 01-csharp-sql-injection — 100.0
[01-csharp-sql-injection.md](01-csharp-sql-injection.md)

<details><summary>Full AI response</summary>

## Summary

The new repository interpolates user input directly into a SQL string, creating a classic injection vulnerability.

## Findings

- [Critical] src/CustomerRepository.cs:14 — SQL injection via string-interpolated query
  `var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`
  Any `email` containing a quote (e.g. `' OR '1'='1`) alters the query, allowing data exfiltration, authentication bypass on callers relying on this lookup, or arbitrary SQL execution depending on connection permissions. Fix: use a parameterized query, e.g. `var command = new SqlCommand("SELECT Id, Email FROM Customers WHERE Email = @email", connection); command.Parameters.AddWithValue("@email", email);`

## Verdict

Request changes

</details>

### 02-off-by-one — 95.0
[02-off-by-one.md](02-off-by-one.md)

<details><summary>Full AI response</summary>

## Summary
New pagination helpers contain two off-by-one/counting errors that return wrong items and undercount pages.

## Findings

[High] src/pagination.js:7 — `getPage` skips the first page for a documented 1-based page number
> `const start = page * pageSize;`
For a 1-based `page`, `getPage(items, 1, 10)` computes `start = 10`, dropping the first 10 items; page N returns items belonging to page N+1. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `totalPages` drops the final partial page
> `return Math.floor(items.length / pageSize);`
`Math.floor` undercounts when `items.length` isn't a multiple of `pageSize` (e.g., 25 items / 10 per page returns 2 instead of 3), making the last items unreachable. Fix: use `Math.ceil(items.length / pageSize)`.

## Verdict
Request changes

</details>

### 03-race-condition — 100.0
[03-race-condition.md](03-race-condition.md)

<details><summary>Full AI response</summary>

## Summary
A new request-statistics counter that performs unsynchronized concurrent access to a shared `Dictionary`, making it unsafe under the demonstrated parallel workload.

## Findings
- **[High] src/counter.cs:35 — Concurrent unsynchronized mutation of shared `Dictionary`**
  `await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));`
  `HandleAllAsync` invokes `stats.Inc` on multiple threads simultaneously, but `counts` is a plain `Dictionary<string,int>` mutated without synchronization. `Dictionary` is not thread-safe for concurrent writes; this can corrupt internal state, lose increments, or throw. Fix: use `ConcurrentDictionary<string,int>` with `AddOrUpdate`, or guard `Inc` with a `lock`.

- **[Medium] src/counter.cs:20 — Unsynchronized read of `counts` during concurrent writes**
  `return counts.TryGetValue(path, out var count) ? count : 0;`
  `Total` calls `Count`, which reads the dictionary with no synchronization; reading a `Dictionary` while another thread writes is undefined and may throw or return stale/corrupt results. Fix: same as above — `ConcurrentDictionary` or a shared lock.

- **[Medium] src/counter.cs:25 — `Snapshot` exposes the live mutable dictionary**
  `return counts;`
  Returns the internal dictionary by reference, so callers can mutate internal state and can iterate it while `Inc` writes, which can throw `InvalidOperationException`. Fix: return a copy (e.g., `new Dictionary<string,int>(counts)` under the lock) or an immutable/read-only snapshot.

## Verdict
Request changes

</details>

### 04-missing-error-handling — 80.0
[04-missing-error-handling.md](04-missing-error-handling.md)

<details><summary>Full AI response</summary>

## Summary
Adds config loading, a backup writer, and a remote config fetcher; low overall risk but the backup writer leaks its file descriptor.

## Findings

[Medium] src/config.ts:15 — File descriptor opened but never closed
> `const fd = fs.openSync(path, "w")`

`fs.writeSync(fd, data)` at src/config.ts:16 uses `fd`, but no `fs.closeSync(fd)` ever runs — neither on success nor if `writeSync` throws. Each call leaks a file descriptor, which can exhaust the process fd limit under repeated use. Fix: wrap in try/finally calling `fs.closeSync(fd)`, or use `fs.writeFileSync(path, data)` which handles this internally.

## Verdict
Request changes

</details>

### 05-clean-refactor — 100.0
[05-clean-refactor.md](05-clean-refactor.md)

<details><summary>Full AI response</summary>

## Summary
Low-risk refactor converting a manual accumulation loop into an equivalent LINQ `Sum` with an algebraically identical tax computation.

## Findings
None.

## Verdict
Approve

</details>

### 06-typos — 95.0
[06-typos.md](06-typos.md)

<details><summary>Full AI response</summary>

## Summary
Low-risk feature addition introducing account creation; primary issues are multiple spelling mistakes, including one in an exported API name and two in a user-facing error message.

## Findings
[Medium] src/accounts.ts:36 — misspelled exported function name
`export function getAdress(account: Account): string {`
`getAdress` is a public API name with a typo; consumers will import the misspelled identifier, making later correction a breaking change. Rename to `getAddress`.

[Medium] src/accounts.ts:23 — typos in user-facing error message
`throw new Error("Username lenght must be at least 3 charaters.")`
The error text shown to users contains two misspellings ("lenght", "charaters"). Change to `"Username length must be at least 3 characters."`

[Low] src/accounts.ts:40 — typo in public string literal
`export const TEXT = "teh quick brown fox"`
"teh" should be "the".

[Low] src/accounts.ts:16,19,32 — cosmetic typos in comment and local identifier
` * We recieve the raw form input and normalize it.` — "recieve" → "receive".
`  const retires = opts.maxRetries ?? DEFAULTS.maxRetries` and `console.log(`Created account for ${account.username}, retrying up to ${retires} times`)` — local variable "retires" → "retries"; the log message is also user-visible, so the misspelled name propagates into output semantics only cosmetically.

## Verdict
Approve with nits

</details>

---
