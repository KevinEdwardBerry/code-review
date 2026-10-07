---
prompt_version: v2
prompt_file: prompts/code-review.v2.md
fixture: 04-missing-error-handling
date: 2026-10-07
reviewer_model: subagent_explore default model
reviewer_profile: subagent_explore
judge_model: subagent_explore default model
judge_profile: subagent_explore
weighted_score: 100.0
hard_fail: false
---

# 04-missing-error-handling / v2

## Models
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model)

## AI response
### Summary
Adds config loading helpers: `loadConfig` (sync file read + JSON parse), `writeBackup` (sync file write), and `fetchRemoteConfig` (HTTP fetch). The change is small but has a real resource leak and missing error handling.

### Findings

- **[medium] src/config.ts:15-18 - `writeBackup` never closes the file descriptor**
  - Problem: `fs.openSync` returns an fd that is never released with `fs.closeSync`. Each call leaks a descriptor; under repeated calls this can exhaust the fd limit and crash the process. Also, if `fs.writeSync` throws, the fd is leaked even on the error path.
  - Fix: use `fs.writeFileSync(path, data)` (simplest), or wrap in try/finally:
    ```ts
    const fd = fs.openSync(path, "w");
    try {
      fs.writeSync(fd, data);
    } finally {
      fs.closeSync(fd);
    }
    ```
  - Code snippet:
    ```ts
    const fd = fs.openSync(path, "w");
    fs.writeSync(fd, data);
    ```

- **[medium] src/config.ts:22 - `fetchRemoteConfig` doesn't check `res.ok`**
  - Problem: `fetch` resolves on HTTP errors (404, 500). `res.json()` on an error page will either throw an opaque parse error or return a non-config body that is silently cast to `AppConfig`. A failed remote fetch produces a malformed config rather than a clear error.
  - Fix:
    ```ts
    const res = await fetch(url);
    if (!res.ok) throw new Error(`fetchRemoteConfig: HTTP ${res.status} from ${url}`);
    return res.json();
    ```
  - Code snippet:
    ```ts
    const res = await fetch(url);
    return res.json();
    ```

- **[low] src/config.ts:7-9 - `loadConfig` returns unvalidated `JSON.parse` output as `AppConfig`**
  - Problem: `cfg` is `any`; a missing or mistyped `port`/`dbUrl` in the file silently propagates as `undefined` into the typed `AppConfig`. Validation here materially improves safety since the config feeds port/DB setup.
  - Fix: validate required fields after parsing, e.g. `if (typeof cfg.port !== "number" || typeof cfg.dbUrl !== "string") throw new Error("invalid config");`
  - Code snippet:
    ```ts
    const cfg = JSON.parse(raw);
    return cfg;
    ```

### Verdict
request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | All three expected findings identified: fd leak in writeBackup, missing res.ok check in fetchRemoteConfig, and unvalidated JSON.parse in loadConfig. |
| Precision | 3 | No false positives; did not flag the AppConfig interface or invent issues. Sync fs blocking nit not raised, which is fine (acceptable extra only). |
| Severity calibration | 3 | fd leak and fetch res.ok rated medium, unvalidated parse rated low — matches expected severities exactly (medium/low for validation). |
| Actionability | 3 | Each finding includes a concrete fix with code (writeFileSync or try/finally closeSync, res.ok check with descriptive error, field validation) and correct file/line references. |
| Reasoning | 3 | Explanations are accurate: fetch resolves on HTTP errors, JSON.parse returns any silently cast, fd leaked on error path too — impact explained clearly. |
| Format | 3 | Follows Summary / Findings / Verdict structure, findings ordered by severity with labeled severities. |
| Tone | 3 | Constructive, concise, no filler. |

- Matched: fd_leak, fetch_no_status, no_validation
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{"fixture":"04-missing-error-handling","scores":{"recall":3,"precision":3,"severity_calibration":3,"actionability":3,"reasoning":3,"format":3,"tone":3},"rationale":{"recall":"All three expected findings identified: fd leak in writeBackup, missing res.ok check in fetchRemoteConfig, and unvalidated JSON.parse in loadConfig.","precision":"No false positives; did not flag the AppConfig interface or invent issues. Sync fs blocking nit not raised, which is fine (acceptable extra only).","severity_calibration":"fd leak and fetch res.ok rated medium, unvalidated parse rated low — matches expected severities exactly (medium/low for validation).","actionability":"Each finding includes a concrete fix with code (writeFileSync or try/finally closeSync, res.ok check with descriptive error, field validation) and correct file/line references.","reasoning":"Explanations are accurate: fetch resolves on HTTP errors, JSON.parse returns any silently cast, fd leaked on error path too — impact explained clearly.","format":"Follows Summary / Findings / Verdict structure, findings ordered by severity with labeled severities.","tone":"Constructive, concise, no filler."},"matched":["fd_leak","fetch_no_status","no_validation"],"missed":[],"false_positives":[],"typo_recall":null,"hard_fail":{"missed_critical":false,"fabricated":false,"missed_behavioral_typo":false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
