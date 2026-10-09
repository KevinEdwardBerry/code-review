---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 05-clean-refactor
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed (judge used a separate subagent_general profile; a distinct concrete model could not be selected or verified)
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: false
---

# 05-clean-refactor / v7

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed (judge used a separate subagent_general profile; a distinct concrete model could not be selected or verified))

## AI response
## Summary
Behavior-equivalent refactor of `OrderTotal` from a manual loop to LINQ `Sum`; low risk.

## Findings
None.

## Verdict
Approve

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | There are no seeded issues. The review correctly reports None, which is the ideal outcome. |
| precision | 3 | The review has no false positives. It makes no claim that the arithmetic changed and no style complaint about LINQ. It also ignores the diff churn. |
| severity_calibration | 3 | No findings were raised, which matches the expected result. There are no severities to miscalibrate. |
| actionability | 3 | No findings were expected, so nothing needed a fix or a line reference. The review did not invent any. |
| reasoning | 3 | The review correctly calls the change a behavior-equivalent, low-risk refactor. |
| format | 3 | The review follows Summary / Findings / Verdict exactly, and Findings says None. |
| tone | 3 | The review is concise and has no filler. |

- Matched: none (no seeded issues)
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "05-clean-refactor",
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
    "recall": "There are no seeded issues. The review correctly reports None, which is the ideal outcome.",
    "precision": "The review has no false positives. It makes no claim that the arithmetic changed and no style complaint about LINQ. It also ignores the diff churn.",
    "severity_calibration": "No findings were raised, which matches the expected result. There are no severities to miscalibrate.",
    "actionability": "No findings were expected, so nothing needed a fix or a line reference. The review did not invent any.",
    "reasoning": "The review correctly calls the change a behavior-equivalent, low-risk refactor.",
    "format": "The review follows Summary / Findings / Verdict exactly, and Findings says None.",
    "tone": "The review is concise and has no filler."
  },
  "matched": [],
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
