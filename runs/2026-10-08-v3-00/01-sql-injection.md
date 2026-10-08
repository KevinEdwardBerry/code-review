---
prompt_version: v3
prompt_file: prompts/code-review.v3.md
fixture: 01-sql-injection
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 78.3
hard_fail: false
---

# 01-sql-injection / v3

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
This change adds a stored procedure that builds a dynamic SQL query by concatenating an unvalidated user parameter, creating a direct SQL injection vulnerability.

## Findings

[Critical] src/users.sql:9-10 — SQL injection via string concatenation in dynamic SQL

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + '''';
EXEC sp_executesql @query;
```

`@name` is interpolated directly into the query string. An attacker passing `'; DROP TABLE users; --` (or similar) can inject arbitrary SQL, leading to data exfiltration or destructive commands. There is also no escaping or quoting of the input.

Fix: parameterize the dynamic statement instead of concatenating:

```sql
SET @query = N'SELECT id, name, email FROM users WHERE name = @name';
EXEC sp_executesql @query, N'@name nvarchar(255)', @name;
```

Alternatively, if no dynamic SQL is actually needed, run the static `SELECT` directly in the procedure.

[Low] src/users.sql:8 — `nvarchar(1023)` may truncate long `@name` values combined with the query prefix

```sql
DECLARE @query nvarchar(1023);
```

The query literal is ~70 characters; a full-length 255-char `@name` fits, so this is fine as written, but the odd 1023 length is unusual — `nvarchar(max)` or a larger fixed size would be more robust if the query grows. Low severity; optional fix once the injection above is resolved (a parameterized statement makes size requirements clearer).

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Identifies the expected critical SQL injection caused by concatenating `@name` into the dynamic query. |
| Precision | 1 | The additional low-severity finding is a false positive: the stated maximum-length input fits in the declared query variable, and hypothetical future query growth is not a defect in this diff. |
| Severity calibration | 3 | The SQL injection is correctly marked Critical, matching the expected severity. |
| Actionability | 2 | The injection finding gives a concrete parameterized fix and file reference. The additional finding cites the wrong line for the declaration and proposes a speculative change. |
| Reasoning | 2 | The injection explanation correctly describes how interpolated input can alter the executed SQL. The truncation concern is unsupported by the stated lengths, which weakens the overall reasoning. |
| Format | 3 | Uses Summary, Findings, and Verdict, with findings ordered by severity. |
| Tone | 3 | Constructive, focused, and concise. |

- Matched: sqli
- Missed: none
- False positives: claims `nvarchar(1023)` may truncate a full-length `@name` even though the query and input fit.
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 1,
    "severity_calibration": 3,
    "actionability": 2,
    "reasoning": 2,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Identifies the expected critical SQL injection caused by concatenating @name into the dynamic query.",
    "precision": "The additional low-severity finding is a false positive: the stated maximum-length input fits in the declared query variable, and hypothetical future query growth is not a defect in this diff.",
    "severity_calibration": "The SQL injection is correctly marked Critical, matching the expected severity.",
    "actionability": "The injection finding gives a concrete parameterized fix and file reference. The additional finding cites the wrong line for the declaration and proposes a speculative change.",
    "reasoning": "The injection explanation correctly describes how interpolated input can alter the executed SQL. The truncation concern is unsupported by the stated lengths, which weakens the overall reasoning.",
    "format": "Uses Summary, Findings, and Verdict, with findings ordered by severity.",
    "tone": "Constructive, focused, and concise."
  },
  "matched": ["sqli"],
  "missed": [],
  "false_positives": ["Claims nvarchar(1023) may truncate a full-length @name even though the query and input fit."],
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
