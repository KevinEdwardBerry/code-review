---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 04-missing-error-handling
date: 2026-10-07
reviewer_model: subagent_explore default model
judge_model: subagent_explore default model
weighted_score: 95.0
hard_fail: false
---

# 04-missing-error-handling / v1

## AI response

### Summary
Adds a small config module with file load/backup helpers and a remote fetch. The change is simple but has a real resource leak and a couple of robustness gaps worth fixing.

### Findings

- **high src/config.ts:16-19 — `writeBackup` never closes the file descriptor**
  - Problem: `fs.openSync` returns a fd that is never passed to `fs.closeSync`. Repeated calls leak descriptors until the process hits `EMFILE` and crashes. Also, a single `fs.writeSync` is not guaranteed to write all bytes for large `data`.
  - Fix: use `fs.writeFileSync(path, data)` (handles open/write-all/close), or wrap in try/finally:
    ```ts
    const fd = fs.openSync(path, "w");
    try {
      fs.writeSync(fd, data);
    } finally {
      fs.closeSync(fd);
    }
    ```

- **medium src/config.ts:21-24 — `fetchRemoteConfig` ignores HTTP errors and returns unvalidated data**
  - Problem: `res.json()` is returned without checking `res.ok`, so a 404/500 error body is silently treated as an `AppConfig`. The parsed JSON is also unchecked, so callers get an object that may lack `port`/`dbUrl` (typed as `AppConfig` via `any`).
  - Fix: check `res.ok` and throw a descriptive error otherwise; optionally validate/coerce fields before returning, e.g.:
    ```ts
    if (!res.ok) throw new Error(`fetchRemoteConfig failed: ${res.status} ${res.statusText}`);
    const cfg = await res.json();
    if (typeof cfg?.port !== "number" || typeof cfg?.dbUrl !== "string")
      throw new Error("invalid remote config");
    return cfg;
    ```

- **medium src/config.ts:9-13 — `loadConfig` returns unvalidated JSON**
  - Problem: same issue as above for the local file — `JSON.parse` result is returned unchecked as `AppConfig`, so a malformed config produces confusing failures downstream instead of a clear error at load time.
  - Fix: validate `cfg.port`/`cfg.dbUrl` types (as above) and throw on mismatch; optionally wrap `readFileSync`/`JSON.parse` in try/catch to include `path` in the error message.

- **nit src/config.ts:22-23 — `res.json()` is `Promise<any>` silently matching `AppConfig`**
  - Problem: fine today, but hides the type gap. Covered by the validation fix above; otherwise annotate `const cfg = (await res.json()) as AppConfig` to make the unchecked cast explicit.

### Verdict
request changes — the fd leak in `writeBackup` is a genuine bug, and the unchecked `AppConfig` returns will produce misleading failures in common error paths.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | All three expected issues found: fd leak in writeBackup, missing res.ok check in fetchRemoteConfig, and unvalidated JSON.parse in loadConfig (plus remote validation). |
| Precision | 3 | No false positives. The extra nit about res.json() returning Promise<any> and the writeSync partial-write note are legitimate observations, not noise. |
| Severity calibration | 2 | fd leak rated high vs expected medium (one level off, defensible given EMFILE crash impact); others correctly medium/nit. |
| Actionability | 3 | Concrete fixes with code snippets for each finding; line ranges slightly off from actual new-file positions (writeBackup body is ~lines 15-18, cited 16-19) but code references are accurate. |
| Reasoning | 3 | Correctly explains impact: descriptor leak leading to EMFILE, error bodies parsed as config, downstream failures from unvalidated JSON. |
| Format | 3 | Follows Summary / Findings / Verdict with findings ordered by severity. |
| Tone | 3 | Constructive and concise, no filler. |

- Matched: fd_leak, fetch_no_status, no_validation
- Missed: none
- False positives: none
- Typo recall: null

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
    "recall": "All three expected issues found: fd leak in writeBackup, missing res.ok check in fetchRemoteConfig, and unvalidated JSON.parse in loadConfig (plus remote validation).",
    "precision": "No false positives. The extra nit about res.json() returning Promise<any> and the writeSync partial-write note are legitimate observations, not noise.",
    "severity_calibration": "fd leak rated high vs expected medium (one level off, defensible given EMFILE crash impact); others correctly medium/nit.",
    "actionability": "Concrete fixes with code snippets for each finding; line ranges slightly off from actual new-file positions (writeBackup body is ~lines 15-18, cited 16-19) but code references are accurate.",
    "reasoning": "Correctly explains impact: descriptor leak leading to EMFILE, error bodies parsed as config, downstream failures from unvalidated JSON.",
    "format": "Follows Summary / Findings / Verdict with findings ordered by severity.",
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
