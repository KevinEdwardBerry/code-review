---
prompt_version: v5
prompt_file: prompts/code-review.v5.md
fixture: 04-missing-error-handling
date: 2026-10-07
reviewer_model: subagent_explore (default subagent model)
reviewer_profile: subagent_explore
judge_model: subagent_general (parent model)
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: false
---

# 04-missing-error-handling / v5

## Models
- Reviewer: subagent_explore (subagent_explore (default subagent model))
- Judge: subagent_general (subagent_general (parent model))

## AI response

### Summary
The change adds a new `src/config.ts` module with an `AppConfig` interface and three helpers: `loadConfig` (sync file read + JSON parse), `writeBackup` (sync file write), and `fetchRemoteConfig` (fetch + JSON parse). The logic is mostly straightforward, but `writeBackup` leaks its file descriptor and `fetchRemoteConfig` doesn't check the response status before parsing.

### Findings
- **[medium] src/config.ts:15-16 - File descriptor never closed in `writeBackup`**
  - Problem: `fs.openSync` returns a descriptor that is written to but never closed. Repeated calls (e.g., periodic backups) will leak descriptors and can eventually exhaust the process's file-descriptor limit; on some platforms writes may also not be fully flushed before the descriptor is GC'd. There is no `try/finally`, so even the write path doesn't guarantee cleanup.
  - Fix: Wrap in `try/finally` with `fs.closeSync(fd)`, or simply use `fs.writeFileSync(path, data)` which handles open/write/close atomically.
  - Code snippet:
    ```ts
    const fd = fs.openSync(path, "w");
    fs.writeSync(fd, data);
    ```

- **[medium] src/config.ts:20-21 - `fetchRemoteConfig` ignores HTTP error status**
  - Problem: `fetch` does not reject on non-2xx responses, so a 404/500 HTML error page will be passed to `res.json()`, producing either a confusing `SyntaxError` or silently wrong parsed data returned as `AppConfig`. Callers can't distinguish "server returned an error" from "server returned config".
  - Fix: Check `res.ok` (or `res.status`) before parsing and throw a descriptive error including the status and URL.
  - Code snippet:
    ```ts
    const res = await fetch(url);
    return res.json();
    ```

- **[low] src/config.ts:10-11 - `loadConfig` returns unvalidated `JSON.parse` result**
  - Problem: `JSON.parse` returns `any`; a well-formed JSON file missing `port`/`dbUrl` or with wrong types (e.g. `port: "abc"`) is returned as a valid `AppConfig`, so misconfiguration surfaces later as confusing failures rather than at load time.
  - Fix: Validate the parsed object (e.g., check `typeof cfg.port === "number"` and `typeof cfg.dbUrl === "string"`, or use a schema validator) and throw a descriptive error on mismatch.
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
| Recall | 3 | Finds all three seeded issues: fd leak in writeBackup, missing res.ok check in fetchRemoteConfig, and unvalidated JSON in loadConfig. |
| Precision | 3 | No false positives; it did not flag AppConfig or invent unrelated issues. |
| Severity calibration | 3 | Matches expected severities: fd leak and fetch status as medium, validation as low (expected medium/low). |
| Actionability | 3 | Each finding includes a concrete fix, correct file:line references, and relevant code snippets. |
| Reasoning | 3 | Explanations correctly describe the defect and its runtime impact (descriptor exhaustion, confusing parse errors, misconfiguration). |
| Format | 3 | Follows Summary / Findings / Verdict, ordered by severity with consistent [medium]/[low] labels. |
| Tone | 3 | Constructive and concise, no filler or rude language. |

- Matched: [fd_leak, fetch_no_status, no_validation]
- Missed: []
- False positives: []
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "04-missing-error-handling",
  "scores": {
    "recall": 3,
    "precision": 3,
    "severity_calibration": 3,
    "actionability": 3,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Finds all three seeded issues: fd leak in writeBackup, missing res.ok check in fetchRemoteConfig, and unvalidated JSON in loadConfig.",
    "precision": "No false positives; it did not flag AppConfig or invent unrelated issues.",
    "severity_calibration": "Matches expected severities: fd leak and fetch status as medium, validation as low (expected medium/low).",
    "actionability": "Each finding includes a concrete fix, correct file:line references, and relevant code snippets.",
    "reasoning": "Explanations correctly describe the defect and its runtime impact (descriptor exhaustion, confusing parse errors, misconfiguration).",
    "format": "Follows Summary / Findings / Verdict, ordered by severity with consistent [medium]/[low] labels.",
    "tone": "Constructive and concise, no filler or rude language."
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
