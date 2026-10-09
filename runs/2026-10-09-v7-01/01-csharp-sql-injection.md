---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 01-csharp-sql-injection
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: none
---

# 01-csharp-sql-injection / v7

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
The change adds a customer repository whose email lookup is built via string interpolation, introducing a SQL injection vulnerability.

## Findings
[Critical] src/CustomerRepository.cs:14 — SQL injection via interpolated query
`var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`
Impact: `email` is inserted directly into the SQL text, so a value like `' OR '1'='1` (or worse, a stacked statement) lets an attacker bypass the lookup filter or execute arbitrary SQL.
Fix: Use a parameterized query, e.g. `var sql = "SELECT Id, Email FROM Customers WHERE Email = @email";` and `command.Parameters.AddWithValue("@email", email);` (or `command.Parameters.Add("@email", SqlDbType.NVarChar).Value = email;`).

## Verdict
Request changes


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | The review identifies the one must-find issue, `sqli_email`, at the correct line `src/CustomerRepository.cs:14`. |
| Precision | 3 | No false positives or irrelevant flags; the review stays focused on the single SQL injection defect. |
| Severity | 3 | Correctly labels the finding as [Critical], matching the expected severity for `sqli_email`. |
| Actionability | 3 | Provides a concrete, correct fix: parameterized query with @email, and cites the exact vulnerable line. |
| Reasoning | 3 | Explanation is correct and describes the impact, including an example payload and the attack outcome. |
| Format | 3 | Follows the requested Summary / Findings / Verdict structure with a single, severity-ordered finding. |
| Tone | 3 | Constructive, concise, and free of filler. |


- Matched: sqli_email
- Missed: none
- False positives: none
- Typo recall: N/A

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
    "recall": "The review identifies the one must-find issue, `sqli_email`, at the correct line `src/CustomerRepository.cs:14`.",
    "precision": "No false positives or irrelevant flags; the review stays focused on the single SQL injection defect.",
    "severity_calibration": "Correctly labels the finding as [Critical], matching the expected severity for `sqli_email`.",
    "actionability": "Provides a concrete, correct fix: parameterized query with @email, and cites the exact vulnerable line.",
    "reasoning": "Explanation is correct and describes the impact, including an example payload and the attack outcome.",
    "format": "Follows the requested Summary / Findings / Verdict structure with a single, severity-ordered finding.",
    "tone": "Constructive, concise, and free of filler."
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
