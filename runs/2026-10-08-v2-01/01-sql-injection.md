---
prompt_version: v2
prompt_file: prompts/code-review.v2.md
fixture: 01-sql-injection
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: none
---

# 01-sql-injection / v2

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
The new stored procedure builds a SQL statement by concatenating an unsanitized user-supplied parameter, introducing a direct SQL injection vulnerability.

## Findings

- [Critical] src/users.sql:8-10 — SQL injection via string concatenation into dynamic SQL
  ```sql
  SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
  EXEC sp_executesql @query;
  ```
  **Impact:** `@name` is interpolated verbatim, so input like `'; DROP TABLE users; --` (or exfiltration/UNION-based payloads) executes arbitrary SQL with the caller's privileges. Any caller passing user input here enables full SQLi.
  **Fix:** Either drop dynamic SQL entirely (`SELECT id, name, email FROM users WHERE name = @name;`) or parameterize it: `EXEC sp_executesql N'SELECT id, name, email FROM users WHERE name = @name', N'@name nvarchar(255)', @name;`

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Identifies the expected SQL injection caused by concatenating @name into dynamic SQL. |
| Precision | 3 | The finding is supported by the cited code in the diff; no false positives. |
| Severity calibration | 3 | Correctly rates the SQL injection vulnerability as Critical. |
| Actionability | 3 | Provides concrete fixes, including a parameterized sp_executesql option, and cites the correct file and lines. |
| Reasoning | 3 | Accurately explains that user input is interpolated verbatim and can alter or extend the executed SQL. |
| Format | 3 | Follows the requested Summary / Findings / Verdict structure, with the finding under Findings. |
| Tone | 3 | Constructive, focused, and concise. |

- Matched: `sqli`
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {"recall": 3, "precision": 3, "severity_calibration": 3, "actionability": 3, "reasoning": 3, "format": 3, "tone": 3},
  "rationale": {
    "recall": "Identifies the expected SQL injection caused by concatenating @name into dynamic SQL.",
    "precision": "The finding is supported by the cited code in the diff; no false positives.",
    "severity_calibration": "Correctly rates the SQL injection vulnerability as Critical.",
    "actionability": "Provides concrete fixes, including a parameterized sp_executesql option, and cites the correct file and lines.",
    "reasoning": "Accurately explains that user input is interpolated verbatim and can alter or extend the executed SQL.",
    "format": "Follows the requested Summary / Findings / Verdict structure, with the finding under Findings.",
    "tone": "Constructive, focused, and concise."
  },
  "matched": ["sqli"],
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
