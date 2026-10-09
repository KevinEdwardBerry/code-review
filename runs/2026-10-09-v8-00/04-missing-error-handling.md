---
prompt_version: v8
prompt_file: prompts/code-review.v8.md
fixture: 04-missing-error-handling
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: none
---

# 04-missing-error-handling / v8

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
Adds a webhook delivery helper that POSTs a payload via fetch; low risk but it silently ignores non-2xx responses.

## Findings

[Medium] src/webhook.ts:2 — HTTP error responses are not checked, so failed deliveries are reported as success
```
  await fetch(url, {
```
`fetch` only rejects on network failures; a 4xx/5xx response resolves normally, so the caller cannot detect a failed webhook delivery. Fix: capture the response and throw or return a result when `!res.ok` (e.g., `const res = await fetch(...); if (!res.ok) throw new Error(\`Webhook failed: ${res.status}\`)`).

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Identifies the single seeded `unchecked_http_status` finding in src/webhook.ts. |
| Precision | 3 | No false positives; does not incorrectly flag network-failure propagation. |
| Severity calibration | 3 | Correctly labels the issue Medium, matching the expected severity. |
| Actionability | 3 | Provides a concrete fix (check `!res.ok` and throw) and cites the correct file and line. |
| Reasoning | 3 | Correctly explains that fetch resolves for 4xx/5xx and why this is a problem. |
| Format | 3 | Follows Summary / Findings / Verdict structure and orders the finding by severity. |
| Tone | 3 | Concise, constructive, and focused on the issue. |

- Matched: unchecked_http_status
- Missed: (none)
- False positives: (none)
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "04-missing-error-handling",
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
    "recall": "Identifies the single seeded `unchecked_http_status` finding in src/webhook.ts.",
    "precision": "No false positives; does not incorrectly flag network-failure propagation.",
    "severity_calibration": "Correctly labels the issue Medium, matching the expected severity.",
    "actionability": "Provides a concrete fix (check `!res.ok` and throw) and cites the correct file and line.",
    "reasoning": "Correctly explains that fetch resolves for 4xx/5xx and why this is a problem.",
    "format": "Follows Summary / Findings / Verdict structure and orders the finding by severity.",
    "tone": "Concise, constructive, and focused on the issue."
  },
  "matched": ["unchecked_http_status"],
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
