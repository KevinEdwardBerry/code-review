---
prompt_version: v6
prompt_file: prompts/code-review.v6.md
fixture: 04-missing-error-handling
date: 2026-10-07
reviewer_model: unknown
reviewer_profile: subagent_explore
judge_model: unknown
judge_profile: subagent_general
weighted_score: 96.7
hard_fail: none
---

# 04-missing-error-handling / v6

## Models
- Reviewer: subagent_explore (unknown)
- Judge: subagent_general (unknown)

## AI response
### Summary
Adds a config module with `loadConfig`, `writeBackup`, and `fetchRemoteConfig`. The change is small but leaves a file-descriptor leak and lacks response validation on the remote fetch path.

### Findings
- **[medium] src/config.ts:15-16 - `writeBackup` never closes the file descriptor**
  - Problem: `fs.openSync` returns an fd that is written to but never closed. Repeated calls leak descriptors until process limits are hit; also, without a `try/finally`, a `writeSync` throw leaks the fd immediately.
  - Fix: wrap in `try { fs.writeSync(fd, data); } finally { fs.closeSync(fd); }`, or simpler, use `fs.writeFileSync(path, data)`.
  - Code snippet:
    ```ts
    const fd = fs.openSync(path, "w");
    fs.writeSync(fd, data);
    ```
- **[medium] src/config.ts:21-22 - `fetchRemoteConfig` ignores HTTP status**
  - Problem: `res.json()` is returned regardless of `res.ok`; a 404/500 body is parsed and returned as `AppConfig`, or `res.json()` rejects with an opaque parse error. Also, no timeout means the promise can hang indefinitely.
  - Fix: check `if (!res.ok) throw new Error(...)` before parsing, and consider an `AbortSignal`/timeout.
  - Code snippet:
    ```ts
    const res = await fetch(url);
    return res.json();
    ```
- **[low] src/config.ts:11 - `loadConfig` returns unvalidated JSON as `AppConfig`**
  - Problem: `JSON.parse` result is returned unchecked; a config missing `port`/`dbUrl` silently produces a malformed `AppConfig` and `undefined` downstream rather than failing at load time.
  - Fix: validate required fields/types after parsing and throw a descriptive error.
  - Code snippet:
    ```ts
    const cfg = JSON.parse(raw);
    return cfg;
    ```

### Verdict
`request changes`


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Review found all three seeded issues: fd_leak, fetch_no_status, and no_validation. |
| Precision | 3 | All findings correspond to real defects in the diff; no must-not-flag items were flagged. |
| Severity Calibration | 3 | Severities match expected: writeBackup and fetchRemoteConfig are medium, and loadConfig validation is low (expected medium/low). |
| Actionability | 3 | Each finding provides a concrete fix and correct file:line references. |
| Reasoning | 2 | Explanations for fd and fetch are correct and include impact; the loadConfig finding is correct but only addresses field validation, not file/malformed-JSON error context. |
| Format | 3 | Follows Summary / Findings / Verdict with findings ordered by severity. |
| Tone | 3 | Constructive and concise with no filler. |

- Matched: fd_leak, fetch_no_status, no_validation
- Missed: none
- False positives: none
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "04-missing-error-handling",
  "scores": {
    "recall": 3,
    "precision": 3,
    "severity_calibration": 3,
    "actionability": 3,
    "reasoning": 2,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Review found all three seeded issues: fd_leak, fetch_no_status, and no_validation.",
    "precision": "All findings correspond to real defects in the diff; no must-not-flag items were flagged.",
    "severity_calibration": "Severities match expected: writeBackup and fetchRemoteConfig are medium, and loadConfig validation is low (expected medium/low).",
    "actionability": "Each finding provides a concrete fix and correct file:line references.",
    "reasoning": "Explanations for fd and fetch are correct and include impact; the loadConfig finding is correct but only addresses field validation, not file/malformed-JSON error context.",
    "format": "Follows Summary / Findings / Verdict with findings ordered by severity.",
    "tone": "Constructive and concise with no filler."
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
