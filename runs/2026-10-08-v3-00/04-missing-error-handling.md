---
prompt_version: v3
prompt_file: prompts/code-review.v3.md
fixture: 04-missing-error-handling
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 90.0
hard_fail: false
---

# 04-missing-error-handling / v3

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
Low-to-moderate risk change adding config helpers to `src/config.ts`; the main defect is an unclosed file descriptor in `writeBackup`.

## Findings

- **[Medium] src/config.ts:14 — File descriptor never closed in `writeBackup`**
  ```ts
  const fd = fs.openSync(path, "w")
  fs.writeSync(fd, data)
  ```
  `fd` is opened but never `fs.closeSync`'d. Each call leaks a file descriptor; on repeated writes (e.g., periodic backups) the process will exhaust its fd limit and start failing with `EMFILE`. Additionally, if `writeSync` throws, the fd leaks immediately. Fix: wrap in try/finally and call `fs.closeSync(fd)`, or simply use `fs.writeFileSync(path, data)` which handles open/write/close atomically.

- **[Low] src/config.ts:21 — `fetchRemoteConfig` ignores HTTP status**
  ```ts
  const res = await fetch(url)
  return res.json()
  ```
  A non-2xx response (e.g., a 404 HTML error page) is passed straight to `res.json()`, producing a confusing parse error rather than a clear failure. Fix: check `res.ok` and throw an error including `res.status` before parsing. (Also, the return value is unvalidated `any` cast to `AppConfig`, same as `loadConfig` — flagging once here as low severity since no validation contract is established in the diff.)

## Verdict
Approve with nits — the fd leak should ideally be fixed before merge, but the change is small and the impact is limited to repeated-write scenarios.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Identifies all three expected defects: the descriptor leak, missing HTTP status check, and lack of config validation. |
| Precision | 3 | No clear false-positive finding; the validation observation is relevant to loadConfig, though only mentioned parenthetically under fetchRemoteConfig. |
| Severity calibration | 2 | The fd leak is rated Medium as expected; fetch status is rated Low although expected Medium, and validation is reasonably described as low severity. |
| Actionability | 2 | Provides concrete fixes for the fd leak and HTTP status handling. The validation issue has no specific loadConfig line reference or proposed fix, and the fd-leak line citation points to the function signature rather than the leaking operations. |
| Reasoning | 3 | Correctly explains the resource leak and the consequences of parsing an error response; it also correctly identifies that parsed config is unvalidated. |
| Format | 3 | The review uses clear summary, findings, and verdict sections with severity labels and code references. |
| Tone | 3 | Focused and professional. |

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
    "severity_calibration": 2,
    "actionability": 2,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Identifies all three expected defects: the descriptor leak, missing HTTP status check, and lack of config validation.",
    "precision": "No clear false-positive finding; the validation observation is relevant to loadConfig, though only mentioned parenthetically under fetchRemoteConfig.",
    "severity_calibration": "The fd leak is rated Medium as expected; fetch status is rated Low although expected Medium, and validation is reasonably described as low severity.",
    "actionability": "Provides concrete fixes for the fd leak and HTTP status handling. The validation issue has no specific loadConfig line reference or proposed fix, and the fd-leak line citation points to the function signature rather than the leaking operations.",
    "reasoning": "Correctly explains the resource leak and the consequences of parsing an error response; it also correctly identifies that parsed config is unvalidated.",
    "format": "The review uses clear summary, findings, and verdict sections with severity labels and code references.",
    "tone": "Focused and professional."
  },
  "matched": ["fd_leak", "fetch_no_status", "no_validation"],
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
