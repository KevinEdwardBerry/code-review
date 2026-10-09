---
prompt_version: v8
prompt_file: prompts/code-review.v8.md
fixture: 01-csharp-sql-injection
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: none
---

# 01-csharp-sql-injection / v8

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
High-risk change: `FindByEmailAsync` builds its SQL query via string interpolation of user-supplied input, exposing the repository to SQL injection.

## Findings

- [Critical] src/CustomerRepository.cs:14 — SQL injection via interpolated email parameter
  ```
  var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";
  ```
  The `email` argument is concatenated directly into the query text, so a caller supplying input like `' OR '1'='1` (or `'; DROP TABLE Customers;--`) alters the executed SQL. This can leak arbitrary customer data or execute destructive statements. Fix by parameterizing the query:
  ```csharp
  const string sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
  await using var command = new SqlCommand(sql, connection);
  command.Parameters.Add(new SqlParameter("@email", SqlDbType.NVarChar, 256) { Value = email });
  ```

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | The review finds the only seeded issue, sqli_email, at the expected location and with the correct description. |
| Precision | 3 | The review contains only the one genuine finding with no false positives or unrelated flagged items. |
| Severity calibration | 3 | The finding is correctly ranked as Critical, matching the expected severity for SQL injection. |
| Actionability | 3 | The review provides a concrete parameterized fix with the correct file:line reference. |
| Reasoning | 3 | The explanation correctly identifies the injection vector and impact, including an example payload and how to remediate. |
| Format | 3 | The review follows the requested Summary / Findings / Verdict structure and is ordered by severity. |
| Tone | 3 | The tone is professional, concise, and constructive. |

- Matched: sqli_email
- Missed: (none)
- False positives: (none)
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-csharp-sql-injection",
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
    "recall": "The review finds the only seeded issue, sqli_email, at the expected location and with the correct description.",
    "precision": "The review contains only the one genuine finding with no false positives or unrelated flagged items.",
    "severity_calibration": "The finding is correctly ranked as Critical, matching the expected severity for SQL injection.",
    "actionability": "The review provides a concrete parameterized fix with the correct file:line reference.",
    "reasoning": "The explanation correctly identifies the injection vector and impact, including an example payload and how to remediate.",
    "format": "The review follows the requested Summary / Findings / Verdict structure and is ordered by severity.",
    "tone": "The tone is professional, concise, and constructive."
  },
  "matched": ["sqli_email"],
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
