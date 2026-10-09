---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 04-missing-error-handling
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 76.7
hard_fail: false
---

# 04-missing-error-handling / v1

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
# Code Review: `src/config.ts`

Thanks for the addition — a few issues here that I'd want addressed before merge, ranging from correctness bugs to missing validation.

## 🔴 Bugs / Correctness

**1. `writeBackup` leaks the file descriptor**
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
The file descriptor is never closed via `fs.closeSync(fd)`. Under repeated calls this leaks FDs and on some platforms can produce incomplete writes or `EMFILE` errors. If you want the simpler API, `fs.writeFileSync(path, data)` does the same thing in one call without the leak. If you keep `openSync`, wrap in `try/finally` with `fs.closeSync(fd)`.

**2. `loadConfig` returns untyped, unvalidated data**
```ts
const cfg = JSON.parse(raw)
return cfg
```
`JSON.parse` returns `any`, so this silently satisfies the `AppConfig` return type while providing no guarantee the file actually contains `port`/`dbUrl` — a missing or mistyped field becomes a runtime failure far downstream. Either validate explicitly, or use a schema validator (zod, valibot, etc.). If you don't want a dependency, a manual check like `typeof cfg.port === "number"` before returning goes a long way.

**3. `fetchRemoteConfig` ignores HTTP errors and lacks validation**
```ts
const res = await fetch(url)
return res.json()
```
- No check of `res.ok` — a 404/500 HTML error page will be passed to `res.json()` and produce a confusing `SyntaxError` instead of a meaningful message.
- `res.json()` also returns `any`, so same unvalidated-shape problem as `loadConfig`.
- Consider a timeout (`AbortSignal.timeout(...)`) — a hung remote will otherwise block indefinitely.
- `res.json()` returns `Promise<any>` and you're returning it directly into `Promise<AppConfig>`; fine, but see the type-safety note below.

## 🟡 Minor / Consistency

**4. Sync vs async mixing**
`loadConfig` and `writeBackup` are synchronous while `fetchRemoteConfig` is async. If `loadConfig` is called at startup that's defensible, but `writeBackup` doing synchronous I/O on a hot path will block the event loop. Worth a comment or making it async (`fs.promises.writeFile`).

**5. Style inconsistency**
The file mixes `;` and no-`;` line endings (`port: number;` vs `import ... "fs"`). Pick whichever matches the project convention.

**6. Unhandled errors**
`JSON.parse` on malformed config throws a bare `SyntaxError`; consider wrapping with context like `Failed to load config at ${path}: ...` — debugging "Unexpected token" with no filename is painful.

## Suggested shape

```ts
export function loadConfig(path: string): AppConfig {
  const raw = fs.readFileSync(path, "utf8")
  const cfg: unknown = JSON.parse(raw)
  if (typeof cfg !== "object" || cfg === null
      || typeof (cfg as AppConfig).port !== "number"
      || typeof (cfg as AppConfig).dbUrl !== "string") {
    throw new Error(`Invalid config at ${path}`)
  }
  return cfg as AppConfig
}
```

**Verdict:** Request changes — the FD leak and the two unchecked `any` → `AppConfig` casts are the must-fixes.


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | All three must-find items are covered: the fd leak (#1), the missing res.ok check (#3), and unvalidated JSON.parse output with no error context (#2 and #6). |
| Precision | 2 | No serious false positives. The style inconsistency nit (#5) is trivial noise. The claim that the leak can cause incomplete writes is speculative. Item 3's last bullet is redundant and self-contradictory ("fine, but see the type-safety note below"). The timeout suggestion is scope creep but reasonable. |
| Severity calibration | 2 | The fd leak and the config validation are all marked 🔴 and called must-fixes, which is slightly high against the expected medium/low. The missing res.ok check is bundled into a single item, and the verdict does not list it as a must-fix. The sync I/O nit is correctly placed under Minor. |
| Actionability | 2 | Fixes are concrete: try/finally or writeFileSync, a validation snippet, and a res.ok check. Findings have no file:line references, only code snippets. The res.ok fix is described but not shown in code. CITATION_CHECK reports no problems. |
| Reasoning correctness | 2 | The explanations are correct and describe the impact: FD leaks and EMFILE, misleading SyntaxError on error pages, and failures far downstream. Some of it is shallow or slightly speculative. It misses that the fd also leaks when writeSync throws. |
| Format adherence | 2 | It has a summary line, findings grouped by severity, and a verdict. It uses custom headings instead of strict Summary/Findings/Verdict, and adds an unrequested 'Suggested shape' section. |
| Tone and concision | 2 | Constructive and professional. Some redundancy (the duplicated any note and the repeated JSON.parse context point in #6) and the style nit add mild noise. |

- Matched: fd_leak, fetch_no_status, no_validation
- Missed: none
- False positives: 
  - Style inconsistency nit about mixed semicolons (trivial noise)
  - Redundant, self-contradictory bullet about res.json() returning any in item 3
  - Speculative claim of incomplete writes on some platforms
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "04-missing-error-handling",
  "scores": {
    "recall": 3,
    "precision": 2,
    "severity_calibration": 2,
    "actionability": 2,
    "reasoning": 2,
    "format": 2,
    "tone": 2
  },
  "rationale": {
    "recall": "All three must-find items are covered: the fd leak (#1), the missing res.ok check (#3), and unvalidated JSON.parse output with no error context (#2 and #6).",
    "precision": "No serious false positives. The style inconsistency nit (#5) is trivial noise. The claim that the leak can cause incomplete writes is speculative. Item 3's last bullet is redundant and self-contradictory (\"fine, but see the type-safety note below\"). The timeout suggestion is scope creep but reasonable.",
    "severity_calibration": "The fd leak and the config validation are all marked 🔴 and called must-fixes, which is slightly high against the expected medium/low. The missing res.ok check is bundled into a single item, and the verdict does not list it as a must-fix. The sync I/O nit is correctly placed under Minor.",
    "actionability": "Fixes are concrete: try/finally or writeFileSync, a validation snippet, and a res.ok check. Findings have no file:line references, only code snippets. The res.ok fix is described but not shown in code. CITATION_CHECK reports no problems.",
    "reasoning": "The explanations are correct and describe the impact: FD leaks and EMFILE, misleading SyntaxError on error pages, and failures far downstream. Some of it is shallow or slightly speculative. It misses that the fd also leaks when writeSync throws.",
    "format": "It has a summary line, findings grouped by severity, and a verdict. It uses custom headings instead of strict Summary/Findings/Verdict, and adds an unrequested 'Suggested shape' section.",
    "tone": "Constructive and professional. Some redundancy (the duplicated any note and the repeated JSON.parse context point in #6) and the style nit add mild noise."
  },
  "matched": [
    "fd_leak",
    "fetch_no_status",
    "no_validation"
  ],
  "missed": [],
  "false_positives": [
    "Style inconsistency nit about mixed semicolons (trivial noise)",
    "Redundant, self-contradictory bullet about res.json() returning any in item 3",
    "Speculative claim of incomplete writes on some platforms"
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
