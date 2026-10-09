---
prompt_version: v6
prompt_file: prompts/code-review.v6.md
fixture: 04-missing-error-handling
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 80.0
hard_fail: {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}
---

# 04-missing-error-handling / v6

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
Adds config loading, a backup writer, and a remote config fetcher; low overall risk but the backup writer leaks its file descriptor.

## Findings

[Medium] src/config.ts:15 — File descriptor opened but never closed
> `const fd = fs.openSync(path, "w")`

`fs.writeSync(fd, data)` at src/config.ts:16 uses `fd`, but no `fs.closeSync(fd)` ever runs — neither on success nor if `writeSync` throws. Each call leaks a file descriptor, which can exhaust the process fd limit under repeated use. Fix: wrap in try/finally calling `fs.closeSync(fd)`, or use `fs.writeFileSync(path, data)` which handles this internally.

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 1 | Found the file descriptor leak (fd_leak) but missed fetch_no_status and no_validation. |
| precision | 3 | No false positives or hallucinated citations; the only reported finding is real. |
| severity_calibration | 3 | The fd_leak finding is correctly labeled medium, matching the expected severity. |
| actionability | 3 | Provides a concrete fix and the correct file:line citation. |
| reasoning | 3 | Explanation is correct and describes the runtime impact of the leak. |
| format | 3 | Follows Summary / Findings / Verdict and is ordered by severity. |
| tone | 3 | Constructive, concise, and free of filler. |

- Matched: fd_leak
- Missed: fetch_no_status, no_validation
- False positives: None
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "04-missing-error-handling",
  "scores": {
    "recall": 1,
    "precision": 3,
    "severity_calibration": 3,
    "actionability": 3,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Found the file descriptor leak (fd_leak) but missed fetch_no_status and no_validation.",
    "precision": "No false positives or hallucinated citations; the only reported finding is real.",
    "severity_calibration": "The fd_leak finding is correctly labeled medium, matching the expected severity.",
    "actionability": "Provides a concrete fix and the correct file:line citation.",
    "reasoning": "Explanation is correct and describes the runtime impact of the leak.",
    "format": "Follows Summary / Findings / Verdict and is ordered by severity.",
    "tone": "Constructive, concise, and free of filler."
  },
  "matched": [
    "fd_leak"
  ],
  "missed": [
    "fetch_no_status",
    "no_validation"
  ],
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
