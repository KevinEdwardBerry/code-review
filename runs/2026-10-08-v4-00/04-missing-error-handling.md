---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 04-missing-error-handling
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: N/A (judge failed)
hard_fail: unscored (judge failed)
---

# 04-missing-error-handling / v4

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed; failed after one retry)

## AI response
## Summary
Adds config loading helpers with a file-descriptor leak in `writeBackup` and missing error/response handling in `fetchRemoteConfig`; overall moderate risk.

## Findings

- **[Medium] src/config.ts:15 — `openSync` file descriptor is never closed**
  ```ts
  const fd = fs.openSync(path, "w")
  fs.writeSync(fd, data)
  ```
  `writeBackup` opens `fd` but never calls `fs.closeSync(fd)`. Each call leaks a descriptor; repeated calls (or a `writeSync` throw) accumulate leaked handles and can exhaust the process fd limit. Fix: wrap in try/finally with `fs.closeSync(fd)`, or use `fs.writeFileSync(path, data)`.

- **[Medium] src/config.ts:21 — HTTP error responses are silently parsed as config**
  ```ts
  const res = await fetch(url)
  return res.json()
  ```
  `fetch` resolves on non-2xx responses, so a 404/500 HTML or error body is passed to `res.json()` — producing either an opaque `SyntaxError` or an `AppConfig`-typed object that isn't a valid config. Fix: check `res.ok` and throw a descriptive error (including `res.status`) before parsing.

- **[Low] src/config.ts:7 — parsed JSON returned without validation against `AppConfig`**
  ```ts
  const cfg = JSON.parse(raw)
  return cfg
  ```
  Any well-formed JSON (e.g. a string, array, or missing `port`/`dbUrl`) is returned typed as `AppConfig`, pushing malformed-config failures to distant consumers. Fix: validate `cfg.port`/`cfg.dbUrl` types (or use a schema) and throw on mismatch. (Same applies to `fetchRemoteConfig`, which shares the unchecked-cast pattern.)

## Verdict
Request changes

## Judge status
Judge failed after the initial judgment and one retry because neither response satisfied the requested schema. No score, matched/missed lists, or hard-fail determination is assigned.

### Initial judge output (invalid schema)
```json
{"fixture":"config_review","scores":{"recall":3,"precision":2,"severity_calibration":3,"actionability":3,"reasoning":2,"format":3,"tone":3},"rationales":{"recall":"Identifies all three expected findings and gives actionable fixes. However, the validation finding cites src/config.ts:7, which is a blank line; JSON.parse is on line 10. This is an inaccurate citation and triggers hard_fail.","precision":"All three findings are supported by the diff. The review does not flag acceptable synchronous filesystem usage or AppConfig itself.","severity_calibration":"The descriptor leak and missing response status check are rated Medium; unvalidated configuration is rated Low, within the expected range.","actionability":"Each finding includes a practical remediation.","reasoning":"The validation finding's line anchor is incorrect.","format":"Organized findings.","tone":"Professional."},"matched":["fd_leak","fetch_no_status","no_validation"],"missed":[],"false_positives":[],"typo_recall":null,"hard_fail":{"fabricated":false,"critical_omission":false,"invalid_schema":false}}
```

### Retry output (invalid schema)
```json
{"fixture":"04-missing-error-handling","scores":{"recall":3,"precision":3,"severity_calibration":3,"actionability":3,"reasoning":3,"format":3,"tone":3},"rationales":{"recall":"The review covers all three expected findings.","precision":"All three findings are supported.","severity_calibration":"Ratings match expected severities.","actionability":"Each finding includes a practical remediation.","reasoning":"Explanations accurately describe failure modes; the validation line anchor is incorrect but is not fabricated code, line, or API.","format":"Summary, findings, verdict.","tone":"Professional."},"matched":["fd_leak","fetch_no_status","no_validation"],"missed":[],"false_positives":[],"typo_recall":null,"hard_fail":{"fabricated":false,"critical_omission":false,"invalid_schema":false}}
```

- Matched: not scored
- Missed: not scored
- False positives: not scored
- Typo recall: N/A

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
The review cites line 7 for `JSON.parse`, while that expression is on new-file line 10. Prior v3 score: 90.0; current delta unavailable.
