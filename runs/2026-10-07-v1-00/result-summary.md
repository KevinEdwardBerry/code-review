# v1 - 2026-10-07-00 — Detailed results

- Prompt: `prompts/code-review.v1.md`
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model; a different judge model could not be selected via the subagent tool, so self-grading bias is possible)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **91.9/100** (baseline, no previous version)
- Hard fails: none

## What changed
Baseline.

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
| 01-sql-injection | 3 | 2 | 2 | 3 | 3 | 3 | 3 | 88.3 | new |
| 02-off-by-one | 3 | 3 | 2 | 3 | 3 | 3 | 3 | 95.0 | new |
| 03-race-condition | 3 | 3 | 3 | 2 | 3 | 3 | 3 | 95.0 | new |
| 04-missing-error-handling | 3 | 2 | 2 | 3 | 3 | 3 | 3 | 88.3 | new |
| 05-clean-refactor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 100.0 | new |
| 06-typos | 2 | 3 | 2 | 3 | 3 | 3 | 3 | 85.0 | new |

Typo recall (06-typos): misspelling 1/1, swap 2/2, missing_letter 2/3.

## Observations / next changes
- Recall is strong: every must-find issue in fixtures 01-05 was found, and the two behavior-changing typos in 06 (`maxRetires`, `lenght`) were found and ranked first. The only miss is the cosmetic `usernam` variable (missing_letter).
- Severity is the most common loss: reviewers over-rate by one level (leaked connection medium vs low, `totalPages` floor and fd leak high vs medium, `lenght` critical vs high). Suggest: define severity with concrete examples and say "reserve critical for exploitable/data-loss; a silent no-op check is high".
- Line references are sometimes off (03, 02) because the diff has no line numbers. Suggest: instruct to cite the quoted code snippet along with the line, or number the diff lines before review.
- Extras are mostly valid but add noise (cursor close, short-write, input validation). Suggest: cap low-value extras or group them under a single "Other" bullet.
- Clean diff (05) was handled well, but the nit's reasoning was muddled; suggest "only raise nits you can state precisely".
- Judge caveats: 04 precision penalised a legitimate extra finding (override to 3 would give 95.0); 06 reasoning has an internal inconsistency ("crashes" vs silent) the judge mostly forgave. Consider tightening the rubric on how to treat valid-but-unlisted findings.

## Per-fixture results
#### [01-sql-injection](sql-injection.md) - 88.3
<details><summary>AI response</summary>

### Summary
Adds `find_user_by_name` which queries SQLite for a user by name. The function is vulnerable to SQL injection and leaks the connection if the query raises.

### Findings
- **[critical] src/users.py:12 - SQL injection via string-concatenated query**
- Problem: `name` is interpolated directly into the SQL string. Input like `' OR '1'='1` (or `'; DROP TABLE users;--`) lets an attacker bypass matching, exfiltrate arbitrary rows, or execute destructive statements.
- Fix: Use a parameterized query:
  ```python
  cur.execute("SELECT id, name, email FROM users WHERE name = ?", (name,))
  ```

- **[medium] src/users.py:11-16 - Connection leaked if execute/fetchone raises**
- Problem: `conn.close()` only runs on the happy path. If `cur.execute` or `fetchone` throws, the connection (and its lock on `app.db`) is left open, which can degrade to database-lock errors under repeated failures.
- Fix: Use a context manager or try/finally:
  ```python
  conn = get_db()
  try:
      cur = conn.cursor()
      cur.execute("SELECT id, name, email FROM users WHERE name = ?", (name,))
      return cur.fetchone()
  finally:
      conn.close()
  ```
  (Or `contextlib.closing` / `with conn:`.)

- **[low] src/users.py:14-15 - Cursor not explicitly closed**
- Problem: The cursor object is dropped without `cur.close()`. Usually harmless in CPython due to refcounting, but closing the connection first means it's benign — worth tidying once the try/finally fix is applied.

### Verdict
request changes

</details>

