---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 01-sql-injection
date: 2026-10-07
reviewer_model: subagent_explore default model
judge_model: subagent_explore default model
weighted_score: 95.0
hard_fail: false
---

# 01-sql-injection / v1

## AI response

### Summary
The change adds a stored procedure `FindUserByName` that builds a SQL string via concatenation, plus a commented "alternative" line — both introduce SQL injection vulnerabilities in what is labeled "user queries."

### Findings
- **critical src/users.sql:9 - SQL injection via string concatenation in stored procedure**
- Problem: `@name` is interpolated directly into a dynamic SQL string and executed with `sp_executesql`. An attacker passing `x' OR '1'='1` (or `'; DROP TABLE users;--`) can read all users or execute arbitrary statements. This is a textbook exploitable vulnerability.
- Fix: Either use a static query (`SELECT id, name, email FROM users WHERE name = @name`) — preferred, since no dynamic SQL is needed here — or parameterize properly:
```sql
SET @query = N'SELECT id, name, email FROM users WHERE name = @pname'
EXEC sp_executesql @query, N'@pname NVARCHAR(255)', @pname = @name
```
- **high src/users.sql:18 - Vulnerable code left in file as a comment**
- Problem: The line `SELECT ... WHERE name = '" + name + "'` is another injection-prone pattern sitting in the file, explicitly labeled "Alternative vulnerable approach." Even as a comment, it invites copy-paste into application code and may trip security scanners/audits.
- Fix: Delete it, or replace with a safe parameterized example if an alternative is genuinely needed.
- **nit src/users.sql - Formatting/semicolon nits**
- Problem: Extra blank lines at the top of the file, missing semicolon after `DECLARE`, and `NVARCHAR` should be `N'...'` literal prefix for Unicode safety in the query string (the string literal should use the `N` prefix since `@query` is `NVARCHAR`).
- Fix: `SET @query = N'SELECT ...'`, tidy whitespace, add semicolons.

### Verdict
request changes — the stored procedure must not concatenate user input into dynamic SQL.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | The critical sqli finding is identified at the correct location (dynamic SQL built by concatenating @name in FindUserByName, cited at src/users.sql:9). |
| Precision | 3 | No false positives. The second finding (the 'alternative' concatenation line) is an explicitly acceptable extra, and the nit list (missing N prefix on NVARCHAR literal, semicolons, whitespace) is valid minor noise. |
| Severity calibration | 2 | The main sqli is correctly rated critical. However, the commented 'alternative approach' line — expected as low/nit — is rated high, more than one level off. |
| Actionability | 3 | Each finding has a concrete fix with file:line reference; the sqli fix correctly shows parameterized sp_executesql usage and even suggests the better static-query option. |
| Reasoning | 3 | Explanations are correct and demonstrate exploit impact (OR '1'='1, DROP TABLE), correctly noting sp_executesql alone does not protect against concatenated input. |
| Format | 3 | Follows Summary / Findings / Verdict structure, findings ordered by severity. |
| Tone | 3 | Constructive and focused, no filler. |

- Matched: sqli
- Missed: none
- False positives: none
- Typo recall: null

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 3,
    "severity_calibration": 2,
    "actionability": 3,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "The critical sqli finding is identified at the correct location (dynamic SQL built by concatenating @name in FindUserByName, cited at src/users.sql:9).",
    "precision": "No false positives. The second finding (the 'alternative' concatenation line) is an explicitly acceptable extra, and the nit list (missing N prefix on NVARCHAR literal, semicolons, whitespace) is valid minor noise.",
    "severity_calibration": "The main sqli is correctly rated critical. However, the commented 'alternative approach' line — expected as low/nit — is rated high, more than one level off.",
    "actionability": "Each finding has a concrete fix with file:line reference; the sqli fix correctly shows parameterized sp_executesql usage and even suggests the better static-query option.",
    "reasoning": "Explanations are correct and demonstrate exploit impact (OR '1'='1, DROP TABLE), correctly noting sp_executesql alone does not protect against concatenated input.",
    "format": "Follows Summary / Findings / Verdict structure, findings ordered by severity.",
    "tone": "Constructive and focused, no filler."
  },
  "matched": ["sqli"],
  "missed": [],
  "false_positives": [],
  "typo_recall": null,
  "hard_fail": {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
