---
prompt_version: v5
prompt_file: prompts/code-review.v5.md
fixture: 01-sql-injection
date: 2026-10-07
reviewer_model: subagent_explore (default subagent model)
reviewer_profile: subagent_explore
judge_model: subagent_general (parent model)
judge_profile: subagent_general
weighted_score: 95.0
hard_fail: false
---

# 01-sql-injection / v5

## Models
- Reviewer: subagent_explore (subagent_explore (default subagent model))
- Judge: subagent_general (subagent_general (parent model))

## AI response

### Summary
The change adds a SQL Server stored procedure that builds a query by concatenating an input parameter directly into a dynamic SQL string, plus a trailing invalid SQL fragment. The dynamic SQL is trivially injectable.

### Findings
- **[critical] src/users.sql:8 — SQL injection via string concatenation in `FindUserByName`**
  - Problem: `@name` is interpolated into the SQL text executed by `sp_executesql`. Any caller-supplied value like `' OR 1=1 --` escapes the string literal and executes arbitrary SQL, exposing/dropping data. This is a textbook SQL injection reachable through the procedure's only parameter.
  - Fix: Either use a plain static statement (`SELECT id, name, email FROM users WHERE name = @name`) or parameterize the dynamic SQL: `EXEC sp_executesql N'SELECT ... WHERE name = @n', N'@n NVARCHAR(255)', @n = @name`.
  - Code snippet:
    ```sql
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **[low] src/users.sql:12 — invalid, non-executable SQL fragment left in file**
  - Problem: `SELECT id, name, email FROM users WHERE name = '" + name + "'"` is not valid SQL — it looks like a pasted application-layer snippet (e.g. C# string concatenation) and will cause a syntax error if the file is executed as a script. It also mirrors the same injectable pattern.
  - Fix: Remove the line, or if it documents a query to be implemented elsewhere, move it into the proper parameterized statement.
  - Code snippet:
    ```sql
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

### Verdict
`request changes`

## Judge scores (AI)

| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Found the seeded critical SQL injection in FindUserByName and the additional trailing query injection. |
| Precision | 3 | No false positives; only the expected critical and an acceptable low/nit extra. |
| Severity calibration | 3 | Critical for the SQL injection and low for the extra match expected severities. |
| Actionability | 2 | Fixes are concrete and correct, but file:line references are one line off from the official diff line numbers. |
| Reasoning | 3 | Correctly explains the SQL injection via string concatenation and the invalid trailing fragment. |
| Format | 3 | Follows Summary / Findings / Verdict, ordered by severity. |
| Tone | 3 | Constructive, technical, and concise. |

- Matched: [sqli]
- Missed: []
- False positives: []
- Typo recall: n/a

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
    "recall": "Found the seeded critical SQL injection in FindUserByName and the additional trailing query injection.",
    "precision": "No false positives; only the expected critical and an acceptable low/nit extra.",
    "severity_calibration": "Critical for the SQL injection and low for the extra match expected severities.",
    "actionability": "Fixes are concrete and correct, but file:line references are one line off from the official diff line numbers.",
    "reasoning": "Correctly explains the SQL injection via string concatenation and the invalid trailing fragment.",
    "format": "Follows Summary / Findings / Verdict, ordered by severity.",
    "tone": "Constructive, technical, and concise."
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
