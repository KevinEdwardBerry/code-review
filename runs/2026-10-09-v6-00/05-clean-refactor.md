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
hard_fail: {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}
---

# 05-clean-refactor / v6

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
Low-risk refactor converting a manual accumulation loop into an equivalent LINQ `Sum` with an algebraically identical tax computation.

## Findings
None.

## Verdict
Approve

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | No seeded issues were present and the review correctly reports none. |
| precision | 3 | No false positives; the review correctly treats the change as a diff-churn-only, behavior-preserving refactor. |
| severity_calibration | 3 | No findings, so no severity mismatches; the empty findings list matches the expected clean result. |
| actionability | 3 | No fixes are required for a clean refactor and the review does not introduce unnecessary actions. |
| reasoning | 3 | Correctly characterizes the transformation as algebraically identical and low-risk. |
| format | 3 | Follows the requested Summary / Findings / Verdict ordering. |
| tone | 3 | Concise, constructive, and free of filler. |

- Matched: None
- Missed: None
- False positives: None
- Typo recall: N/A

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
    "recall": "No seeded issues were present and the review correctly reports none.",
    "precision": "No false positives; the review correctly treats the change as a diff-churn-only, behavior-preserving refactor.",
    "severity_calibration": "No findings, so no severity mismatches; the empty findings list matches the expected clean result.",
    "actionability": "No fixes are required for a clean refactor and the review does not introduce unnecessary actions.",
    "reasoning": "Correctly characterizes the transformation as algebraically identical and low-risk.",
    "format": "Follows the requested Summary / Findings / Verdict ordering.",
    "tone": "Concise, constructive, and free of filler."
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
