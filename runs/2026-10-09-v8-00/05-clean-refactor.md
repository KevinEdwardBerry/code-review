---
prompt_version: v8
prompt_file: prompts/code-review.v8.md
fixture: 05-clean-refactor
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: none
---

# 05-clean-refactor / v8

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
Low-risk refactor that replaces a manual accumulation loop with `Enumerable.Sum` and algebraically equivalent tax computation (`total + total * taxRate` ≡ `subtotal * (1 + taxRate)`).

## Findings
None.

## Verdict
Approve

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Correctly identifies that the refactor has no issues and the ideal review has no findings. |
| Precision | 3 | No false positives; does not claim arithmetic changed, complain about LINQ, or flag diff churn. |
| Severity calibration | 3 | No severity errors; the clean diff is appropriately approved without inflated severity. |
| Actionability | 3 | No fixes are required for a clean refactor, and the verdict is clear. |
| Reasoning | 3 | Correctly notes the algebraic equivalence and the behavior-preserving nature of the change. |
| Format | 3 | Follows Summary / Findings / Verdict exactly. |
| Tone | 3 | Concise, constructive, and appropriate. |

- Matched: (none)
- Missed: (none)
- False positives: (none)
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
    "recall": "Correctly identifies that the refactor has no issues and the ideal review has no findings.",
    "precision": "No false positives; does not claim arithmetic changed, complain about LINQ, or flag diff churn.",
    "severity_calibration": "No severity errors; the clean diff is appropriately approved without inflated severity.",
    "actionability": "No fixes are required for a clean refactor, and the verdict is clear.",
    "reasoning": "Correctly notes the algebraic equivalence and the behavior-preserving nature of the change.",
    "format": "Follows Summary / Findings / Verdict exactly.",
    "tone": "Concise, constructive, and appropriate."
  },
  "matched": [],
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
