---
prompt_version: {{VERSION}}
prompt_file: prompts/code-review.{{VERSION}}.md
fixture: {{FIXTURE}}
date: {{DATE}}
reviewer_model: {{REVIEWER_MODEL}}
reviewer_profile: {{REVIEWER_PROFILE}}
judge_model: {{JUDGE_MODEL}}
judge_profile: {{JUDGE_PROFILE}}
weighted_score: {{SCORE}}
hard_fail: {{HARD_FAIL}}
---

# {{FIXTURE}} / {{VERSION}}

## Models
- Reviewer: {{REVIEWER_PROFILE}} ({{REVIEWER_MODEL}})
- Judge: {{JUDGE_PROFILE}} ({{JUDGE_MODEL}})

## AI response
{{REVIEW}}

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
{{SCORE_ROWS}}

- Matched: {{MATCHED}}
- Missed: {{MISSED}}
- False positives: {{FALSE_POSITIVES}}
- Typo recall: {{TYPO_RECALL}}

<details><summary>Judge JSON</summary>

```json
{{JUDGE_JSON}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
