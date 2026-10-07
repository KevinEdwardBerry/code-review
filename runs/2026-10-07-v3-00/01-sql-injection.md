---
prompt_version: v3
prompt_file: prompts/code-review.v3.md
fixture: 01-sql-injection
date: 2026-10-07
reviewer_model: subagent_explore default model
reviewer_profile: subagent_explore
judge_model: subagent_explore default model
judge_profile: subagent_explore
weighted_score: 85.0
hard_fail: none
---

# 01-sql-injection / v3

## Models
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model)

## AI response
### Summary
The diff adds a stored procedure that builds a SQL query via string concatenation and executes it with `sp_executesql`, plus a commented/loose "alternative" line that shows the same concatenation pattern. This introduces a clear, exploitable SQL injection vulnerability.

### Findings

- **critical src/users.sql:8-10 — SQL injection via dynamic SQL string concatenation**
  - Problem: `@name` is interpolated directly into a query string and executed. Input like `'; DROP TABLE users; --` escapes the quoted literal and runs arbitrary SQL. This is the classic SQLi pattern — parameterization must be used, not string building.
  - Fix: use a parameterized query, e.g.
    ```sql
    CREATE PROCEDURE FindUserByName
        @name NVARCHAR(255)
    AS
    BEGIN
        SELECT id, name, email FROM users WHERE name = @name
        -- or, if dynamic SQL is truly needed:
        -- EXEC sp_executesql N'SELECT id, name, email FROM users WHERE name = @p', N'@p NVARCHAR(255)', @p = @name
    END
    ```
  - Code snippet:
    ```sql
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **high src/users.sql:15 — invalid SQL committed to the file**
  - Problem: the line `SELECT ... WHERE name = '" + name + "'`" is not valid T-SQL — it's application-level concatenation pseudocode left in a .sql file. It will break anything that executes this file (migrations, schema apply scripts). Even as a "documentation" of the vulnerable pattern, it shouldn't ship.
  - Fix: delete the line entirely; do not retain vulnerable example code in the repo.
  - Code snippet:
    ```sql
    -- Alternative vulnerable approach
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

- **medium src/users.sql:9 — `DECLARE @query` missing semicolon/termination robustness**
  - Problem: minor — `NVARCHAR(MAX)` for a fixed-shape query and absence of `SET NOCOUNT ON` / error handling is noise compared to the injection, but worth cleaning up while fixing the procedure.
  - Fix: once the procedure is rewritten as a direct parameterized SELECT, this disappears.

### Verdict
request changes — the change introduces an exploitable SQL injection and an invalid SQL statement; both must be fixed before merge.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | Found the critical SQLi in FindUserByName (lines 8-10 vs expected 9-10 — acceptable) with the correct parameterized fix, and noted the alternative concatenation line. |
| precision | 2 | The medium finding about DECLARE/SET NOCOUNT ON/missing semicolon is dubious noise — no semicolon is required after DECLARE in T-SQL. Otherwise clean. |
| severity_calibration | 2 | Core critical correctly rated critical. The alternative line (expected low/nit extra) is rated high for a different reason ('invalid SQL breaks migrations'), which inflates it; the nit is medium rather than low. |
| actionability | 3 | Concrete parameterized fix matching the expected remediation, correct file and line ranges, plus a clear delete recommendation for line 14/15. |
| reasoning | 2 | SQLi explanation is correct and demonstrates exploitability. The claim that line 15 'will break anything that executes this file' is speculative and the reasoning for the medium nit (semicolon, NOCOUNT) is largely incorrect. |
| format | 3 | Follows Summary / Findings / Verdict, ordered by severity, with snippets. |
| tone | 3 | Constructive and focused, no filler. |

- Matched: sqli
- Missed: 
- False positives: medium nit claiming DECLARE missing semicolon / missing SET NOCOUNT ON is a real issue; line 15 reframed as high-severity 'invalid SQL that breaks migrations' rather than a low/nit vulnerable-pattern note
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 2,
    "severity_calibration": 2,
    "actionability": 3,
    "reasoning": 2,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Found the critical SQLi in FindUserByName (lines 8-10 vs expected 9-10 — acceptable) with the correct parameterized fix, and noted the alternative concatenation line.",
    "precision": "The medium finding about DECLARE/SET NOCOUNT ON/missing semicolon is dubious noise — no semicolon is required after DECLARE in T-SQL. Otherwise clean.",
    "severity_calibration": "Core critical correctly rated critical. The alternative line (expected low/nit extra) is rated high for a different reason ('invalid SQL breaks migrations'), which inflates it; the nit is medium rather than low.",
    "actionability": "Concrete parameterized fix matching the expected remediation, correct file and line ranges, plus a clear delete recommendation for line 14/15.",
    "reasoning": "SQLi explanation is correct and demonstrates exploitability. The claim that line 15 'will break anything that executes this file' is speculative and the reasoning for the medium nit (semicolon, NOCOUNT) is largely incorrect.",
    "format": "Follows Summary / Findings / Verdict, ordered by severity, with snippets.",
    "tone": "Constructive and focused, no filler."
  },
  "matched": ["sqli"],
  "missed": [],
  "false_positives": ["medium nit claiming DECLARE missing semicolon / missing SET NOCOUNT ON is a real issue", "line 15 reframed as high-severity 'invalid SQL that breaks migrations' rather than a low/nit vulnerable-pattern note"],
  "typo_recall": null,
  "hard_fail": {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
