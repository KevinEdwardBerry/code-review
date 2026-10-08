---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 04-missing-error-handling
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 66.7
hard_fail: false
---

# 04-missing-error-handling / v1

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Code Review

**Blocking issues**

1. **`writeBackup` leaks the file descriptor** — `fs.openSync` returns an fd that's never closed. If the write throws, or under repeated calls, this will exhaust file descriptors. Either wrap in try/finally with `fs.closeSync(fd)`, or simply use `fs.writeFileSync(path, data)`.

```ts
export function writeBackup(path: string, data: string): void {
  fs.writeFileSync(path, data)
}
```

2. **`loadConfig` returns unvalidated data typed as `AppConfig`** — `JSON.parse` returns `any`; the `AppConfig` return type is a lie. A config file missing `port` or with `port: "abc"` passes silently and fails downstream. Validate (e.g., zod, or manual checks) before returning:

```ts
const cfg = JSON.parse(raw) as unknown
if (typeof cfg !== "object" || cfg === null || typeof (cfg as any).port !== "number" || typeof (cfg as any).dbUrl !== "string") {
  throw new Error(`Invalid config at ${path}`)
}
return cfg as AppConfig
```

3. **`fetchRemoteConfig` has the same validation problem plus no HTTP error handling** — `res.json()` on a 404/500 may still resolve (e.g., an error body parsed as JSON) and be cast to `AppConfig`. Check `res.ok` first, and validate the payload shape as above:

```ts
if (!res.ok) throw new Error(`fetch ${url} failed: ${res.status}`)
```

**Non-blocking suggestions**

- `loadConfig`/`JSON.parse` will throw a raw `SyntaxError` on malformed JSON — consider wrapping with a contextual error message including `path`.
- `writeBackup` opens with "w" which truncates; if a backup should be atomic, write to a temp file and rename.
- Mixing sync (`readFileSync`, `openSync`/`writeSync`) and async (`fetch`) APIs is fine for a CLI, but if this module is used in a server context the sync calls will block the event loop — worth a comment or async variants.
- Style inconsistency: semicolons inside the interface but omitted elsewhere; pick one per project convention.
- No timeout on `fetch` — consider `AbortSignal.timeout(...)`.

**Verdict:** Request changes — the fd leak and the unchecked `AppConfig` casts are real defects; the rest is polish.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Identifies all three expected issues: the unclosed file descriptor, unvalidated loadConfig output, and missing fetch response status check. |
| Precision | 1 | The atomic-write and fetch-timeout suggestions are speculative enhancements rather than defects established by the diff; the style suggestion is also unrelated to the seeded issues. |
| Severity calibration | 1 | All three expected issues are grouped under “Blocking issues,” overstating their expected medium or medium/low severity. |
| Actionability | 2 | Provides concrete fixes and code examples, but does not include file or line references. |
| Reasoning correctness | 3 | Correctly explains the descriptor leak, the unchecked parsed configuration, and why an HTTP error response can still produce parsed JSON. |
| Format adherence | 1 | Includes findings and a verdict, but does not follow the requested Summary / Findings / Verdict structure. |
| Tone and concision | 2 | Generally constructive and clear, though several non-blocking suggestions add noise beyond the relevant findings. |

- Matched: fd_leak, fetch_no_status, no_validation
- Missed: none
- False positives: Atomic backup suggestion is speculative; no-fetch-timeout suggestion is an optional enhancement, not an established defect in the diff; semicolon-style suggestion is unrelated to the expected findings.
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "04-missing-error-handling",
  "scores": {
    "recall": 3,
    "precision": 1,
    "severity_calibration": 1,
    "actionability": 2,
    "reasoning": 3,
    "format": 1,
    "tone": 2
  },
  "rationale": {
    "recall": "Identifies all three expected issues: the unclosed file descriptor, unvalidated loadConfig output, and missing fetch response status check.",
    "precision": "The atomic-write and fetch-timeout suggestions are speculative enhancements rather than defects established by the diff; the style suggestion is also unrelated to the seeded issues.",
    "severity_calibration": "All three expected issues are grouped under “Blocking issues,” overstating their expected medium or medium/low severity.",
    "actionability": "Provides concrete fixes and code examples, but does not include file or line references.",
    "reasoning": "Correctly explains the descriptor leak, the unchecked parsed configuration, and why an HTTP error response can still produce parsed JSON.",
    "format": "Includes findings and a verdict, but does not follow the requested Summary / Findings / Verdict structure.",
    "tone": "Generally constructive and clear, though several non-blocking suggestions add noise beyond the relevant findings."
  },
  "matched": [
    "fd_leak",
    "fetch_no_status",
    "no_validation"
  ],
  "missed": [],
  "false_positives": [
    "Atomic backup suggestion is speculative; the diff does not establish that backup writes need to be atomic.",
    "No-fetch-timeout suggestion is an optional enhancement, not an established defect in the diff.",
    "Semicolon-style suggestion is unrelated to the expected findings."
  ],
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
