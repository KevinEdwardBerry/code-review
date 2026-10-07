## {{VERSION}} - {{DATE}}

- Prompt: `prompts/code-review.{{VERSION}}.md`
- Reviewer model: {{REVIEWER_MODEL}} | Judge model: {{JUDGE_MODEL}}
- Fixtures: {{FIXTURES}}
- Overall: **{{OVERALL}}/100** ({{DELTA}} vs {{PREV_VERSION}})
- Hard fails: {{HARD_FAILS}}

### What changed
{{WHAT_CHANGED}}

### Scores (0-3, AI judge)
| Fixture | Recall | Precision | Severity | Actionability | Reasoning | Format | Tone | Total | Delta |
|---|---|---|---|---|---|---|---|---|---|
{{SCORE_TABLE}}

### Observations / next changes
{{OBSERVATIONS}}

### Runs and AI responses
{{RUN_LINKS_AND_RESPONSES}}

---
