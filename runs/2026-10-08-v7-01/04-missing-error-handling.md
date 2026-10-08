---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 04-missing-error-handling
date: 2026-10-08
reviewer_model: unknown concrete model
reviewer_profile: subagent_explore
judge_model: unknown concrete model
judge_profile: subagent_general
weighted_score: 83.3
hard_fail: none
---

# 04-missing-error-handling / v7

## Models
- Reviewer: subagent_explore (unknown concrete model)
- Judge: subagent_general (unknown concrete model)

## AI response
## Findings

### 1. `writeBackup()` leaks the file descriptor
**Severity: High**

`fs.openSync()` is never followed by `fs.closeSync()`. Repeated calls can exhaust the process's file-descriptor limit and prevent subsequent filesystem operations.

```ts
export function writeBackup(path: string, data: string): void {
  const fd = fs.openSync(path, "w")
  fs.writeSync(fd, data)
}
```

Prefer `fs.writeFileSync(path, data)`, which handles closing correctly, or close the descriptor in a `finally` block:

```ts
export function writeBackup(path: string, data: string): void {
  const fd = fs.openSync(path, "w")
  try {
    fs.writeSync(fd, data)
  } finally {
    fs.closeSync(fd)
  }
}
```

### 2. `loadConfig()` does not validate the parsed configuration
**Severity: High**

`JSON.parse()` returns `any`, so the function can return data that does not satisfy `AppConfig`. For example, the JSON could be valid but omit `dbUrl`, contain a string `port`, or include unexpected values. Failures may then occur far away from configuration loading.

```ts
const cfg = JSON.parse(raw)
return cfg
```

Validate the result before returning:

```ts
if (
  typeof cfg !== "object" ||
  cfg === null ||
  typeof cfg.port !== "number" ||
  !Number.isInteger(cfg.port) ||
  typeof cfg.dbUrl !== "string"
) {
  throw new Error("Invalid configuration")
}
```

Runtime validation is particularly important because the interface alone cannot guarantee that external JSON conforms to the type.

### 3. `fetchRemoteConfig()` returns an unchecked and unvalidated response body
**Severity: High**

The function does not verify that the HTTP request succeeded before parsing, and `res.json()` is implicitly treated as an `AppConfig` without validation. A 404/500 HTML response, malformed JSON, or a valid JSON object with the wrong shape can produce misleading errors or invalid configuration.

```ts
const res = await fetch(url)
return res.json()
```

It should check `res.ok`, parse the body into an `unknown`, and validate it before returning an `AppConfig`.

### 4. Inconsistent and potentially dangerous trust between local and remote configuration
**Severity: Medium**

Both functions return `AppConfig`, but neither ensures that invariant. Remote configuration deserves especially strict validation because it comes from a network source. Depending on how `dbUrl` is used, an invalid or maliciously supplied URL could redirect database connections or leaks credentials.

Validation should apply to both sources, potentially through a shared `validateConfig(value: unknown): AppConfig` helper.

### 5. `writeBackup()` may lose data or leave a partially written file on failure
**Severity: Medium**

If `writeSync()` throws, the current implementation leaves the descriptor open. Even after adding `finally`, the implementation directly truncates the target due to mode `"w"`. If the process fails partway through, the previous backup is lost.

A safer backup pattern is:

1. Write to a temporary file.
2. Flush/close it.
3. Atomically rename it over the destination.

At minimum, fix the descriptor leak; use an atomic write strategy if backup integrity matters.

### 6. Errors do not include useful context
**Severity: Low**

Filesystem errors and JSON parse errors will propagate without identifying which operation or configuration file failed. Consider wrapping errors with contextual information such as the file path, while avoiding logging sensitive file contents.

```ts
throw new Error(`Unable to load configuration from ${path}`, { cause: error })
```

## Recommended direction

Introduce a shared runtime validator and simplify the file write:

```ts
function validateConfig(value: unknown): AppConfig {
  const cfg = value as Partial<AppConfig>

  if (
    typeof cfg?.port !== "number" ||
    !Number.isInteger(cfg.port) ||
    cfg.port < 0 ||
    cfg.port > 65535 ||
    typeof cfg.dbUrl !== "string" ||
    cfg.dbUrl.length === 0
  ) {
    throw new Error("Invalid AppConfig")
  }

  return {
    port: cfg.port,
    dbUrl: cfg.dbUrl,
  }
}
```

Then:

- Use `fs.writeFileSync()` or a temp-file-plus-rename implementation for `writeBackup()`.
- Check `res.ok` in `fetchRemoteConfig()`.
- Pass both local and remote parsed values through `validateConfig()`.
- Consider making `dbUrl` a parsed/validated URL and constraining allowed URL schemes.

Overall, the API surface is simple and reasonable, but the change should not be accepted as-is because it leaks file descriptors and provides no runtime guarantee that either configuration source actually produces an `AppConfig`.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | All three seeded issues are found: the file-descriptor leak in writeBackup, the missing res.ok check in fetchRemoteConfig, and the lack of runtime validation (including missing error context) for loadConfig and the remote response. |
| Precision | 3 | No fabricated findings and the AppConfig interface is not flagged. The extra observations (data loss on a failed write, missing error context, and the trust/validation overlap) are real defects in the diff, so there are no false positives. |
| Severity calibration | 1 | All three must-find issues are marked High, while the expected severity is medium (or medium/low for no_validation), over-rating by one to two levels across multiple findings. |
| Actionability | 2 | Each finding includes a concrete fix or code snippet, but no file:line anchors are provided, making direct application slightly harder. |
| Reasoning | 3 | Explanations correctly identify root causes (unclosed descriptor, unchecked HTTP response, unvalidated JSON) and describe concrete impacts such as descriptor exhaustion, invalid configuration, and misleading errors. |
| Format | 2 | Numbered findings are ordered by severity and a concluding recommendation is present, but the required Summary and Verdict sections/headings are not explicit. |
| Tone | 3 | Constructive and focused, with no filler or rudeness, though the wording is occasionally emphatic ('dangerous', 'maliciously'). |

- Matched: fd_leak, fetch_no_status, no_validation
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
    "severity_calibration": 1,
    "actionability": 2,
    "reasoning": 3,
    "format": 2,
    "tone": 3
  },
  "rationale": {
    "recall": "All three seeded issues are found: the file-descriptor leak in writeBackup, the missing res.ok check in fetchRemoteConfig, and the lack of runtime validation (including missing error context) for loadConfig and the remote response.",
    "precision": "No fabricated findings and the AppConfig interface is not flagged. The extra observations (data loss on a failed write, missing error context, and the trust/validation overlap) are real defects in the diff, so there are no false positives.",
    "severity_calibration": "All three must-find issues are marked High, while the expected severity is medium (or medium/low for no_validation), over-rating by one to two levels across multiple findings.",
    "actionability": "Each finding includes a concrete fix or code snippet, but no file:line anchors are provided, making direct application slightly harder.",
    "reasoning": "Explanations correctly identify root causes (unclosed descriptor, unchecked HTTP response, unvalidated JSON) and describe concrete impacts such as descriptor exhaustion, invalid configuration, and misleading errors.",
    "format": "Numbered findings are ordered by severity and a concluding recommendation is present, but the required Summary and Verdict sections/headings are not explicit.",
    "tone": "Constructive and focused, with no filler or rudeness, though the wording is occasionally emphatic ('dangerous', 'maliciously')."
  },
  "matched": [
    "fd_leak",
    "fetch_no_status",
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
