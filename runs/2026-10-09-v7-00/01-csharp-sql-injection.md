---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 01-csharp-sql-injection
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed (judge used a separate subagent_general profile; a distinct concrete model could not be selected or verified)
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: false
---

# 01-csharp-sql-injection / v7

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed (judge used a separate subagent_general profile; a distinct concrete model could not be selected or verified))

## AI response
## Summary
New repository method builds a SQL query by interpolating user input, introducing a critical SQL injection vulnerability.

## Findings
- [Critical] src/CustomerRepository.cs:14 — SQL injection via string-interpolated query
  `var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`
  The `email` parameter is inserted directly into the SQL text, so an attacker-controlled value (e.g., `' OR '1'='1`) can alter the query, exfiltrate arbitrary rows, or execute injected statements. Fix: use a parameterized query, e.g.
  ```csharp
  var sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
  await using var command = new SqlCommand(sql, connection);
  command.Parameters.AddWithValue("@email", email);
  ```

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | The review finds the only seeded issue, sqli_email, at src/CustomerRepository.cs:14. |
| precision | 3 | There are no false positives. The review does not flag any must-not-flag items and reports one finding anchored to the vulnerable line. |
| severity_calibration | 3 | The review rates the issue Critical, which matches the expected severity. |
| actionability | 3 | The review gives a concrete parameterized-query fix with a code snippet and the correct file:line. CITATION_CHECK reports ok. It uses AddWithValue instead of an explicit database type, which is a minor point. |
| reasoning | 3 | The review correctly explains that the attacker-controlled email is inserted into the SQL text. It gives an example payload and describes the impact: altering the query, exfiltrating rows, or running injected statements. |
| format | 3 | The review follows Summary / Findings / Verdict and has a single finding, so ordering by severity is trivially satisfied. |
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
    "precision": "There are no false positives. The review does not flag any must-not-flag items and reports one finding anchored to the vulnerable line.",
    "severity_calibration": "The review rates the issue Critical, which matches the expected severity.",
    "actionability": "The review gives a concrete parameterized-query fix with a code snippet and the correct file:line. CITATION_CHECK reports ok. It uses AddWithValue instead of an explicit database type, which is a minor point.",
    "reasoning": "The review correctly explains that the attacker-controlled email is inserted into the SQL text. It gives an example payload and describes the impact: altering the query, exfiltrating rows, or running injected statements.",
    "format": "The review follows Summary / Findings / Verdict and has a single finding, so ordering by severity is trivially satisfied.",
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
