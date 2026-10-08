---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 01-sql-injection
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 71.7
hard_fail: false
---

# 01-sql-injection / v1

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Code Review: `src/users.sql`

### 🔴 Critical: SQL Injection Vulnerability

The `FindUserByName` procedure concatenates the `@name` parameter directly into a dynamic SQL string:

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

This is a textbook SQL injection vulnerability. An input like `' OR '1'='1' --` or `'; DROP TABLE users; --` would execute arbitrary SQL. Also, any legitimate name containing a single quote (e.g., `O'Brien`) will break the query.

### Recommended Fix

**Option 1 (preferred):** Dynamic SQL isn't needed at all here — use a plain parameterized query:

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

**Option 2:** If dynamic SQL is genuinely required, parameterize `sp_executesql`:

```sql
DECLARE @query nvarchar(1023) =
    N'SELECT id, name, email FROM users WHERE name = @name';
EXEC sp_executesql @query, N'@name nvarchar(255)', @name = @name;
```

### Minor Issues

- `@query` should be `nvarchar` with Unicode literal prefix (`N'...'`) to avoid implicit-conversion issues with non-ASCII names.
- No `NULL`/empty-input handling — decide whether `@name IS NULL` should return nothing or raise an error.
- If names aren't unique, consider whether callers expect multiple rows; document the contract.

**Verdict:** Do not merge as-is — the injection flaw must be fixed.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Identifies the critical SQL injection caused by concatenating @name into the dynamic SQL. |
| Precision | 1 | The Unicode-literal note is a plausible concern, but NULL handling and name-uniqueness suggestions are speculative and not defects established by the diff. |
| Severity calibration | 2 | The injection is correctly marked critical; the speculative minor suggestions add noise but are not assigned high severity. |
| Actionability | 2 | Provides concrete plain-query and parameterized sp_executesql fixes, but does not give line references. |
| Reasoning correctness | 3 | Correctly explains how user input can alter the dynamic SQL and notes that quote-containing names can break the query. |
| Format adherence | 1 | Includes a verdict and findings, but does not follow the specified Summary / Findings / Verdict structure. |
| Tone and concision | 2 | Mostly focused and constructive, though the extra speculative minor issues add some noise. |

- Matched: sqli
- Missed: none
- False positives: Speculative NULL/empty-input handling suggestion; speculative suggestion to document behavior for non-unique names.
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 1,
    "severity_calibration": 2,
    "actionability": 2,
    "reasoning": 3,
    "format": 1,
    "tone": 2
  },
  "rationale": {
    "recall": "Identifies the critical SQL injection caused by concatenating @name into the dynamic SQL.",
    "precision": "The Unicode-literal note is a plausible concern, but NULL handling and name-uniqueness suggestions are speculative and not defects established by the diff.",
    "severity_calibration": "The injection is correctly marked critical; the speculative minor suggestions add noise but are not assigned high severity.",
    "actionability": "Provides concrete plain-query and parameterized sp_executesql fixes, but does not give line references.",
    "reasoning": "Correctly explains how user input can alter the dynamic SQL and notes that quote-containing names can break the query.",
    "format": "Includes a verdict and findings, but does not follow the specified Summary / Findings / Verdict structure.",
    "tone": "Mostly focused and constructive, though the extra speculative minor issues add some noise."
  },
  "matched": [
    "sqli"
  ],
  "missed": [],
  "false_positives": [
    "Speculative NULL/empty-input handling suggestion.",
    "Speculative suggestion to document behavior for non-unique names."
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
