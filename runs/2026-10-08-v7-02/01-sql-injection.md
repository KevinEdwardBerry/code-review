---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 01-sql-injection
date: 2026-10-08
reviewer_model: unknown
reviewer_profile: subagent_explore
judge_model: unknown
judge_profile: subagent_general
weighted_score: 58.3
hard_fail: none
---

# 01-sql-injection / v7

## Models
- Reviewer: subagent_explore (unknown)
- Judge: subagent_general (unknown)

## AI response
# Code Review: `src/users.sql`

## Critical Issues

### 1. SQL Injection Vulnerability (BLOCKER)
The stored procedure builds a SQL string by concatenating `@name` directly into the query text and executing it with `sp_executesql`:

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

An attacker passing `@name = "x' OR '1'='1" --"` (or worse, `x'; DROP TABLE users; --`) will execute arbitrary SQL. This defeats the entire purpose of a stored procedure and is a textbook injection hole.

**Fix:** There is no reason for dynamic SQL here at all. Use a static parameterized statement:

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

If dynamic SQL were genuinely required (it isn’t), the safe pattern is parameterization via `sp_executesql`:

```sql
SET @query = N'SELECT id, name, email FROM users WHERE name = @p1';
EXEC sp_executesql @query, N'@p1 nvarchar(255)', @p1 = @name;
```

### 2. Unicode Prefix Missing
The dynamic string literal uses `'...'` instead of `N'...'`. Since `@query` is `nvarchar`, non-Unicode content in the literal is fine here, but the convention and safety practice is to always use `N` prefixes on `nvarchar` literals. Minor now, but it becomes a real bug if the query ever embeds other nvarchar data.

### 3. Quote-Escaping Fragility
Even if injection weren’t a concern, a legitimate name containing a single quote (e.g., `O'Brien`) would break the query at runtime — a silent functional bug that only surfaces with real data.

## Moderate Issues

### 4. `@query` Size Limit
`nvarchar(1023)` is an arbitrary, small cap. If this pattern grows, truncation produces a truncated/partial statement — possibly an error, possibly an altered-but-valid query. Use `nvarchar(max)` when dynamic SQL is justified (or, again, eliminate it).

### 5. Missing Schema Qualification
`users` should be `dbo.users` (or the appropriate schema). Unqualified references incur resolution overhead and can resolve to the wrong object depending on the executing user’s default schema.

### 6. Error Handling / Semantics
- No consideration of what "find" means: exact match vs. `LIKE`? Multiple users with the same name will return multiple rows — confirm callers handle that.
- No `TRY/CATCH` or transaction needed for a single SELECT, but worth noting if this proc grows.

## Minor / Style

- `SET NOCOUNT ON;` — good, included.
- Consider naming convention consistency (`FindUserByName` vs. `usp_...` or `Users_GetByName`, whatever the codebase uses).
- `CREATE OR ALTER` requires SQL Server 2016 SP1+ — confirm the target version.

## Summary

| Severity | Issue |
|---|---|
| 🔴 Blocker | SQL injection via string concatenation + `sp_executesql` |
| 🔴 Blocker | Quote characters in input break the query |
| 🟡 Moderate | Unqualified table name; arbitrary 1023-char buffer; unclear match semantics |
| 🟢 Minor | Missing `N` prefix; naming/version conventions |

**Recommendation:** Reject this change. The dynamic SQL provides zero benefit — replace it with the plain parameterized `SELECT` shown above, which fixes the injection hole, the quote-escaping bug, and the buffer limit in one edit.


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | The review identifies the seeded SQL injection vulnerability in FindUserByName and quotes the exact concatenated dynamic SQL from the diff. |
| Precision | 0 | The SQLi is correct, but the review adds multiple non-issues: the 1023-character @query limit is not a real defect for this query, missing schema qualification is a style nit dressed as a moderate functional issue, and the error-handling/semantics concerns are unsupported. It also duplicates the same SQLi defect as a separate 'Quote-Escaping Fragility' BLOCKER. |
| Severity | 1 | SQL injection is correctly called a blocker/critical, but the same defect is listed twice as a blocker, and non-issues (buffer size, schema, semantics) are rated as moderate. |
| Actionability | 2 | The SQLi fix is concrete and correct, but no exact file:line references are provided and some suggested fixes address non-issues. |
| Reasoning | 2 | SQLi explanation is correct with attack examples and impact, but the reasoning for the additional issues over-interprets the code. |
| Format | 2 | Review is structured by severity with a summary table, but the Summary/Verdict appears at the end rather than at the start and it lacks precise line references. |
| Tone | 2 | Professional and constructive, but verbose and includes several speculative nits that reduce focus. |

- Matched: sqli
- Missed: none
- False positives: Claims the @query nvarchar(1023) limit can produce a truncated/altered query (the query length is bounded by the 255-char @name), Missing schema qualification raised as a moderate functional issue (no evidence of multi-schema or wrong-object resolution in the diff), Error-handling/semantics concerns raised as an issue (the procedure name and query clearly specify exact-match behavior)
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 0,
    "severity_calibration": 1,
    "actionability": 2,
    "reasoning": 2,
    "format": 2,
    "tone": 2
  },
  "rationale": {
    "recall": "The review identifies the seeded SQL injection vulnerability in FindUserByName and quotes the exact concatenated dynamic SQL from the diff.",
    "precision": "The SQLi is correct, but the review adds multiple non-issues: the 1023-character @query limit is not a real defect for this query, missing schema qualification is a style nit dressed as a moderate functional issue, and the error-handling/semantics concerns are unsupported. It also duplicates the same SQLi defect as a separate 'Quote-Escaping Fragility' BLOCKER.",
    "severity_calibration": "SQL injection is correctly called a blocker/critical, but the same defect is listed twice as a blocker, and non-issues (buffer size, schema, semantics) are rated as moderate.",
    "actionability": "The SQLi fix is concrete and correct, but no exact file:line references are provided and some suggested fixes address non-issues.",
    "reasoning": "SQLi explanation is correct with attack examples and impact, but the reasoning for the additional issues over-interprets the code.",
    "format": "Review is structured by severity with a summary table, but the Summary/Verdict appears at the end rather than at the start and it lacks precise line references.",
    "tone": "Professional and constructive, but verbose and includes several speculative nits that reduce focus."
  },
  "matched": [
    "sqli"
  ],
  "missed": [],
  "false_positives": [
    "Claims the @query nvarchar(1023) limit can produce a truncated/altered query (the query length is bounded by the 255-char @name)",
    "Missing schema qualification raised as a moderate functional issue (no evidence of multi-schema or wrong-object resolution in the diff)",
    "Error-handling/semantics concerns raised as an issue (the procedure name and query clearly specify exact-match behavior)"
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
