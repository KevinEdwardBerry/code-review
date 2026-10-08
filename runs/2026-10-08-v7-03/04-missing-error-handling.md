---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 04-missing-error-handling
date: 2026-10-08
reviewer_model: unknown (concrete model not exposed)
reviewer_profile: subagent_explore
judge_model: unknown (concrete model not exposed)
judge_profile: subagent_general
weighted_score: 75.0
hard_fail: none
---

# 04-missing-error-handling / v7

## Models
- Reviewer: subagent_explore (unknown concrete model)
- Judge: subagent_general (unknown concrete model)

## AI response
## Code Review

### Issues Found

**1. `writeBackup` leaks the file descriptor (bug — should fix)**
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
`fs.closeSync(fd)` is never called, so the fd stays open until GC/process exit. On repeated calls this can exhaust file descriptors (`EMFILE`). Either close it in a `try/finally`, or simply use `fs.writeFileSync(path, data)` which handles open/write/close atomically.

**2. `loadConfig` returns unvalidated data (type-safety concern)**
```ts
const cfg = JSON.parse(raw)
return cfg
```
`JSON.parse` returns `any`; nothing guarantees `port` is a number or `dbUrl` exists. A malformed config silently propagates until it fails elsewhere. Consider runtime validation (e.g., zod, or manual checks with a thrown error). Same applies to `fetchRemoteConfig`, which returns `res.json()` (a `Promise<any>`) cast to `AppConfig`.

**3. `fetchRemoteConfig` lacks error handling (reliability concern)**
- No check of `res.ok` — a 404/500 response will still be parsed and returned as if it were a valid config.
- No timeout — `fetch` can hang indefinitely.
- No handling of non-JSON error bodies (`res.json()` will throw a less-informative error).

**4. No error handling around file/JSON operations in `loadConfig`**
`fs.readFileSync` throws a raw `ENOENT` for missing files and `JSON.parse` throws a bare `SyntaxError` with byte-offset info. Wrapping these in a descriptive error (including `path`) would help debugging, though this is minor.

**5. Style/consistency nits**
- Mixed semicolon usage: interface fields use `;`, function bodies don't.
- `loadConfig`/`writeBackup` are synchronous while `fetchRemoteConfig` is async — fine, but synchronous I/O in `loadConfig` blocks the event loop if called at runtime rather than startup.

### Recommendations
- Replace `writeBackup` body with `fs.writeFileSync(path, data)` (or close `fd` in `finally`).
- Add a validation step producing `AppConfig` or throwing, shared by `loadConfig` and `fetchRemoteConfig`.
- In `fetchRemoteConfig`, check `res.ok`, add `AbortSignal.timeout(...)`, and surface HTTP errors clearly.

### Verdict
The fd leak in `writeBackup` is the one definite bug; the rest are robustness/typing improvements. I'd request changes on the leak and validation before approval.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Finds fd leak, missing HTTP status check, and missing config validation. |
| Precision | 2 | Core findings are correct; timeout, response-body and style notes add noise. |
| Severity calibration | 2 | Overall severity framing broadly matches medium / medium-low expectations. |
| Actionability | 2 | Provides concrete fixes but no exact file:line citations. |
| Reasoning | 2 | Explains impact correctly, with some unsupported extra concerns. |
| Format | 0 | Does not use the required Summary/Findings/Verdict structure. |
| Tone | 3 | Focused and constructive. |

- Matched: `fd_leak`, `fetch_no_status`, `no_validation`
- Missed: none
- False positives: descriptor-GC claim; unseeded timeout, non-JSON-body and semicolon-consistency recommendations.
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{"fixture":"04-missing-error-handling","scores":{"recall":3,"precision":2,"severity_calibration":2,"actionability":2,"reasoning":2,"format":0,"tone":3},"rationale":{"recall":"Finds all three expected issues: the unclosed descriptor, missing res.ok check, and lack of runtime validation for parsed config data.","precision":"The core findings are supported by the diff. The semicolon-style nit and additional timeout/non-JSON-body recommendations are unnecessary noise; the claim that the descriptor stays open only until garbage collection is inaccurate.","severity_calibration":"The review treats the descriptor leak as a bug requiring a fix and frames the other issues as reliability or typing concerns, broadly matching the expected medium and medium/low severities.","actionability":"Suggests concrete fixes, including try/finally or writeFileSync, checking res.ok, and validating config data, but provides no file-and-line references.","reasoning":"Explains the practical impact of the descriptor leak and why unchecked HTTP errors and unvalidated fields can lead to invalid configuration. Some added concerns are not part of the expected findings.","format":"Does not use the required exact Summary/Findings/Verdict structure: it uses Code Review and Issues Found instead.","tone":"Focused and constructive, with no rude or distracting language."},"matched":["fd_leak","fetch_no_status","no_validation"],"missed":[],"false_positives":["The descriptor is said to remain open only until garbage collection; the diff provides no mechanism that would close the OS file descriptor during GC.","Unseeded timeout, non-JSON error-body, and semicolon-consistency recommendations add noise beyond the expected findings."],"typo_recall":null,"hard_fail":{"missed_critical":false,"fabricated":false,"missed_behavioral_typo":false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
