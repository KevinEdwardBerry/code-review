---
prompt_version: v7
prompt_file: prompts/code-review-v7.md
fixture: 01-sql-injection
date: 2026-10-08
reviewer_model: unknown concrete model
reviewer_profile: subagent_explore
judge_model: unknown concrete model
judge_profile: subagent_general
weighted_score: 83.3
hard_fail: none
---

# 01-sql-injection / v7

## Models
- Reviewer: subagent_explore (unknown concrete model)
- Judge: subagent_general (unknown concrete model)

## AI response
# Code Review: `src/users.sql`

## Critical Issues

### 1. SQL Injection (BLOCKER)
Both additions build SQL via string concatenation with unparameterized user input:

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
EXEC sp_executesql @query
```
and
```sql
SELECT id, name, email FROM users WHERE name = '" + name + "'"
```

An input like `' OR '1'='1` or `'; DROP TABLE users; --` would execute arbitrary SQL. This defeats the entire purpose of a stored procedure.

**Fix** — the proc doesn't need dynamic SQL at all:
```sql
CREATE PROCEDURE FindUserByName
    @name NVARCHAR(255)
AS
BEGIN
    SELECT id, name, email FROM users WHERE name = @name;
END
```
If dynamic SQL were truly needed, use parameters: `EXEC sp_executesql @query, N'@name NVARCHAR(255)', @name`.

### 2. Invalid SQL Syntax (BLOCKER)
```sql
SELECT id, name, email FROM users WHERE name = '" + name + "'
```
This line sits at file top-level, outside any procedure, and mixes SQL with application-language string concatenation (`" + name + "`). It will fail to parse/execute as SQL. It looks like application code (e.g., PHP/JS) was accidentally pasted into the `.sql` file — it should be removed and replaced with a parameterized query in the calling code, or a call to the stored procedure.

## Minor Issues

- **Inconsistent style:** keywords are uppercase but there's no `;` statement terminators; `EXEC` lacks parentheses (valid, but `EXEC(...)` or `EXECUTE` is cleaner).
- **`NVARCHAR(MAX)`** for `@query` is unnecessary here, though harmless.
- No `SET NOCOUNT ON;` in the procedure (minor convention).
- The comment `-- User queries` followed by `+` on blank lines suggests formatting noise in the diff; ensure the file doesn't contain stray artifacts.

## Recommendation
Do not merge. Rewrite the procedure as a static parameterized query and delete the orphaned concatenated SELECT line entirely — and audit the application layer for any similar string-concatenated queries, since the pasted line suggests this pattern exists elsewhere.


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Found the critical SQLi in FindUserByName and also identified the additional concatenated query. |
| Precision | 2 | Contains extra findings not in EXPECTED (invalid SQL syntax in the orphaned SELECT, several style nits) but no hallucinations or must-not-flag items. |
| Severity calibration | 2 | The must-find sqli is correctly ranked critical, but the acceptable extra query is also ranked critical rather than low/nit. |
| Actionability | 2 | Provides concrete, correct fixes but does not give file:line references. |
| Reasoning correctness | 3 | Correctly explains SQL injection impact with example payloads. |
| Format adherence | 3 | Well-structured with Critical Issues, Minor Issues, and Recommendation. |
| Tone and concision | 3 | Constructive and focused, no filler. |

- Matched: sqli
- Missed: none
- False positives: "Invalid SQL syntax in the orphaned top-level SELECT (not an expected finding)"; "Style nits: missing semicolons, NVARCHAR(MAX) unnecessary, missing SET NOCOUNT ON, formatting noise"
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 2,
    "severity_calibration": 2,
    "actionability": 2,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Found the critical SQLi in FindUserByName and also identified the additional concatenated query.",
    "precision": "Contains extra findings not in EXPECTED (invalid SQL syntax in the orphaned SELECT, several style nits) but no hallucinations or must-not-flag items.",
    "severity_calibration": "The must-find sqli is correctly ranked critical, but the acceptable extra query is also ranked critical rather than low/nit.",
    "actionability": "Provides concrete, correct fixes but does not give file:line references.",
    "reasoning": "Correctly explains SQL injection impact with example payloads.",
    "format": "Well-structured with Critical Issues, Minor Issues, and Recommendation.",
    "tone": "Constructive and focused, no filler."
  },
  "matched": [
    "sqli"
  ],
  "missed": [],
  "false_positives": [
    "Invalid SQL syntax in the orphaned top-level SELECT (not an expected finding)",
    "Style nits: missing semicolons, NVARCHAR(MAX) unnecessary, missing SET NOCOUNT ON, formatting noise"
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
