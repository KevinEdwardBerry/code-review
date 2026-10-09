---
prompt_version: v6
prompt_file: prompts/code-review.v6.md
fixture: 05-clean-refactor
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: false
---

# 05-clean-refactor / v6

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
Low-risk behavior-equivalent refactor replacing a manual accumulation loop with LINQ `Sum`.

## Findings
None.

## Verdict
Approve


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | There were no seeded issues. The review correctly reports None. |
| precision | 3 | The review has no false positives. It doesn't claim the arithmetic changed and doesn't complain about LINQ. It also doesn't mention the diff churn. |
| severity_calibration | 3 | The review raises no findings, so there is nothing to miscalibrate. The Approve verdict matches the ideal. |
| actionability | 3 | No findings were needed, and citation check is ok with no problems. Nothing is left unactionable. |
| reasoning | 3 | The summary correctly calls the change a behavior-equivalent refactor. |
| format | 3 | The review follows the Summary / Findings / Verdict structure exactly. |
| tone | 3 | The review is concise and has no filler. |

- Matched: none
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
    "recall": "There were no seeded issues. The review correctly reports None.",
    "precision": "The review has no false positives. It doesn't claim the arithmetic changed and doesn't complain about LINQ. It also doesn't mention the diff churn.",
    "severity_calibration": "The review raises no findings, so there is nothing to miscalibrate. The Approve verdict matches the ideal.",
    "actionability": "No findings were needed, and citation check is ok with no problems. Nothing is left unactionable.",
    "reasoning": "The summary correctly calls the change a behavior-equivalent refactor.",
    "format": "The review follows the Summary / Findings / Verdict structure exactly.",
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
