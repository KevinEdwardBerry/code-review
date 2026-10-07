---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 01-sql-injection
date: 2026-10-07
reviewer_model: default subagent model
reviewer_profile: subagent_explore
judge_model: parent model
judge_profile: subagent_general
weighted_score: 78.3
hard_fail: none
---

# 01-sql-injection / v4

## Models
- Reviewer: subagent_explore (default subagent model)
- Judge: subagent_general (parent model)

## AI response
### Summary
The change adds a SQL Server stored procedure `FindUserByName` that builds a query via string concatenation, plus a stray non-SQL fragment line. Both the procedure and the trailing line contain classic SQL injection, and the trailing line is also invalid SQL that will break the script.

### Findings
- **[critical] src/users.sql:8 - SQL injection via string concatenation in stored procedure**
  - Problem: `@name` is concatenated directly into the query text and executed with `sp_executesql`. A value like `' OR 1=1 --` (or `'; DROP TABLE users --`) lets an attacker read or modify arbitrary data.
  - Fix: Don't use dynamic SQL at all — `SELECT id, name, email FROM users WHERE name = @name` — or, if dynamic SQL is required, parameterize: `SET @query = N'... WHERE name = @p1'; EXEC sp_executesql @query, N'@p1 NVARCHAR(255)', @p1 = @name`.
  - Code snippet:
    ```sql
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **[critical] src/users.sql:12 - Stray line is both invalid T-SQL and SQL injection**
  - Problem: The line `SELECT id, name, email FROM users WHERE name = '" + name + "'` is not valid T-SQL — `name` is an undefined identifier and `"..."` string quoting/concatenation is wrong, so running this script fails outright. It also appears to be a pasted application-code fragment embedding the same injectable concatenation pattern.
  - Fix: Remove the line entirely; the procedure already covers the lookup. If it was meant as a query, replace with `WHERE name = @name` against a declared parameter.
  - Code snippet:
    ```sql
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

- **[low] src/users.sql:7 - DECLARE missing semicolon/terminator robustness**
  - Problem: `DECLARE @query NVARCHAR(MAX)` and `SET`/`EXEC` statements lack semicolons; while currently legal, a `BEGIN...END` block followed by more statements can hit parsing pitfalls (e.g., if a `WITH`/CTE or `THROW` is added later). Minor defensive issue.
  - Fix: Terminate statements with semicolons and initialize in one step: `DECLARE @query NVARCHAR(MAX) = N'...';`.
  - Code snippet:
    ```sql
    DECLARE @query NVARCHAR(MAX)
    ```

### Verdict
request changes


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Found the must-find critical SQL injection in FindUserByName via SET @query concatenation and sp_executesql. |
| Precision | 2 | No must-not-flag items flagged. The trailing SELECT line is an acceptable extra, but the DECLARE semicolon/terminator nit (src/users.sql:8) is a dubious, non-expected finding. |
| Severity calibration | 1 | Main SQLi correctly ranked critical. The trailing SELECT line is expected as low/nit but was ranked critical, which is more than one level off. |
| Actionability | 2 | Each finding includes a concrete fix and a code snippet, but line numbers are slightly off (SET @query is at line 9, trailing SELECT at line 13, DECLARE at line 8). |
| Reasoning correctness | 3 | Explanations correctly describe the SQL injection impact and the invalid T-SQL fragment. |
| Format adherence | 3 | Follows Summary / Findings / Verdict and is ordered by severity. |
| Tone and concision | 3 | Constructive, focused, and free of filler. |

- Matched: sqli
- Missed: none
- False positives: DECLARE missing semicolon/terminator robustness (src/users.sql:8) - dubious nit not in expected
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 2,
    "severity_calibration": 1,
    "actionability": 2,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Found the must-find critical SQL injection in FindUserByName via SET @query concatenation and sp_executesql.",
    "precision": "No must-not-flag items flagged. The trailing SELECT line is an acceptable extra, but the DECLARE semicolon/terminator nit (src/users.sql:8) is a dubious, non-expected finding.",
    "severity_calibration": "Main SQLi correctly ranked critical. The trailing SELECT line is expected as low/nit but was ranked critical, which is more than one level off.",
    "actionability": "Each finding includes a concrete fix and a code snippet, but line numbers are slightly off (SET @query is at line 9, trailing SELECT at line 13, DECLARE at line 8).",
    "reasoning": "Explanations correctly describe the SQL injection impact and the invalid T-SQL fragment.",
    "format": "Follows Summary / Findings / Verdict and is ordered by severity.",
    "tone": "Constructive, focused, and free of filler."
  },
  "matched": [
    "sqli"
  ],
  "missed": [],
  "false_positives": [
    "DECLARE missing semicolon/terminator robustness (src/users.sql:8) - dubious nit not in expected"
  ],
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
