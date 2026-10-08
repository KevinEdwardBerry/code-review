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
The new `FindUserByName` procedure builds a SQL statement by concatenating the `@name` parameter directly into a query string, introducing a SQL injection vulnerability.

## Findings

**[Critical] src/users.sql:9-11 — SQL injection via string concatenation in dynamic SQL**

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

Impact: `@name` is interpolated verbatim into the query string. A caller passing a value like `x' OR '1'='1` (or worse, `x'; DROP TABLE users; --`) can read arbitrary rows or execute arbitrary statements. Any user input routed into this parameter is exploitable.

Fix: Either use a plain static query (no dynamic SQL needed here):

```sql
CREATE OR ALTER PROCEDURE FindUserByName
    @name nvarchar(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id, name, email FROM users WHERE name = @name;
END
```

or, if dynamic SQL is truly required, parameterize it:

```sql
EXEC sp_executesql
    N'SELECT id, name, email FROM users WHERE name = @name',
    N'@name nvarchar(255)',
    @name = @name;
```

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Identifies the expected SQL injection caused by concatenating @name into dynamic SQL. |
| Precision | 3 | Reports only the real vulnerability in the diff. |
| Severity calibration | 3 | Correctly rates the SQL injection as Critical. |
| Actionability | 3 | Provides the relevant file and line range and concrete static-query and parameterized-query fixes. |
| Reasoning | 3 | Explains how unescaped input can alter the query and describes the resulting impact. |
| Format | 3 | Uses the requested Summary, Findings, and Verdict sections in severity order. |
| Tone | 3 | Clear, focused, and professional. |

- Matched: sqli
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
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
    "recall": "Identifies the expected SQL injection caused by concatenating @name into dynamic SQL.",
    "precision": "Reports only the real vulnerability in the diff.",
    "severity_calibration": "Correctly rates the SQL injection as Critical.",
    "actionability": "Provides the relevant file and line range and concrete static-query and parameterized-query fixes.",
    "reasoning": "Explains how unescaped input can alter the query and describes the resulting impact.",
    "format": "Uses the requested Summary, Findings, and Verdict sections in severity order.",
    "tone": "Clear, focused, and professional."
  },
  "matched": [
    "sqli"
  ],
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
