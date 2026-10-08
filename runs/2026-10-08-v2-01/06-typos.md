---
prompt_version: v2
prompt_file: prompts/code-review.v2.md
fixture: 06-typos
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 83.3
hard_fail: fabricated
---

# 06-typos / v2

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
The change adds an account creation module with mostly functional code, but contains several typos — including in an exported function name and a user-facing error message — plus a docstring that describes behavior the code doesn't implement.

## Findings

- **[Medium] src/accounts.ts:39 — Typo in exported identifier `getAdress`**
  ```ts
  export function getAdress(account: Account): string {
  ```
  `getAdress` should be `getAddress`. Exported API names are hard to rename later without breaking consumers. Fix: rename to `getAddress` before release.

- **[Low] src/accounts.ts:23 — Misspellings in user-facing error message**
  ```ts
  throw new Error("Username lenght must be at least 3 charaters.")
  ```
  "lenght" → "length", "charaters" → "characters". This string is shown to users. Fix: `throw new Error("Username length must be at least 3 characters.")`

- **[Low] src/accounts.ts:15 — Docstring claims behavior not implemented; also a comment typo**
  ```ts
  /**
   * Creates a new account and sends a welcome email.
   * We recieve the raw form input and normalize it.
   */
  ```
  The function never sends a welcome email (only logs), so the doc comment is misleading. Also "recieve" → "receive". Fix: either implement the email send or correct the comment.

- **[Low] src/accounts.ts:21 — Typo'd local variable `retires`**
  ```ts
  const retires = opts.maxRetries ?? DEFAULTS.maxRetries
  ```
  Used consistently (line 35), so functionally fine, but reads as "retires" rather than "retries". Fix: rename to `retries`.

- **[Low] src/accounts.ts:10 — `timeoutMs` option accepted but never used**
  ```ts
  const DEFAULTS = { maxRetries: 3, timeoutMs: 5000 }
  ```
  `opts.timeoutMs` is silently accepted and ignored. Fix: remove it from `DEFAULTS` or use it, so callers don't assume it has an effect.

- **[Low] src/accounts.ts:43 — Typo in public string literal**
  ```ts
  export const TEXT = "teh quick brown fox"
  ```
  "teh" → "the". Fix only if this string is user-facing; otherwise harmless.

## Verdict
Request changes — primarily to fix the exported `getAdress` name and the user-facing error message before this ships.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Identifies all six expected typos: t1 through t6. |
| Precision | 2 | The extra docstring observation is supported by the diff, but the timeoutMs finding is an unseeded configuration concern rather than an established defect. |
| Severity calibration | 2 | The exported API typo is ranked above the user-facing typos, but cosmetic typos are marked Low rather than nit, and the public string typo is placed after cosmetic findings. |
| Actionability | 2 | Findings include concrete fixes, but some cited line numbers do not point to the quoted code. |
| Reasoning | 3 | The typo explanations and impact of the exported API name are correct; the docstring claim is also contradicted by the implementation. |
| Format | 3 | Uses Summary, Findings, and Verdict sections, with findings ordered from Medium to Low severity. |
| Tone | 3 | Constructive and focused. |

- Matched: `t1_adress_api`, `t2_lenght`, `t3_charaters`, `t4_retires`, `t5_recieve`, `t6_teh_text`
- Missed: none
- False positives: `timeoutMs` option concern (unseeded and not established by the diff)
- Typo recall: misspelling 1/1; swap 3/3; missing_letter 2/2

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "06-typos",
  "scores": {"recall": 3, "precision": 2, "severity_calibration": 2, "actionability": 2, "reasoning": 3, "format": 3, "tone": 3},
  "rationale": {
    "recall": "Identifies all six expected typos: t1 through t6.",
    "precision": "The extra docstring observation is supported by the diff, but the timeoutMs finding is an unseeded configuration concern rather than an established defect.",
    "severity_calibration": "The exported API typo is ranked above the user-facing typos, but cosmetic typos are marked Low rather than nit, and the public string typo is placed after cosmetic findings.",
    "actionability": "Findings include concrete fixes, but some cited line numbers do not point to the quoted code.",
    "reasoning": "The typo explanations and impact of the exported API name are correct; the docstring claim is also contradicted by the implementation.",
    "format": "Uses Summary, Findings, and Verdict sections, with findings ordered from Medium to Low severity.",
    "tone": "Constructive and focused."
  },
  "matched": ["t1_adress_api", "t2_lenght", "t3_charaters", "t4_retires", "t5_recieve", "t6_teh_text"],
  "missed": [],
  "false_positives": ["Claims timeoutMs should be removed or used, although the diff alone does not establish that this option is intended to have behavior."],
  "typo_recall": {"misspelling": "1/1", "swap": "3/3", "missing_letter": "2/2"},
  "hard_fail": {"missed_critical": false, "fabricated": true, "missed_behavioral_typo": false}
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
