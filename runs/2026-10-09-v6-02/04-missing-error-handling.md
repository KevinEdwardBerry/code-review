---
prompt_version: v6
prompt_file: prompts/code-review.v6.md
fixture: 04-missing-error-handling
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 95.0
hard_fail: true
---

# 04-missing-error-handling / v6

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
A new webhook delivery helper that POSTs a payload but ignores the HTTP response status, so failed deliveries go undetected; otherwise low-risk.

## Findings
[Medium] src/webhook.ts:6 — HTTP response status is never checked, so failed deliveries are silently treated as success
`  })
`fetch` resolves without throwing for non-2xx responses (e.g., 404, 500), and the return value is discarded, so `deliverWebhook` reports success even when the endpoint rejected or failed the request. Impact: callers cannot distinguish delivered from failed webhooks. Fix: capture the response and check `res.ok` (and/or the status code), throwing or returning an error when delivery fails, e.g. `const res = await fetch(...); if (!res.ok) throw new Error(\`Webhook failed: ${res.status}\`)`.

## Verdict
Request changes


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | The review found the only seeded issue: fetch resolves for 4xx/5xx and the Response is never checked. |
| precision | 3 | No false positives. It did not flag network failure handling, which is a must-not-flag item. |
| severity_calibration | 3 | Rated Medium, which matches the expected medium severity. |
| actionability | 2 | The fix is concrete: check res.ok and throw an error that includes the status. The citation check reported a problem: the cited line 6 is `})` and the quoted excerpt does not match the cited line. The expected range is 2-6, so the cite is only loosely aligned. Actionability is lowered for this one citation problem. |
| reasoning | 3 | The explanation is correct. It says fetch does not throw on non-2xx responses, the return value is discarded, and callers cannot tell delivered webhooks from failed ones. |
| format | 3 | Follows Summary, Findings and Verdict, with a single finding. The code excerpt is slightly malformed. |
| tone | 3 | Concise and constructive, with no filler. |

- Matched: unchecked_http_status
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "04-missing-error-handling",
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
    "recall": "The review found the only seeded issue: fetch resolves for 4xx/5xx and the Response is never checked.",
    "precision": "No false positives. It did not flag network failure handling, which is a must-not-flag item.",
    "severity_calibration": "Rated Medium, which matches the expected medium severity.",
    "actionability": "The fix is concrete: check res.ok and throw an error that includes the status. The citation check reported a problem: the cited line 6 is `})` and the quoted excerpt does not match the cited line. The expected range is 2-6, so the cite is only loosely aligned. Actionability is lowered for this one citation problem.",
    "reasoning": "The explanation is correct. It says fetch does not throw on non-2xx responses, the return value is discarded, and callers cannot tell delivered webhooks from failed ones.",
    "format": "Follows Summary, Findings and Verdict, with a single finding. The code excerpt is slightly malformed.",
    "tone": "Concise and constructive, with no filler."
  },
  "matched": [
    "unchecked_http_status"
  ],
  "missed": [],
  "false_positives": [],
  "typo_recall": null,
  "hard_fail": {
    "missed_critical": false,
    "fabricated": true,
    "missed_behavioral_typo": false
  }
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
