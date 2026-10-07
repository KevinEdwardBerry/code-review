---
prompt_version: v6
prompt_file: prompts/code-review.v6.md
fixture: 01-sql-injection
date: 2026-10-07
reviewer_model: unknown
reviewer_profile: subagent_explore
judge_model: unknown
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: none
---

# 01-sql-injection / v6

## Models
- Reviewer: subagent_explore (unknown)
- Judge: subagent_general (unknown)

## AI response
### Summary
The change adds a SQL Server stored procedure `FindUserByName` that builds a query via string concatenation of user input, plus a stray appended line of non-SQL text that mixes code fragments into the file. The procedure contains a critical SQL injection vulnerability; the trailing line is malformed and only mirrors the same vulnerable pattern.

### Findings

- **[critical] src/users.sql:9 - SQL injection via string concatenation in dynamic SQL**
  - Problem: The user-supplied `@name` is concatenated directly into `@query` and executed via `sp_executesql`. An input like `'; DROP TABLE users; --` executes arbitrary SQL — the textbook injection pattern in a reachable, callable procedure.
  - Fix: Either use a plain parameterized statement (`SELECT id, name, email FROM users WHERE name = @name`) — no dynamic SQL is needed here — or parameterize properly: `EXEC sp_executesql @query, N'@name NVARCHAR(255)', @name = @name`.
  - Code snippet:
    ```
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **[low] src/users.sql:12 - stray malformed non-SQL line appended to file**
  - Problem: `SELECT id, name, email FROM users WHERE name = '" + name + "'"` is not valid T-SQL — it looks like a leftover application-code fragment (`name` is not a SQL identifier/string concatenation here). It will cause a syntax error if the file is executed as a script, and it merely repeats the vulnerable pattern without being reachable. Likely committed by accident.
  - Fix: Remove the line entirely.
  - Code snippet:
    ```
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

### Verdict
`request changes`


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Found the critical SQL injection vulnerability in FindUserByName via string concatenation. |
| Precision | 3 | No false positives; the second low finding is an acceptable extra. |
| Severity Calibration | 3 | Correctly rated the stored procedure as critical and the extra malformed query as low. |
| Actionability | 3 | Provides correct file:line references and concrete, correct fixes for both findings. |
| Reasoning | 3 | Explains the SQL injection impact and provides a proper parameterized fix. |
| Format | 3 | Follows Summary / Findings / Verdict structure and orders by severity. |
| Tone | 3 | Constructive, concise, and focused. |

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
    "actionability": 3,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Found the critical SQL injection vulnerability in FindUserByName via string concatenation.",
    "precision": "No false positives; the second low finding is an acceptable extra.",
    "severity_calibration": "Correctly rated the stored procedure as critical and the extra malformed query as low.",
    "actionability": "Provides correct file:line references and concrete, correct fixes for both findings.",
    "reasoning": "Explains the SQL injection impact and provides a proper parameterized fix.",
    "format": "Follows Summary / Findings / Verdict structure and orders by severity.",
    "tone": "Constructive, concise, and focused."
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
