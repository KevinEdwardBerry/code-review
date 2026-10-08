---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 04-missing-error-handling
date: 2026-10-08
reviewer_model: unknown
reviewer_profile: subagent_explore
judge_model: unknown
judge_profile: subagent_general
weighted_score: 75.0
hard_fail: none
---

# 04-missing-error-handling / v7

## Models
- Reviewer: subagent_explore (unknown)
- Judge: subagent_general (unknown)

## AI response
# Code Review: `src/config.ts`

## Summary
This change adds a typed config-loading module with three functions. The overall shape is reasonable, but there are several correctness and robustness issues, most notably a **file descriptor leak** and **unchecked write completeness** in `writeBackup`.

## Findings

### 1. `writeBackup` leaks a file descriptor (High)
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
`fd` is never closed via `fs.closeSync(fd)`. Repeated calls will leak descriptors and can eventually hit `EMFILE`. If an exception is thrown by `writeSync`, the leak is guaranteed. Either:
- Use `fs.writeFileSync(path, data)` (simplest, handles open/write/close internally), or
- Wrap in `try/finally` and call `fs.closeSync(fd)`.

### 2. `writeSync` may perform a partial write (Medium)
`fs.writeSync` returns the number of bytes written; it is not guaranteed to write the full string in one call. Either check the return value and loop, or just use `fs.writeFileSync`, which handles this for you.

### 3. No runtime validation of parsed config (High)
```ts
const cfg = JSON.parse(raw)
return cfg
```
`JSON.parse` returns `any`; returning it as `AppConfig` silently accepts missing or wrongly-typed fields (e.g., `port: "8080"`, missing `dbUrl`). This defeats the purpose of the interface. Add explicit validation:
```ts
if (typeof cfg.port !== "number" || typeof cfg.dbUrl !== "string") {
  throw new Error("invalid config");
}
```
or use a schema validator (zod, ajv, etc.).

### 4. Same validation problem in `fetchRemoteConfig` (High)
`res.json()` also returns `any` (in older TS DOM libs) and is blindly returned as `AppConfig`. A malformed remote payload propagates deep into the app before failing. Validate as above.

### 5. `fetchRemoteConfig` ignores HTTP errors (Medium)
```ts
const res = await fetch(url)
return res.json()
```
A 404/500 response body will still be parsed and cast to `AppConfig`. Check `res.ok` (or `res.status`) and throw a descriptive error. Also consider a timeout (`AbortSignal.timeout(...)`) since `fetch` has no default timeout, and handle JSON parse failures with a wrapped error.

### 6. `loadConfig` swallows context on errors (Low)
`fs.readFileSync` and `JSON.parse` errors propagate raw, which is okay, but wrapping them (`throw new Error(\`failed to load config from ${path}: ...\`)`) would make debugging much easier. Consider whether a synchronous blocking read is acceptable here — fine for startup config loading, but worth noting.

### 7. No durability guarantee for the backup (Low)
If `writeBackup` is meant to produce a durable backup, consider `fs.fsyncSync(fd)` before closing (or document that durability isn’t required). `"w"` also truncates an existing backup before writing — a crash mid-write could leave a truncated backup; writing to a temp file + rename would be safer.

### 8. Style/consistency (Nit)
Inconsistent semicolons (missing after `readFileSync`, `JSON.parse`, `openSync`, `writeSync`, `fetch`, `res.json()`). If the codebase uses semicolons (as the import line suggests), keep it consistent — or let the linter/formatter enforce it.

## Recommendations
- Rewrite `writeBackup` as `fs.writeFileSync(path, data)` (fixes findings 1–2).
- Extract a `validateConfig(raw: unknown): AppConfig` used by both loaders.
- Check `res.ok` and add a timeout in `fetchRemoteConfig`.
- Wrap errors with path/URL context.


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | All three seeded issues are found: the file-descriptor leak in writeBackup, the missing res.ok check in fetchRemoteConfig, and the unvalidated/cast JSON output from loadConfig. |
| Precision | 2 | No clear false positives and the AppConfig interface is not flagged, but the review adds several unseeded extras (partial write, validation in fetchRemoteConfig, durability/fsync, semicolon style) that add noise. |
| Severity | 1 | fd_leak and no_validation are both over-severitied to High (expected medium and medium/low); only fetch_no_status severity matches. |
| Actionability | 2 | Each finding includes a concrete fix or suggestion and code snippets, but file:line references are not provided. |
| Reasoning | 3 | Explanations are technically correct and describe impact (descriptor exhaustion, unvalidated config propagation, HTTP error responses parsed as config). |
| Format | 2 | Summary / Findings / Recommendations structure is present and severity labels are used, but there is no explicit Verdict section and the findings are not strictly ordered by severity. |
| Tone | 2 | Constructive and professional, though the volume of extra findings makes the review somewhat noisy and less focused. |

- Matched: fd_leak, fetch_no_status, no_validation
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "04-missing-error-handling",
  "scores": {
    "recall": 3,
    "precision": 2,
    "severity_calibration": 1,
    "actionability": 2,
    "reasoning": 3,
    "format": 2,
    "tone": 2
  },
  "rationale": {
    "recall": "All three seeded issues are found: the file-descriptor leak in writeBackup, the missing res.ok check in fetchRemoteConfig, and the unvalidated/cast JSON output from loadConfig.",
    "precision": "No clear false positives and the AppConfig interface is not flagged, but the review adds several unseeded extras (partial write, validation in fetchRemoteConfig, durability/fsync, semicolon style) that add noise.",
    "severity_calibration": "fd_leak and no_validation are both over-severitied to High (expected medium and medium/low); only fetch_no_status severity matches.",
    "actionability": "Each finding includes a concrete fix or suggestion and code snippets, but file:line references are not provided.",
    "reasoning": "Explanations are technically correct and describe impact (descriptor exhaustion, unvalidated config propagation, HTTP error responses parsed as config).",
    "format": "Summary / Findings / Recommendations structure is present and severity labels are used, but there is no explicit Verdict section and the findings are not strictly ordered by severity.",
    "tone": "Constructive and professional, though the volume of extra findings makes the review somewhat noisy and less focused."
  },
  "matched": [
    "fd_leak",
    "fetch_no_status",
    "no_validation"
  ],
  "missed": [],
  "false_positives": [],
  "typo_recall": null,
  "hard_fail": {
    "missed_critical": false,
    "fabricated": false,
    "missed_behavioral_typo": false
  }
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