#### [02-off-by-one](off-by-one.md) - 95.0
<details><summary>AI response</summary>

### Summary
Adds `getPage` and `totalPages` helpers for 1-based pagination. Both functions contain indexing/rounding errors that make them return wrong results in normal use.

### Findings
- **high src/pagination.js:6 — off-by-one in `getPage` for 1-based pages**
- Problem: The doc says `page` is 1-based, but `start = page * pageSize` treats it as 0-based. `getPage(items, 1, 10)` skips the first 10 items, and the last page is never reachable. Example: 20 items, pageSize 10 → page 1 returns items 10–19, page 2 returns an empty array.
- Fix: `const start = (page - 1) * pageSize;`

- **high src/pagination.js:15 — `totalPages` truncates instead of rounding up**
- Problem: `Math.floor(items.length / pageSize)` drops the final partial page. 25 items with pageSize 10 reports 2 pages, hiding the last 5 items entirely.
- Fix: `return Math.ceil(items.length / pageSize);`

- **medium src/pagination.js:5,13 — no validation of `page`/`pageSize`**
- Problem: `pageSize <= 0` makes `totalPages` return `Infinity`/`NaN` and `getPage` behave oddly (e.g. negative `start` makes `slice` count from the end of the array). `page <= 0` likewise produces slices from the end of the array rather than empty results. Whether this matters depends on callers, which aren't visible here.
- Fix: Guard inputs, e.g. `if (pageSize <= 0) throw new RangeError('pageSize must be positive')` and clamp `page` to `>= 1`.

### Verdict
request changes

</details>

#### [03-race-condition](race-condition.md) - 95.0
<details><summary>AI response</summary>

### Summary
Adds a mutex-protected per-path request counter. The write path is locked, but both read paths bypass the mutex or expose the shared map, so the type is still unsafe for concurrent use — the very thing the mutex is meant to fix.

### Findings
- **high src/counter.go:21 — `Count` reads the map without locking**
- Problem: `return s.counts[path]` runs while another goroutine may be holding the lock and writing in `Inc`. Concurrent map read/write is a data race and can panic with "concurrent map read and map write" in Go. This will fail `-race` and crash in normal use.
- Fix: acquire the lock (preferably `sync.RWMutex` with `s.mu.RLock()`/`RUnlock()`) before reading:
  ```go
  func (s *RequestStats) Count(path string) int {
      s.mu.RLock()
      defer s.mu.RUnlock()
      return s.counts[path]
  }
  ```

- **high src/counter.go:26 — `Snapshot` returns the internal map**
- Problem: Callers get a live reference to `s.counts`, so they can read/mutate it concurrently with `Inc` — same race/panic risk — and can corrupt internal state without the lock. It also silently sees later mutations.
- Fix: copy under the lock:
  ```go
  func (s *RequestStats) Snapshot() map[string]int {
      s.mu.RLock()
      defer s.mu.RUnlock()
      out := make(map[string]int, len(s.counts))
      for k, v := range s.counts {
          out[k] = v
      }
      return out
  }
  ```

- **nit src/counter.go:15-19 — unlock via `defer`**
- Manual `Lock`/`Unlock` works here but `defer s.mu.Unlock()` is more idiomatic and panic-safe if the body grows.

### Verdict
request changes

</details>

#### [04-missing-error-handling](missing-error-handling.md) - 88.3
<details><summary>AI response</summary>

### Summary
Adds config loading, backup writing, and remote config fetching helpers. Several real issues: a leaked file descriptor, potential partial writes, and unchecked/unsafe return values.

### Findings

- **high src/config.ts:18 - file descriptor leak in `writeBackup`**
- Problem: `fs.openSync` returns `fd` which is never closed via `fs.closeSync`/`fs.fsync`. Under repeated calls this leaks descriptors until EMFILE.
- Fix: use `fs.writeFileSync(path, data)` (one call, handles close), or wrap in try/finally with `fs.closeSync(fd)`.

