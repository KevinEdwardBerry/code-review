---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 01-csharp-sql-injection
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: false
---

# 01-csharp-sql-injection / v4

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
New repository class introduces a critical SQL injection vulnerability by interpolating user input directly into a query.

## Findings

- [Critical] src/CustomerRepository.cs:14 — SQL injection via string interpolation
  - Evidence: ``var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";``
  - Impact: The `email` parameter is concatenated into the SQL text unescaped, allowing arbitrary SQL execution (data exfiltration, modification, or authentication bypass depending on caller input).
  - Fix: Use a parameterized query, e.g.:
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
| Recall | 3 | Identifies the sole seeded SQL injection vulnerability at the interpolated email value. |
| Precision | 3 | Reports only the expected injection finding; no unsupported issues are raised. |
| Severity calibration | 3 | Correctly rates the vulnerability Critical, matching the expected severity. |
| Actionability | 3 | Provides the correct file and line, a concrete parameterized-query fix, and binds the email parameter. |
| Reasoning | 3 | Accurately explains that caller-controlled input enters SQL text and can alter the query; the stated impacts are plausible. |
| Format | 3 | Uses the required ordered Summary, Findings, and Verdict sections. |
| Tone | 3 | Concise, professional, and constructive. |

- Matched: `sqli_email`
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-csharp-sql-injection",
  "scores": {"recall": 3, "precision": 3, "severity_calibration": 3, "actionability": 3, "reasoning": 3, "format": 3, "tone": 3},
  "rationale": {
    "recall": "Identifies the sole seeded SQL injection vulnerability at the interpolated email value.",
    "precision": "Reports only the expected injection finding; no unsupported issues are raised.",
    "severity_calibration": "Correctly rates the vulnerability Critical, matching the expected severity.",
    "actionability": "Provides the correct file and line, a concrete parameterized-query fix, and binds the email parameter.",
    "reasoning": "Accurately explains that caller-controlled input enters SQL text and can alter the query; the stated impacts are plausible.",
    "format": "Uses the required ordered Summary, Findings, and Verdict sections.",
    "tone": "Concise, professional, and constructive."
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
