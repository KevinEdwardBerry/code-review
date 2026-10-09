---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 01-sql-injection
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 81.7
hard_fail: none
---

# 01-sql-injection / v4

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
The new stored procedure builds SQL by string concatenation, introducing a direct SQL injection vulnerability.

## Findings

[Critical] src/users.sql:10 — SQL injection via concatenated parameter
```
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
```
`@name` is interpolated directly into a dynamic SQL string executed by `sp_executesql` (line 11). A caller passing a value like `x'; DROP TABLE users; --` (or extracting data via `UNION SELECT`) can execute arbitrary SQL. Impact: arbitrary query execution — data exfiltration, modification, or destruction depending on the login's permissions.

Fix: eliminate dynamic SQL entirely; it is unnecessary here since the query is static:
```sql
CREATE OR ALTER PROCEDURE FindUserByName
    @name nvarchar(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id, name, email FROM users WHERE name = @name;
END
```
If dynamic SQL were truly needed, parameterize it: `EXEC sp_executesql N'SELECT id, name, email FROM users WHERE name = @p', N'@p nvarchar(255)', @p = @name;`

[Low] src/users.sql:9 — `nvarchar(1023)` under-length buffer for the dynamic query
```
DECLARE @query nvarchar(1023);
```
`@name` alone can be up to 255 characters; combined with the ~70-char literal it fits today, but the odd length is arbitrary and truncation would silently alter the executed SQL. This is moot if the fix above removes the dynamic SQL; otherwise use `nvarchar(max)` or size it with slack.

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Finds the seeded critical SQL injection caused by concatenating @name into dynamic SQL. |
| Precision | 1 | The additional low-severity finding about the nvarchar(1023) buffer is a false positive: the current maximum input length and query text fit well within the buffer. |
| Severity calibration | 2 | The SQL injection is correctly marked Critical. The speculative buffer concern is marked Low despite not being a current defect. |
| Actionability | 3 | Gives a concrete parameterized fix and the correct file and line for the SQL injection finding. |
| Reasoning correctness | 3 | Correctly explains that user-controlled input reaches executed SQL and describes plausible impacts. |
| Format adherence | 3 | Uses Summary, Findings, and Verdict sections in the requested order, with findings ordered by severity. |
| Tone and concision | 3 | Focused, professional, and concise. |

- Matched: sqli
- Missed: none
- False positives: The claim that nvarchar(1023) is an under-length buffer and may truncate the current query.
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 1,
    "severity_calibration": 2,
    "actionability": 3,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Finds the seeded critical SQL injection caused by concatenating @name into dynamic SQL.",
    "precision": "The additional low-severity finding about the nvarchar(1023) buffer is a false positive: the current maximum input length and query text fit well within the buffer.",
    "severity_calibration": "The SQL injection is correctly marked Critical. The speculative buffer concern is marked Low despite not being a current defect.",
    "actionability": "Gives a concrete parameterized fix and the correct file and line for the SQL injection finding.",
    "reasoning": "Correctly explains that user-controlled input reaches executed SQL and describes plausible impacts.",
    "format": "Uses Summary, Findings, and Verdict sections in the requested order, with findings ordered by severity.",
    "tone": "Focused, professional, and concise."
  },
  "matched": ["sqli"],
  "missed": [],
  "false_positives": ["The claim that nvarchar(1023) is an under-length buffer and may truncate the current query."],
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
