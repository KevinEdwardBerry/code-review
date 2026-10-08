---
prompt_version: v2
prompt_file: prompts/code-review.v2.md
fixture: 04-missing-error-handling
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 91.7
hard_fail: none
---

# 04-missing-error-handling / v2

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
Adds config loading, backup writing, and remote config fetching helpers; the main risk is a file-descriptor leak in `writeBackup` plus unvalidated/unchecked JSON in the config loaders.

## Findings

[Medium] src/config.ts:16 — `writeBackup` never closes the file descriptor
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
`fs.openSync` returns a descriptor that is never released with `fs.closeSync(fd)`. Repeated calls leak file descriptors, which can eventually exhaust the process's fd limit, and on some platforms data may not be fully flushed until close. Fix: wrap in try/finally and call `fs.closeSync(fd)`, or simply use `fs.writeFileSync(path, data)` which handles open/write/close atomically.

[Low] src/config.ts:22 — `fetchRemoteConfig` ignores HTTP error status
```ts
const res = await fetch(url)
return res.json()
```
`fetch` does not throw on 4xx/5xx, so an error response body (e.g., an HTML error page) will either fail JSON parsing with an opaque error or be returned as a bogus `AppConfig`. Fix: check `res.ok` and throw a descriptive error before parsing.

[Low] src/config.ts:9 — `loadConfig` returns unvalidated JSON as `AppConfig`
```ts
const cfg = JSON.parse(raw)
return cfg
```
`JSON.parse` returns `any`; a config file missing `port`/`dbUrl` or with wrong types silently satisfies the `AppConfig` contract, surfacing failures far from the load site. Fix: validate the parsed shape (e.g., a schema check or explicit field checks) before returning. Same concern applies to `fetchRemoteConfig` (src/config.ts:22).

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Finds all three expected defects: the descriptor leak, unchecked fetch status, and unvalidated config JSON. |
| Precision | 3 | All findings describe real defects in the diff; there are no false positives. |
| Severity calibration | 2 | The descriptor leak is rated medium and the validation issue low, both within the expected range. The fetch-status issue is rated low rather than medium. |
| Actionability | 3 | Each finding provides a concrete fix. Some cited line numbers are off, but the code snippets identify the relevant locations. |
| Reasoning | 2 | The impact explanations are mostly sound. Calling fs.writeFileSync atomic is imprecise; it handles descriptor cleanup but does not guarantee atomic writes. |
| Format | 3 | The review is clearly structured into findings and a verdict. |
| Tone | 3 | The review is concise, professional, and focused. |

- Matched: `fd_leak`, `fetch_no_status`, `no_validation`
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "04-missing-error-handling",
  "scores": {"recall": 3, "precision": 3, "severity_calibration": 2, "actionability": 3, "reasoning": 2, "format": 3, "tone": 3},
  "rationale": {
    "recall": "Finds all three expected defects: the descriptor leak, unchecked fetch status, and unvalidated config JSON.",
    "precision": "All findings describe real defects in the diff; there are no false positives.",
    "severity_calibration": "The descriptor leak is rated medium and the validation issue low, both within the expected range. The fetch-status issue is rated low rather than medium.",
    "actionability": "Each finding provides a concrete fix. Some cited line numbers are off, but the code snippets identify the relevant locations.",
    "reasoning": "The impact explanations are mostly sound. Calling fs.writeFileSync atomic is imprecise; it handles descriptor cleanup but does not guarantee atomic writes.",
    "format": "The review is clearly structured into findings and a verdict.",
    "tone": "The review is concise, professional, and focused."
  },
  "matched": ["fd_leak", "fetch_no_status", "no_validation"],
  "missed": [],
  "false_positives": [],
  "typo_recall": null,
  "hard_fail": {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
