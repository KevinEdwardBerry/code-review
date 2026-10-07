---
prompt_version: v3
prompt_file: prompts/code-review.v3.md
fixture: 04-missing-error-handling
date: 2026-10-07
reviewer_model: subagent_explore default model
reviewer_profile: subagent_explore
judge_model: subagent_explore default model
judge_profile: subagent_explore
weighted_score: 95.0
hard_fail: none
---

# 04-missing-error-handling / v3

## Models
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model)

## AI response
### Summary
Adds a small config module with file load/backup-write and remote fetch helpers. Straightforward, but `writeBackup` leaks its file descriptor and `fetchRemoteConfig` never checks the HTTP status.

### Findings

- **high src/config.ts:16-19 - `writeBackup` never closes the file descriptor**
  - Problem: `fs.openSync` returns an fd that is never passed to `fs.closeSync`. Every call leaks a descriptor; under repeated calls the process can exhaust fds and crash. It also leaves data durability/flush semantics ambiguous.
  - Fix: close in a `finally`, or just use `fs.writeFileSync(path, data)`.
  - Code snippet:
    ```ts
    const fd = fs.openSync(path, "w");
    fs.writeSync(fd, data);
    ```

- **medium src/config.ts:21-24 - `fetchRemoteConfig` ignores HTTP errors and return type mismatch**
  - Problem: `res.json()` is parsed even on 4xx/5xx (often returning an error page/body that isn't valid config), and `Response.json()` returns `Promise<any>` — fine, but without an `ok` check a failed fetch silently produces garbage config. A non-JSON error body will also throw an unhelpful parse error instead of a status error.
  - Fix:
    ```ts
    const res = await fetch(url);
    if (!res.ok) throw new Error(`fetchRemoteConfig failed: ${res.status}`);
    return res.json();
    ```

- **low src/config.ts:9-12 - `loadConfig`/`fetchRemoteConfig` trust JSON shape**
  - Problem: `cfg`/`res.json()` are returned as `AppConfig` with no validation; a config file missing `port`/`dbUrl` (or with wrong types) propagates silently and fails later in confusing ways.
  - Fix: validate required fields/types after parsing and throw a descriptive error.

- **low src/config.ts:9-12 - `loadConfig` throws raw errors**
  - Problem: `readFileSync`/`JSON.parse` throw on missing file or malformed JSON with no context about which config path failed. Not a bug, but a cheap improvement for operability.
  - Fix: wrap in try/catch and rethrow with `path` included.

### Verdict
request changes (fd leak must be fixed).

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | Found all three seeded issues: fd leak, missing res.ok check, and unvalidated/uncaught JSON parse. |
| precision | 3 | No false positives; the extra low-severity findings (raw error context, shape trust) are legitimate and the acceptable extras category covers them. AppConfig interface not flagged. |
| severity_calibration | 2 | fd_leak rated high vs expected medium (one level up, arguably defensible given crash potential); fetch_no_status medium and no_validation low match expected. One off by one level. |
| actionability | 3 | Each finding includes file:line, problem, and concrete fix (fs.writeFileSync/finally, res.ok check with code, validation suggestion). |
| reasoning | 3 | Explanations are correct: fd exhaustion, error body parsed as config, silent propagation of invalid shape, and added impact details (unhelpful parse error on non-JSON bodies). |
| format | 3 | Follows Summary/Findings/Verdict structure, findings ordered high→low. |
| tone | 3 | Constructive and concise, no filler. |

- Matched: fd_leak, fetch_no_status, no_validation
- Missed: 
- False positives: 
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "04-missing-error-handling",
  "scores": {
    "recall": 3,
    "precision": 3,
    "severity_calibration": 2,
    "actionability": 3,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Found all three seeded issues: fd leak, missing res.ok check, and unvalidated/uncaught JSON parse.",
    "precision": "No false positives; the extra low-severity findings (raw error context, shape trust) are legitimate and the acceptable extras category covers them. AppConfig interface not flagged.",
    "severity_calibration": "fd_leak rated high vs expected medium (one level up, arguably defensible given crash potential); fetch_no_status medium and no_validation low match expected. One off by one level.",
    "actionability": "Each finding includes file:line, problem, and concrete fix (fs.writeFileSync/finally, res.ok check with code, validation suggestion).",
    "reasoning": "Explanations are correct: fd exhaustion, error body parsed as config, silent propagation of invalid shape, and added impact details (unhelpful parse error on non-JSON bodies).",
    "format": "Follows Summary/Findings/Verdict structure, findings ordered high→low.",
    "tone": "Constructive and concise, no filler."
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
