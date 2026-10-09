---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 04-missing-error-handling
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 90.0
hard_fail: false
---

# 04-missing-error-handling / v4

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
Adds config loading, file backup writing, and remote config fetch helpers; main risks are a leaked file descriptor and unchecked HTTP response status.

## Findings

[Medium] src/config.ts:16 — file descriptor never closed in `writeBackup`
```ts
fs.writeSync(fd, data)
```
`fs.openSync` returns an fd that is never passed to `fs.closeSync`, leaking a descriptor on every call (including on `writeSync` throw). Fix: wrap in try/finally with `fs.closeSync(fd)`, or simply use `fs.writeFileSync(path, data)`.

[Medium] src/config.ts:21 — `fetchRemoteConfig` ignores HTTP error status
```ts
return res.json()
```
On non-2xx responses (e.g. 404/500 returning an HTML error page or unrelated JSON), this either throws a confusing parse error or silently returns data that isn't an `AppConfig`. Fix: check `if (!res.ok) throw new Error(...)` before parsing.

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 2 | Found the descriptor leak and missing HTTP status check, but missed unvalidated JSON configuration and contextual error handling in loadConfig. |
| Precision | 3 | Both findings match real defects in the diff; no false positives. |
| Severity calibration | 3 | Both findings are appropriately rated Medium. |
| Actionability | 3 | Each finding cites its relevant location and gives a concrete fix. |
| Reasoning | 3 | Accurately explains descriptor leakage and the risks of parsing unsuccessful HTTP responses. |
| Format | 3 | Clear, ordered Summary, Findings, and Verdict sections. |
| Tone | 3 | Focused and constructive. |

- Matched: `fd_leak`, `fetch_no_status`
- Missed: `no_validation`
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{"fixture":"04-missing-error-handling","scores":{"recall":2,"precision":3,"severity_calibration":3,"actionability":3,"reasoning":3,"format":3,"tone":3},"rationale":{"recall":"Found the descriptor leak and missing HTTP status check, but missed the unvalidated JSON configuration and lack of contextual error handling in loadConfig.","precision":"Both findings match real defects in the diff; no false positives.","severity_calibration":"Both findings are appropriately rated medium.","actionability":"Each finding cites the relevant location and gives a concrete, correct fix.","reasoning":"Explains the descriptor leak and the risks of parsing unsuccessful HTTP responses accurately.","format":"Uses clear, ordered Summary, Findings, and Verdict sections with consistently formatted findings.","tone":"Focused and constructive."},"matched":["fd_leak","fetch_no_status"],"missed":["no_validation"],"false_positives":[],"typo_recall":null,"hard_fail":{"missed_critical":false,"fabricated":false,"missed_behavioral_typo":false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
