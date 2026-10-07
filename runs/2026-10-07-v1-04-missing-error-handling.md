---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 04-missing-error-handling
date: 2026-10-07
reviewer_model: subagent_explore default model
judge_model: subagent_explore default model (same as reviewer; could not set a different one)
weighted_score: 88.3
hard_fail: false
---

# 04-missing-error-handling / v1

## AI response
### Summary
Adds config loading, backup writing, and remote config fetching helpers. Several real issues: a leaked file descriptor, potential partial writes, and unchecked/unsafe return values.

### Findings

- **high src/config.ts:18 - file descriptor leak in `writeBackup`**
- Problem: `fs.openSync` returns `fd` which is never closed via `fs.closeSync`/`fs.fsync`. Under repeated calls this leaks descriptors until EMFILE. There's also no try/finally, so a throw in `writeSync` leaks it too.
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

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | All three must-find items covered (fetch res.ok check is folded into finding 3). |
| precision | 2 | writeSync short-write finding is real but not in expected; minor extra noise. |
| severity_calibration | 2 | fd leak rated high vs expected medium. |
| actionability | 3 | Concrete fixes with line refs. |
| reasoning | 3 | Correct impact. |
| format | 3 | Follows format. |
| tone | 3 | Constructive, concise. |

- Matched: fd_leak, fetch_no_status, no_validation
- Missed: none
- False positives: writeSync short-write extra finding (real but not in expected/acceptable extras)
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{"fixture":"04-missing-error-handling","scores":{"recall":3,"precision":2,"severity_calibration":2,"actionability":3,"reasoning":3,"format":3,"tone":3},"rationale":{"recall":"All three must-find items are covered: fd_leak (finding 1), fetch_no_status (res.ok check in finding 3), and no_validation (findings 3 and 4 cover unvalidated JSON and missing error context).","precision":"No fabricated or must-not-flag items. The `writeSync` short-write finding is a real defect but not in expected; acceptable extras only listed the sync-blocking nit, so it counts as minor extra noise. The low-severity error-context finding overlaps expected no_validation rather than being a false positive.","severity_calibration":"fd leak rated high vs expected medium — one level off. Other findings align with expected medium/low severities.","actionability":"Each finding gives a concrete fix (writeFileSync/try-finally, loop or writeFileSync, field validation, res.ok check, wrapped error) with file and approximate line references.","reasoning":"Explanations are correct and describe impact (EMFILE descriptor exhaustion, silent truncation, undefined fields propagating, raw ENOENT/SyntaxError without context).","reasoning_note":"","format":"Follows Summary / Findings / Verdict exactly, findings ordered by severity with consistent bullet structure.","tone":"Constructive, concise, no filler."},"matched":["fd_leak","fetch_no_status","no_validation"],"missed":[],"false_positives":["writeSync short-write extra finding (real but not in expected/acceptable extras)"],"typo_recall":null,"hard_fail":{"missed_critical":false,"fabricated":false,"missed_behavioral_typo":false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
- The judge counted the short-write finding as a false positive although it is a legitimate defect; a human override of precision to 3 may be warranted (would raise the score to 95.0).
