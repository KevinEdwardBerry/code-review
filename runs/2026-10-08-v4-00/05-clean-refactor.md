---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 05-clean-refactor
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: false
---

# 05-clean-refactor / v4

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
Low-risk refactor of `OrderTotal` from a manual accumulation loop to `Enumerable.Sum` with an algebraically equivalent tax computation.

## Findings
None.

## Verdict
Approve

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Correctly reports no findings for a behavior-preserving refactor. |
| Precision | 3 | Does not invent issues or flag acceptable implementation choices. |
| Severity calibration | 3 | Assigns no inappropriate severity where there are no issues. |
| Actionability | 3 | Clearly states there are no findings and gives an approval verdict. |
| Reasoning | 3 | Accurately describes the loop-to-Sum refactor and equivalent tax calculation. |
| Format | 3 | Uses a clear summary, findings, and verdict structure. |
| Tone | 3 | Professional and concise. |

- Matched: none (no seeded findings)
- Missed: none
- False positives: none
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{"fixture":"05-clean-refactor","scores":{"recall":3,"precision":3,"severity_calibration":3,"actionability":3,"reasoning":3,"format":3,"tone":3},"rationale":{"recall":"Correctly reports no findings for a behavior-preserving refactor.","precision":"Does not invent issues or flag acceptable implementation choices.","severity_calibration":"Assigns no severity because there are no issues.","actionability":"Clearly states that there are no findings and gives an approval verdict.","reasoning":"Accurately describes the loop-to-Sum refactor and equivalent tax calculation.","format":"Uses a clear summary, findings, and verdict structure.","tone":"Professional and concise."},"matched":["Recognizes the refactor as low-risk and behavior-preserving.","Reports no findings.","Approves the change."],"missed":[],"false_positives":[],"typo_recall":null,"hard_fail":{"missed_critical":false,"fabricated":false,"missed_behavioral_typo":false},"weighted_score":100}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
Prior v3 score: 100.0; delta: 0.0.