- **medium src/config.ts:19 - `fs.writeSync` may write fewer bytes than `data`**
- Problem: `writeSync` returns bytes written and can short-write; the return value is ignored, so backups can be silently truncated.
- Fix: `fs.writeFileSync` avoids this; otherwise loop until all bytes are written and check the return value.

- **medium src/config.ts:9-11 - `loadConfig` returns unvalidated parsed JSON**
- Problem: `JSON.parse` yields `any`; returning it as `AppConfig` means a missing/non-numeric `port` or `dbUrl` silently propagates as `undefined`/wrong type. Same for `fetchRemoteConfig` returning `res.json()` (line 24) without checking `res.ok` or validating the shape.
- Fix: validate required fields (e.g. `typeof cfg.port === "number"`) and throw a descriptive error; in `fetchRemoteConfig` check `if (!res.ok) throw new Error(...)` before parsing.

- **low src/config.ts:8 - no error context on read/parse failures**
- Problem: `readFileSync`/`JSON.parse` errors bubble up raw; callers get `ENOENT`/SyntaxError without the path context.
- Fix: wrap in try/catch and rethrow `new Error(\`Failed to load config at ${path}: ...\`)`.

### Verdict
request changes

</details>

#### [05-clean-refactor](clean-refactor.md) - 100.0
<details><summary>AI response</summary>

### Summary
The change refactors `order_total` to use `sum()` with a `Decimal("0")` start and collapses the tax computation into `subtotal * (1 + tax_rate)`. The logic is mathematically equivalent to the original (subtotal plus subtotal times rate), and the `Decimal` start preserves correct typing when `items` is empty.

### Findings
- **[nit] src/totals.py:5 - int `1` mixed with Decimal `tax_rate`**
- Problem: `1 + tax_rate` works because Python promotes `int + Decimal` to `Decimal`, but if callers ever pass a non-decimal rate it silently changes behavior differently than before in edge cases — this is cosmetic/robustness only, not a real bug.
- Fix: For consistency with the codebase's explicit Decimal style, use `subtotal * (Decimal("1") + tax_rate)`.

No correctness, security, concurrency, or error-handling issues found; empty input still returns `Decimal("0")` as before.

### Verdict
approve with nits

</details>

#### [06-typos](typos.md) - 85.0
<details><summary>AI response</summary>

### Summary
Adds an account creation function with a hard crash from a misspelled property access, a silently-dead config override, and several misspelled identifiers — including one baked into the public `Account` interface.

### Findings
- **[critical] src/accounts.ts:24 - `usernam.lenght` crashes on every call**
- Problem: `lenght` is not a property of `string`; `usernam.lenght < 3` evaluates `undefined < 3`, which is always `false` — so validation silently never runs, and any account is created. (If this were a numeric property it would throw; either way it's broken.) Short usernames are accepted.
- Fix: `if (usernam.length < 3) {`
- **[high] src/accounts.ts:20 - `opts.maxRetires` silently ignores caller option**
- Problem: `maxRetires` is misspelled; `opts.maxRetires` doesn't exist on `Partial<typeof DEFAULTS>` (key is `maxRetries`). TypeScript may flag it, but if it compiles, callers' `maxRetries` values are ignored and it always falls back to 3.
- Fix: `const retries = opts.maxRetries ?? DEFAULTS.maxRetries;`
- **[medium] src/accounts.ts:6 - `adress` misspelled in public `Account` interface**
- Problem: `adress` (missing 'd') becomes part of the public type — every consumer must use the misspelled key, and it's costly to rename later. Same misspelling repeats at lines 35 (`adress: input.adress`) and 39–41 (`getAdress`, `account.adress`).
- Fix: Rename to `address` throughout: `address: string`, `address: input.address`, `getAddress(account) { return account.address; }`
- **[low] src/accounts.ts:14,27 - comment/error-message typos**
- Problem: `recieve` → `receive` in the doc comment; `charcters` → `characters` in the user-facing error string.
- Fix: "We receive the raw form input…" and "Username must be at least 3 characters long"

### Verdict
request changes

</details>

---
