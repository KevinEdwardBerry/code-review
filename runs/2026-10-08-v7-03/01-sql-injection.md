---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 01-sql-injection
date: 2026-10-08
reviewer_model: unknown (concrete model not exposed)
reviewer_profile: subagent_explore
judge_model: unknown (concrete model not exposed)
judge_profile: subagent_general
weighted_score: 65.0
hard_fail: none
---

# 01-sql-injection / v7

## Models
- Reviewer: subagent_explore (unknown concrete model)
- Judge: subagent_general (unknown concrete model)

## AI response
## Code Review: `src/users.sql`

### Critical: SQL Injection (Blocker)

The procedure builds a query via string concatenation and executes it with `sp_executesql`, which is fully vulnerable to SQL injection:

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

An attacker passing `@name = "' OR '1'='1' --"` can dump all users; worse inputs can modify/drop data depending on connection permissions. The entire purpose of `sp_executesql` is to enable *parameterized* queries — it's being misused here.

**Fix — two options:**

1. Simplest: no dynamic SQL at all.
```sql
CREATE OR ALTER PROCEDURE FindUserByName
    @name nvarchar(255)
AS
BEGIN
    SET NOCOUNT ON;
    SELECT id, name, email FROM users WHERE name = @name;
END
```

2. If dynamic SQL is truly required (it isn't here), parameterize it:
```sql
SET @query = N'SELECT id, name, email FROM users WHERE name = @name';
EXEC sp_executesql @query, N'@name nvarchar(255)', @name = @name;
```

### Additional Issues

1. **Buffer truncation:** `@query` is `nvarchar(1023)` while `@name` is `nvarchar(255)` — fine for this string, but the odd limit (1023) suggests a pattern that could silently truncate in longer queries. If kept, use `nvarchar(max)` for the query variable.

2. **String literals should be Unicode-prefixed:** `'SELECT ...'` should be `N'SELECT ...'` when assigned to `nvarchar` to avoid implicit conversion issues.

3. **`GO` placement:** `GO` is a batch separator for tools like SSMS/sqlcmd, not T-SQL. If this file is executed through a migration runner that doesn't understand `GO`, it will fail. If it *is* needed, note the procedure body is terminated by `END`, so `GO` placement is fine — but verify the deployment tool supports it.

4. **Missing error handling / schema qualification:** Consider `dbo.FindUserByName` and `dbo.users` — unqualified object names can resolve to the caller's default schema and cause subtle bugs.

5. **Minor:** `NOCOUNT ON` is good, but there's no `TRY/CATCH` or transaction handling (acceptable for a read-only query, but worth noting).

### Verdict

**Request changes.** The concatenation-based dynamic SQL is a textbook injection vulnerability. The non-dynamic rewrite (option 1) is the correct fix — it's simpler, faster (no recompilation of dynamic text), and safe.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Finds the expected critical SQL injection in FindUserByName. |
| Precision | 0 | Several unsupported or speculative extra findings. |
| Severity calibration | 3 | Correctly ranks the injection as critical. |
| Actionability | 2 | Concrete fixes, but no exact file:line citation. |
| Reasoning | 2 | Correctly explains SQL injection impact; extras are speculative. |
| Format | 1 | Has findings and verdict but not the required Summary/Findings/Verdict structure. |
| Tone | 1 | Constructive, but speculative extras add noise. |

- Matched: `sqli`
- Missed: none
- False positives: buffer truncation; Unicode prefix; conditional GO compatibility; schema qualification; missing TRY/CATCH.
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 0,
    "severity_calibration": 3,
    "actionability": 2,
    "reasoning": 2,
    "format": 1,
    "tone": 1
  },
  "rationale": {
    "recall": "Finds the expected critical SQL injection in FindUserByName.",
    "precision": "Adds several unsupported or speculative issues: buffer truncation is not a demonstrated risk for this query and input size, Unicode-prefixing is not a defect here, and schema qualification, GO compatibility, and error handling are not established problems in the diff.",
    "severity_calibration": "Correctly ranks the injection as critical; the extra items are presented as additional considerations rather than higher-severity defects.",
    "actionability": "Provides concrete safe rewrites, but does not give line references for the finding or fixes.",
    "reasoning": "Correctly explains how concatenating user input into executable SQL enables injection and why parameterization prevents it. Some additional claims are speculative or not defects shown by the diff.",
    "format": "Includes a verdict and findings, but does not follow the rubric's requested Summary / Findings / Verdict structure.",
    "tone": "Constructive, but the lengthy list of speculative additional issues adds noise."
  },
  "matched": ["sqli"],
  "missed": [],
  "false_positives": [
    "Speculative buffer truncation concern for longer queries",
    "Unicode-prefixing presented as an issue",
    "Conditional GO/migration-runner concern",
    "Unqualified object names presented as a bug",
    "Missing TRY/CATCH noted as an issue"
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
