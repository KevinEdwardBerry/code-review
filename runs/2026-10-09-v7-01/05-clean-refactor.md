---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 05-clean-refactor
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: none
---

# 05-clean-refactor / v7

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
Low-risk refactor replacing a manual accumulation loop with LINQ `Sum`; behavior is equivalent.

## Findings
None.

## Verdict
Approve


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | The diff contains no seeded issues and the review correctly reports no findings. |
| Precision | 3 | No false positives; the clean refactor is not flagged incorrectly. |
| Severity | 3 | No severity ratings needed; no findings produced. |
| Actionability | 3 | No action items are appropriate for this behavior-preserving refactor. |
| Reasoning | 3 | Summary correctly identifies the change as equivalent and low-risk. |
| Format | 3 | Exactly follows the Summary / Findings / Verdict structure. |
| Tone | 3 | Constructive, concise, and free of filler. |


- Matched: none
- Missed: none
- False positives: none
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{"fixture": "05-clean-refactor", "scores": {"recall": 3, "precision": 3, "severity_calibration": 3, "actionability": 3, "reasoning": 3, "format": 3, "tone": 3}, "rationale": {"recall": "The diff contains no seeded issues and the review correctly reports no findings.", "precision": "No false positives; the clean refactor is not flagged incorrectly.", "severity_calibration": "No severity ratings needed; no findings produced.", "actionability": "No action items are appropriate for this behavior-preserving refactor.", "reasoning": "Summary correctly identifies the change as equivalent and low-risk.", "format": "Exactly follows the Summary / Findings / Verdict structure.", "tone": "Constructive, concise, and free of filler."}, "matched": [], "missed": [], "false_positives": [], "typo_recall": null, "hard_fail": {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}}

```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
