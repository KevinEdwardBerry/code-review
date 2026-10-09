---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 04-missing-error-handling
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 80.0
hard_fail: none
---

# 04-missing-error-handling / v4

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
Adds config loading, backup writing, and remote config fetching helpers; the backup writer leaks its file descriptor, which is a concrete reliability defect.

## Findings

**[Medium] src/config.ts:15 — file descriptor never closed in `writeBackup`**

```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```

`fs.openSync` returns a descriptor that must be released with `fs.closeSync(fd)`. As written, every call to `writeBackup` leaks a descriptor; repeated calls can exhaust the process's file-descriptor limit, and on an exception from `writeSync` the descriptor is leaked unconditionally. Fix: either use `fs.writeFileSync(path, data)` (the simple fix), or wrap in `try/finally` with `fs.closeSync(fd)`.

**[Low] src/config.ts:16 — `writeSync` result ignored**

```ts
fs.writeSync(fd, data)
```

`fs.writeSync` returns the number of bytes actually written and is not guaranteed to write the entire buffer in one call. If a partial write occurs, the backup is silently truncated. Fix: if keeping the raw-sync approach, loop until all bytes are written; simplest is switching to `fs.writeFileSync`, which also resolves the leak above.

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 1 | Identifies the expected file-descriptor leak, but misses fetch_no_status and no_validation. |
| Precision | 3 | The descriptor-leak finding is supported by the diff. The additional partial-write concern is plausible for fs.writeSync and cites a line present in the diff; no fabricated findings or references. |
| Severity calibration | 3 | The expected descriptor leak is rated Medium, and the additional partial-write concern is rated Low, both reasonably calibrated. |
| Actionability | 3 | Provides concrete remedies for both findings, including writeFileSync and try/finally for the leak. |
| Reasoning correctness | 3 | Explains the descriptor lifecycle and the potential consequences of a partial write. |
| Format adherence | 3 | Uses a clear summary, individually labeled findings, code excerpts, and a verdict. |
| Tone and concision | 3 | Professional and direct. |

- Matched: fd_leak
- Missed: fetch_no_status, no_validation
- False positives: none
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{"fixture":"04-missing-error-handling","scores":{"recall":1,"precision":3,"severity_calibration":3,"actionability":3,"reasoning":3,"format":3,"tone":3},"rationale":{"recall":"Identifies the expected file-descriptor leak, but misses fetch_no_status and no_validation.","precision":"The descriptor-leak finding is supported by the diff. The additional partial-write concern is plausible for fs.writeSync and cites a line present in the diff; no fabricated findings or references.","severity_calibration":"The expected descriptor leak is rated Medium, and the additional partial-write concern is rated Low, both reasonably calibrated.","actionability":"Provides concrete remedies for both findings, including writeFileSync and try/finally for the leak.","reasoning":"Explains the descriptor lifecycle and the potential consequences of a partial write.","format":"Uses a clear summary, individually labeled findings, code excerpts, and a verdict.","tone":"Professional and direct."},"matched":["fd_leak"],"missed":["fetch_no_status","no_validation"],"false_positives":[],"typo_recall":null,"hard_fail":{"missed_critical":false,"fabricated":false,"missed_behavioral_typo":false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
