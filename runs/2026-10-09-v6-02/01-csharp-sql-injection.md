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
New `CustomerRepository` that builds a SQL query via string interpolation, introducing a SQL injection vulnerability.

## Findings
[Critical] src/CustomerRepository.cs:14 — SQL injection via interpolated `email`
> `var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`

`email` is an unvalidated caller-supplied string interpolated directly into the SQL text. A value such as `' OR '1'='1` (or a `'; DROP TABLE ...--` payload) alters the query, allowing arbitrary data reads or destructive statements depending on connection permissions. Fix by parameterizing:

```csharp
const string sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
await using var command = new SqlCommand(sql, connection);
command.Parameters.AddWithValue("@email", email);
```

## Verdict
Request changes


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | The review finds the only seeded issue, sqli_email, at src/CustomerRepository.cs:14. |
| precision | 3 | There are no false positives. It does not flag any of the must-not-flag items. |
| severity_calibration | 3 | It rates the issue Critical, which matches the expected critical severity. |
| actionability | 3 | The fix is concrete: a parameterized query with a SqlCommand parameter. The file:line citation is correct and CITATION_CHECK reports ok. AddWithValue does not set an explicit database type, but this is minor. |
| reasoning | 3 | The explanation is correct. It gives example payloads and says the impact is arbitrary data reads or destructive statements. |
| format | 3 | It follows the Summary / Findings / Verdict structure. |
| tone | 3 | The review is concise and constructive, with no filler. |

- Matched: sqli_email
- Missed: none
- False positives: none
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
    "recall": "The review finds the only seeded issue, sqli_email, at src/CustomerRepository.cs:14.",
    "precision": "There are no false positives. It does not flag any of the must-not-flag items.",
    "severity_calibration": "It rates the issue Critical, which matches the expected critical severity.",
    "actionability": "The fix is concrete: a parameterized query with a SqlCommand parameter. The file:line citation is correct and CITATION_CHECK reports ok. AddWithValue does not set an explicit database type, but this is minor.",
    "reasoning": "The explanation is correct. It gives example payloads and says the impact is arbitrary data reads or destructive statements.",
    "format": "It follows the Summary / Findings / Verdict structure.",
    "tone": "The review is concise and constructive, with no filler."
  },
  "matched": [
    "sqli_email"
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
