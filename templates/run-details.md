# {{VERSION}} - {{DATE}} — Detailed results

- Prompt: `prompts/code-review.{{VERSION}}.md`
- Reviewer: {{REVIEWER_PROFILE}} ({{REVIEWER_MODEL}})
- Judge: {{JUDGE_PROFILE}} ({{JUDGE_MODEL}})
- Fixtures: {{FIXTURES}}
- Overall: **{{OVERALL}}/100** ({{DELTA}} vs {{PREV_VERSION}})
- Hard fails: {{HARD_FAILS}}

## What changed
{{WHAT_CHANGED}}

## Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
{{SCORE_TABLE}}

{{TYPO_RECALL}}

## Observations / next changes
{{OBSERVATIONS}}

## Per-fixture results
{{RUN_LINKS_AND_RESPONSES}}

---
