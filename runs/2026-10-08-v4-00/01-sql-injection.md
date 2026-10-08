---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 01-sql-injection
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 95.0
hard_fail: false
---

# 01-sql-injection / v4

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
The new stored procedure builds dynamic SQL by concatenating a user-supplied name directly into the query string, creating a direct SQL injection vulnerability.

## Findings

[Critical] src/users.sql:9 — SQL injection via string concatenation into `sp_executesql`

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

The `@name` parameter is concatenated verbatim into the executed SQL text. Any caller-supplied value containing a single quote (e.g., `' OR 1=1; --`) escapes the string literal and executes as SQL, allowing unauthorized data access or modification (depending on the executing principal's permissions). There is no escaping of `@name` and no use of `sp_executesql`'s parameter-binding capability.

Fix: use a parameterized query instead of concatenation:

```sql
EXEC sp_executesql
    N'SELECT id, name, email FROM users WHERE name = @name',
    N'@name nvarchar(255)',
    @name = @name;
```

Alternatively, remove the dynamic SQL entirely and run the `SELECT` as a plain statement in the procedure body, since nothing here requires dynamic SQL.

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Finds the seeded SQL injection vulnerability caused by concatenating user input into dynamic SQL. |
| Precision | 3 | The finding is supported by the diff and does not flag acceptable T-SQL syntax or the procedure name. |
| Severity calibration | 3 | Critical severity matches the expected rating for the injection vulnerability. |
| Actionability | 2 | Gives a concrete parameterized-query fix, but cites line 9 while the concatenation is on new line 10. |
| Reasoning | 3 | Correctly explains how a quoted input can alter executed SQL and notes parameter binding. |
| Format | 3 | Uses the requested sections in order and orders findings by severity. |
| Tone | 3 | Focused, constructive, and concise. |

- Matched: sqli
- Missed: none
- False positives: none
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 3,
    "severity_calibration": 3,
    "actionability": 2,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Finds the seeded SQL injection vulnerability caused by concatenating user input into dynamic SQL.",
    "precision": "The finding is supported by the diff and does not flag acceptable T-SQL syntax or the procedure name.",
    "severity_calibration": "Critical severity matches the expected rating for the injection vulnerability.",
    "actionability": "Provides a concrete parameterized-query fix, but cites line 9 while the concatenation is on new line 10.",
    "reasoning": "Correctly explains how an input containing a quote can alter the executed SQL and notes that sp_executesql supports parameter binding.",
    "format": "Follows the requested Summary, Findings, and Verdict structure, with the finding ordered by severity.",
    "tone": "Focused, constructive, and concise."
  },
  "matched": ["sqli"],
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
Prior v3 score: 78.3; delta: +16.7. The line anchor points to a valid but unrelated changed line, so actionability is reduced; no hard-fail flag was assigned by the judge.
