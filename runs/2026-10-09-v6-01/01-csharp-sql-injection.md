---
prompt_version: v6
prompt_file: prompts/code-review.v6.md
fixture: 01-csharp-sql-injection
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: false
---

# 01-csharp-sql-injection / v6

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
Adds a new `CustomerRepository` with a SQL injection vulnerability in email lookup — high-risk change.

## Findings

[Critical] src/CustomerRepository.cs:14 — SQL injection via string-interpolated query
```
var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";
```
The `email` parameter is interpolated directly into the SQL text. An attacker can supply input like `' OR '1'='1` to bypass the email filter or `'; DROP TABLE Customers;--` to execute arbitrary statements, depending on the SQL Server configuration. This exposes customer data and allows destructive queries.

Fix: use a parameterized query:
```csharp
var sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
await using var command = new SqlCommand(sql, connection);
command.Parameters.AddWithValue("@email", email);
```

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Found the critical SQL injection vulnerability in the interpolated email query. |
| Precision | 3 | Reports only the expected issue and does not flag acceptable implementation details. |
| Severity calibration | 3 | Correctly rates the issue Critical, matching the expected severity. |
| Actionability | 3 | Provides the correct file and line, identifies the unsafe interpolation, and gives a concrete parameterized-query fix. |
| Reasoning correctness | 3 | Explains how attacker-controlled input can alter the predicate or execute additional statements and describes the resulting impact. |
| Format adherence | 3 | Follows the requested Summary / Findings / Verdict structure with the finding in the expected section. |
| Tone and concision | 3 | Constructive, focused, and concise. |

- Matched: sqli_email
- Missed: None
- False positives: None
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-csharp-sql-injection",
  "scores": {"recall": 3, "precision": 3, "severity_calibration": 3, "actionability": 3, "reasoning": 3, "format": 3, "tone": 3},
  "rationale": {"recall": "Found the critical SQL injection vulnerability in the interpolated email query.", "precision": "Reports only the expected issue and does not flag acceptable implementation details.", "severity_calibration": "Correctly rates the issue Critical, matching the expected severity.", "actionability": "Provides the correct file and line, identifies the unsafe interpolation, and gives a concrete parameterized-query fix.", "reasoning": "Explains how attacker-controlled input can alter the predicate or execute additional statements and describes the resulting impact.", "format": "Follows the requested Summary / Findings / Verdict structure with the finding in the expected section.", "tone": "Constructive, focused, and concise."},
  "matched": ["sqli_email"], "missed": [], "false_positives": [], "typo_recall": null,
  "hard_fail": {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
Citation check: ok (1 citation checked).