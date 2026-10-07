---
prompt_version: v2
prompt_file: prompts/code-review.v2.md
fixture: 01-sql-injection
date: 2026-10-07
reviewer_model: subagent_explore default model
reviewer_profile: subagent_explore
judge_model: subagent_explore default model
judge_profile: subagent_explore
weighted_score: 95.0
hard_fail: false
---

# 01-sql-injection / v2

## Models
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model)

## AI response
### Summary
This change adds a stored procedure `FindUserByName` that builds a SQL query via string concatenation of user input, plus a commented-out inline concatenation example. It introduces a classic SQL injection vulnerability.

### Findings

- **[critical] src/users.sql:6-8 — SQL injection via string concatenation in `sp_executesql`**
  - Problem: `@name` is concatenated directly into the query string and executed with `sp_executesql`. Any caller-supplied name like `' OR '1'='1` (or `'; DROP TABLE users; --`) can read/modify arbitrary data. This is a textbook exploitable injection.
  - Fix: Don't use dynamic SQL at all — write a plain parameterized statement inside the procedure:
    ```sql
    CREATE PROCEDURE FindUserByName
        @name NVARCHAR(255)
    AS
    BEGIN
        SELECT id, name, email FROM users WHERE name = @name
    END
    ```
    If dynamic SQL is truly required (it isn't here), use parameter binding: `EXEC sp_executesql @query, N'@name NVARCHAR(255)', @name = @name` with `@name` as a placeholder inside the query string.
  - Code snippet:
    ```
    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
    EXEC sp_executesql @query
    ```

- **[medium] src/users.sql:11 — second injection-prone snippet committed to source**
  - Problem: The trailing line `WHERE name = '" + name + "'"` appears to be leftover application-side pseudocode (the `" + name + "` syntax is not valid T-SQL). Even though it's labeled "Alternative vulnerable approach," it is not a comment — it's invalid SQL in the file and models an unsafe pattern. It will break any attempt to run the script and normalizes the same injection flaw in code that touches the DB.
  - Fix: Delete it, or turn it into an actual comment (`--`) if it's meant as documentation — though there's no reason to ship a known-vulnerable example; keep it out of the file.
  - Code snippet:
    ```
    SELECT id, name, email FROM users WHERE name = '" + name + "'"
    ```

### Verdict
request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | The critical SQL injection in FindUserByName is found and correctly diagnosed, including the concatenated @name into sp_executesql. |
| Precision | 3 | No false positives. The second finding (the 'Alternative vulnerable approach' line) is an acceptable extra per EXPECTED, and the review's additional observation that it is invalid T-SQL that would break script execution is accurate and useful rather than noise. |
| Severity calibration | 3 | Critical for the injectable procedure, medium for the committed vulnerable/invalid snippet — consistent with expected critical plus low/nit extra (within one level). |
| Actionability | 2 | Concrete, correct fixes are given (both a plain parameterized statement and proper sp_executesql parameter binding). However, line references are slightly off: the finding cites lines 6-8 while the concatenation is on lines 9-10, and the second snippet is on line 14, not 11. |
| Reasoning | 3 | Correctly explains exploitability with example payloads, notes sp_executesql alone doesn't parameterize, and accurately identifies the second line as invalid T-SQL. |
| Format | 3 | Follows Summary / Findings / Verdict structure with findings ordered by severity. |
| Tone | 3 | Constructive, focused, no filler. |

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
    "precision": 3,
    "severity_calibration": 3,
    "actionability": 2,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "The critical SQL injection in FindUserByName is found and correctly diagnosed, including the concatenated @name into sp_executesql.",
    "precision": "No false positives. The second finding (the 'Alternative vulnerable approach' line) is an acceptable extra per EXPECTED, and the review's additional observation that it is invalid T-SQL that would break script execution is accurate and useful rather than noise.",
    "severity_calibration": "Critical for the injectable procedure, medium for the committed vulnerable/invalid snippet — consistent with expected critical plus low/nit extra (within one level).",
    "actionability": "Concrete, correct fixes are given (both a plain parameterized statement and proper sp_executesql parameter binding). However, line references are slightly off: the finding cites lines 6-8 while the concatenation is on lines 9-10, and the second snippet is on line 14, not 11.",
    "reasoning": "Correctly explains exploitability with example payloads, notes sp_executesql alone doesn't parameterize, and accurately identifies the second line as invalid T-SQL.",
    "format": "Follows Summary / Findings / Verdict structure with findings ordered by severity.",
    "tone": "Constructive, focused, no filler."
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
