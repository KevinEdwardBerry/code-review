---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 01-csharp-sql-injection
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 78.3
hard_fail: false
---

# 01-csharp-sql-injection / v1

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
# Code Review: CustomerRepository

## Critical

**1. SQL Injection (blocking)** — `src/CustomerRepository.cs:15`

```csharp
var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";
```

`email` is interpolated directly into the SQL string. An attacker can supply a crafted email such as `' OR '1'='1` to bypass filters, or worse, run stacked queries depending on driver settings. This must be parameterized:

```csharp
const string sql = "SELECT Id, Email FROM Customers WHERE Email = @Email";
await using var command = new SqlCommand(sql, connection);
command.Parameters.Add("@Email", SqlDbType.NVarChar, 256).Value = email;
```

Note: specifying `SqlDbType` and length avoids parameter-size mismatches that can hurt plan cache reuse for `NVarChar` columns.

## Suggestions

**2. Implicit `IDisposable` behavior with `await using`** — lines 11, 16, 17

This is correct (`SqlConnection`, `SqlCommand`, `SqlDataReader` all support async dispose), so no change needed — but worth confirming the project targets a framework where `IAsyncDisposable` is implemented on these types (netstandard2.1+/net5+). If the package version is old, `await using` won't compile.

**3. `ExecuteReaderAsync` without `CommandBehavior.SingleRow`** — line 17

Since the method returns at most one `Customer`, passing `CommandBehavior.SingleRow | CommandBehavior.SingleResult` lets the provider optimize and documents intent. Optional, but cheap.

**4. Uniqueness assumption on `Email`** — line 15

`FindByEmailAsync` silently returns the *first* matching row. If `Email` isn't backed by a unique constraint in the database, duplicates produce nondeterministic results. Recommend adding `WHERE ... AND ...` semantics clarification or at minimum documenting/enforcing uniqueness at the schema level.

**5. Missing email validation** — line 8

Not strictly required since parameterization makes it safe, but a cheap guard (`string.IsNullOrWhiteSpace` → `ArgumentException`) avoids useless DB round-trips and clearer error semantics.

**6. Minor: no `ConfigureAwait(false)` / library conventions**

If this is shared library code, consider whether the codebase convention calls for `ConfigureAwait(false)`. Skipped in many modern ASP.NET Core codebases; check project norms.

## Verdict

**Request changes.** The SQL injection vulnerability is a hard blocker — everything else is secondary polish. The structure (sealed types, async throughout, proper disposal, nullable return) is otherwise solid.


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | The review finds the single must-find issue, SQL injection through the interpolated `email` in `FindByEmailAsync`. It rates it Critical and calls it blocking. |
| Precision | 1 | Suggestion 2 discusses `await using` async disposal, which is a must-not-flag area, although it concludes that no change is needed. Suggestions 3 to 6 (SingleRow, uniqueness, validation, ConfigureAwait) are speculative noise that the diff doesn't support. None of them is a real defect. |
| Severity calibration | 3 | The injection is correctly marked Critical and blocking. The other items are Suggestions, which is appropriate for their weight. |
| Actionability | 2 | It gives a concrete parameterized-query fix with a typed `SqlDbType` parameter. The line citations are slightly off: the vulnerable statement is on line 14 and the review says 15, and several other cited lines are also shifted by one. The citation check reports ok, so this only lowers the score slightly. |
| Reasoning correctness | 3 | It explains the injection correctly with an example payload, and it covers the stacked-query risk and the plan-cache effect of the parameter type. |
| Format adherence | 2 | It has a Critical section, a Suggestions section and a Verdict, in severity order. It has no explicit Summary section, and the headings differ from the requested Summary / Findings / Verdict. |
| Tone and concision | 2 | The tone is constructive, but the five low-value suggestions add filler and dilute the one important finding. |

- Matched: sqli_email
- Missed: none
- False positives: 
  - Suggestion 2 discusses `await using` / IAsyncDisposable, a must-not-flag area, though it says no change is needed
  - Suggestion 3: unnecessary CommandBehavior.SingleRow suggestion
  - Suggestion 4: speculative uniqueness concern, with a muddled recommendation
  - Suggestion 5: missing email validation, speculative
  - Suggestion 6: ConfigureAwait speculation
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "01-csharp-sql-injection",
  "scores": {
    "recall": 3,
    "precision": 1,
    "severity_calibration": 3,
    "actionability": 2,
    "reasoning": 3,
    "format": 2,
    "tone": 2
  },
  "rationale": {
    "recall": "The review finds the single must-find issue, SQL injection through the interpolated `email` in `FindByEmailAsync`. It rates it Critical and calls it blocking.",
    "precision": "Suggestion 2 discusses `await using` async disposal, which is a must-not-flag area, although it concludes that no change is needed. Suggestions 3 to 6 (SingleRow, uniqueness, validation, ConfigureAwait) are speculative noise that the diff doesn't support. None of them is a real defect.",
    "severity_calibration": "The injection is correctly marked Critical and blocking. The other items are Suggestions, which is appropriate for their weight.",
    "actionability": "It gives a concrete parameterized-query fix with a typed `SqlDbType` parameter. The line citations are slightly off: the vulnerable statement is on line 14 and the review says 15, and several other cited lines are also shifted by one. The citation check reports ok, so this only lowers the score slightly.",
    "reasoning": "It explains the injection correctly with an example payload, and it covers the stacked-query risk and the plan-cache effect of the parameter type.",
    "format": "It has a Critical section, a Suggestions section and a Verdict, in severity order. It has no explicit Summary section, and the headings differ from the requested Summary / Findings / Verdict.",
    "tone": "The tone is constructive, but the five low-value suggestions add filler and dilute the one important finding."
  },
  "matched": [
    "sqli_email"
  ],
  "missed": [],
  "false_positives": [
    "Suggestion 2 discusses `await using` / IAsyncDisposable, a must-not-flag area, though it says no change is needed",
    "Suggestion 3: unnecessary CommandBehavior.SingleRow suggestion",
    "Suggestion 4: speculative uniqueness concern, with a muddled recommendation",
    "Suggestion 5: missing email validation, speculative",
    "Suggestion 6: ConfigureAwait speculation"
  ],
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
