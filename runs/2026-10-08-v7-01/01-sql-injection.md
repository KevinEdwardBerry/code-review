---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 01-sql-injection
date: 2026-10-08
reviewer_model: unknown concrete model
reviewer_profile: subagent_explore
judge_model: unknown concrete model
judge_profile: subagent_general
weighted_score: 85.0
hard_fail: none
---

# 01-sql-injection / v7

## Models
- Reviewer: subagent_explore (unknown concrete model)
- Judge: subagent_general (unknown concrete model)

## AI response
# Code Review: `src/users.sql`

## Critical: SQL Injection Vulnerability

The `FindUserByName` stored procedure builds a query via string concatenation and executes it with `sp_executesql`. This is a textbook SQL injection flaw — the `@name` parameter is injected unescaped into the query text.

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

An attacker passing `@name = ' OR '1'='1'` (or worse, `'; DROP TABLE users;--`) can exfiltrate data or execute arbitrary statements. Note that wrapping the logic in a stored procedure provides **no** protection here — the vulnerability is created by the dynamic SQL itself.

### Fix options

**Option 1 (preferred):** Dynamic SQL isn't needed at all — this is a static query:

```sql
CREATE OR ALTER PROCEDURE FindUserByName
    @name nvarchar(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id, name, email FROM users WHERE name = @name;
END
GO
```

**Option 2:** If dynamic SQL were genuinely required, parameterize `sp_executesql` instead of concatenating:

```sql
EXEC sp_executesql
    N'SELECT id, name, email FROM users WHERE name = @name',
    N'@name nvarchar(255)',
    @name = @name;
```

## Minor issues

- `@query` is declared `nvarchar(1023)` — an odd size; if dynamic SQL is kept, `nvarchar(max)` avoids silent truncation.
- No error handling / `TRY...CATCH` or transaction semantics — not strictly needed for a single SELECT, but worth noting if the proc grows.
- `SELECT id, name, email` — good that it's explicit columns rather than `SELECT *`.
- Trailing `GO` is fine as a batch separator for SQL Server tooling; just confirm it's compatible with whatever migration runner applies this file.

## Verdict

**Request changes.** The procedure must be rewritten to use a parameterized query before merge.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Identifies the one seeded SQL injection flaw in FindUserByName (string concatenation into sp_executesql). |
| Precision | 2 | No fabricated or must-not-flag issues, but includes several trivial nits (nvarchar(1023) size, error handling, GO compatibility, positive SELECT note) that are not seeded findings. |
| Severity calibration | 3 | Correctly calls the SQLi critical and keeps remaining comments as minor/nit-level. |
| Actionability | 2 | Provides concrete, correct fix code (static query and parameterized sp_executesql), but does not give file:line references for the vulnerable line or any nit. |
| Reasoning | 3 | Accurately explains the injection mechanism and impact, including the important note that a stored procedure does not protect against the dynamic SQL flaw. |
| Format | 2 | Has findings and a verdict, ordered by severity, but lacks an explicit Summary / Findings structure and uses a generic title. |
| Tone | 2 | Constructive and focused on the critical issue, with a small amount of filler/positive commentary in the minor-issues section. |

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
    "precision": 2,
    "severity_calibration": 3,
    "actionability": 2,
    "reasoning": 3,
    "format": 2,
    "tone": 2
  },
  "rationale": {
    "recall": "Identifies the one seeded SQL injection flaw in FindUserByName (string concatenation into sp_executesql).",
    "precision": "No fabricated or must-not-flag issues, but includes several trivial nits (nvarchar(1023) size, error handling, GO compatibility, positive SELECT note) that are not seeded findings.",
    "severity_calibration": "Correctly calls the SQLi critical and keeps remaining comments as minor/nit-level.",
    "actionability": "Provides concrete, correct fix code (static query and parameterized sp_executesql), but does not give file:line references for the vulnerable line or any nit.",
    "reasoning": "Accurately explains the injection mechanism and impact, including the important note that a stored procedure does not protect against the dynamic SQL flaw.",
    "format": "Has findings and a verdict, ordered by severity, but lacks an explicit Summary / Findings structure and uses a generic title.",
    "tone": "Constructive and focused on the critical issue, with a small amount of filler/positive commentary in the minor-issues section."
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
