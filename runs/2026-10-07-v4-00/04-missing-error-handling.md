---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 04-missing-error-handling
date: 2026-10-07
reviewer_model: default subagent model
reviewer_profile: subagent_explore
judge_model: parent model
judge_profile: subagent_general
weighted_score: 95.0
hard_fail: none
---

# 04-missing-error-handling / v4

## Models
- Reviewer: subagent_explore (default subagent model)
- Judge: subagent_general (parent model)

## AI response
### Summary
The change adds a `src/config.ts` module with config loading, a file-backup writer, and a remote config fetcher. The code has no error handling, validation, or resource cleanup, so several real defects exist.

### Findings
- **high src/config.ts:20 - `fetchRemoteConfig` never checks the HTTP response status**
  - Problem: `fetch` resolves without throwing for non-2xx responses (404, 500, etc.). The code calls `res.json()` unconditionally, so a server error page or empty body will produce a parse exception or an object that is not an `AppConfig`, propagated to callers as if it were a valid config or an unrelated parse error. Combined with the missing validation, callers can receive a wrong-shaped object on common failure paths.
  - Fix: Check `res.ok` (or `res.status`) before parsing and throw a descriptive error; validate the parsed shape before returning.
  - Code snippet:
    ```
    +  const res = await fetch(url);
    +  return res.json();
    ```

- **medium src/config.ts:15 - file descriptor in `writeBackup` is never closed**
  - Problem: `fs.openSync` returns an `fd` that is written to but never `fs.closeSync`'d. Each call leaks a file descriptor; under repeated calls this exhausts the process fd limit, and on some platforms buffered data may not be fully flushed before process exit.
  - Fix: Use `fs.writeFileSync(path, data)` instead, or wrap `writeSync` in a `try/finally` that calls `fs.closeSync(fd)`.
  - Code snippet:
    ```
    +  const fd = fs.openSync(path, "w");
    +  fs.writeSync(fd, data);
    ```

- **medium src/config.ts:10 - `JSON.parse` result returned unvalidated against `AppConfig`**
  - Problem: `JSON.parse` returns `any`, which is silently cast to `AppConfig`. A config file missing `port`/`dbUrl` or containing the wrong types (e.g. `port` as a string) will be returned as a valid `AppConfig`, deferring failure to downstream consumers where it is harder to diagnose. TypeScript's return type provides no runtime guarantee here.
  - Fix: Validate the parsed object (e.g. check `typeof cfg.port === "number"` and `typeof cfg.dbUrl === "string"`, or use a schema validator like zod) and throw a clear error on mismatch.
  - Code snippet:
    ```
    +  const cfg = JSON.parse(raw);
    +  return cfg;
    ```

- **low src/config.ts:9 - no error context when reading/parsing the config file fails**
  - Problem: If the file is missing or contains invalid JSON, `readFileSync`/`JSON.parse` throw raw errors (`ENOENT`, `SyntaxError`) with no indication that the failure came from loading config at `path`, making operational debugging harder.
  - Fix: Wrap the read/parse in try/catch and rethrow a wrapped error including `path`, e.g. `throw new Error(\`Failed to load config from ${path}: ${err.message}\`)`.
  - Code snippet:
    ```
    +  const raw = fs.readFileSync(path, "utf8");
    +  const cfg = JSON.parse(raw);
    ```

### Verdict
request changes


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Found all three must-find items: `fetchRemoteConfig` missing `res.ok` check, `writeBackup` file descriptor not closed, and `loadConfig` returning unvalidated `JSON.parse` output. It also covered the missing error context aspect of the expected `no_validation` item. |
| Precision | 3 | No fabricated or false-positive findings; every cited line exists in the diff and the lone extra (no error context for config file read/parse) is a real, acceptable observation. |
| Severity calibration | 2 | One severity is off by one level: `fetchRemoteConfig` is ranked high while the expected is medium. The other findings match expected severity (fd leak medium, validation medium). |
| Actionability | 3 | Each finding includes a concrete fix and the correct file:line references (9, 10, 15, 20) in the new file. |
| Reasoning correctness | 3 | Explanations are correct and clearly describe the impact of each defect (fd exhaustion, parsing error responses as valid config, runtime type unsafety, operational debugging difficulty). |
| Format adherence | 3 | Follows the requested Summary / Findings / Verdict structure and orders findings by severity. |
| Tone and concision | 3 | Constructive and focused; no filler or unnecessary prose. |

- Matched: fetch_no_status, fd_leak, no_validation
- Missed: none
- False positives: none
- Typo recall: n/a

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
    "recall": "Found all three must-find items: `fetchRemoteConfig` missing `res.ok` check, `writeBackup` file descriptor not closed, and `loadConfig` returning unvalidated `JSON.parse` output. It also covered the missing error context aspect of the expected `no_validation` item.",
    "precision": "No fabricated or false-positive findings; every cited line exists in the diff and the lone extra (no error context for config file read/parse) is a real, acceptable observation.",
    "severity_calibration": "One severity is off by one level: `fetchRemoteConfig` is ranked high while the expected is medium. The other findings match expected severity (fd leak medium, validation medium).",
    "actionability": "Each finding includes a concrete fix and the correct file:line references (9, 10, 15, 20) in the new file.",
    "reasoning": "Explanations are correct and clearly describe the impact of each defect (fd exhaustion, parsing error responses as valid config, runtime type unsafety, operational debugging difficulty).",
    "format": "Follows the requested Summary / Findings / Verdict structure and orders findings by severity.",
    "tone": "Constructive and focused; no filler or unnecessary prose."
  },
  "matched": [
    "fetch_no_status",
    "fd_leak",
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
