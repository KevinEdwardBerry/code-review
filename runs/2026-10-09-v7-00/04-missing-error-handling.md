---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 04-missing-error-handling
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed (judge used a separate subagent_general profile; a distinct concrete model could not be selected or verified)
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: false
---

# 04-missing-error-handling / v7

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed (judge used a separate subagent_general profile; a distinct concrete model could not be selected or verified))

## AI response
## Summary
A minimal webhook delivery helper; the only demonstrated defect is that HTTP error responses are silently treated as successful deliveries.

## Findings
[Medium] src/webhook.ts:2 — HTTP error responses are ignored
`  await fetch(url, {`
`fetch` resolves without throwing on 4xx/5xx statuses, so `deliverWebhook` returns successfully even when the webhook was rejected, making delivery failures indistinguishable from success. Check `response.ok` (or the status code) and throw/retry on non-2xx responses.

## Verdict
Approve with nits

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | The review found the only must-find issue, the unchecked HTTP status. It names the same defect at the same location. |
| precision | 3 | There are no false positives. The review did not flag network-failure handling, which is on the must-not-flag list. |
| severity_calibration | 3 | The review rates it Medium, which matches the expected medium severity. |
| actionability | 3 | The fix is concrete: check response.ok or the status and throw. The citation src/webhook.ts:2 is valid, and CITATION_CHECK reports ok. |
| reasoning | 3 | The explanation is correct. fetch resolves on 4xx/5xx, so the function reports success when the endpoint rejected the webhook, and failures look like successes. The review also states the impact. It does not say the thrown error should include the status, which is a minor gap. |
| format | 3 | The review follows Summary / Findings / Verdict. It has a single finding, so ordering is not an issue. |
| tone | 3 | The review is concise, constructive and free of filler. |

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
    "actionability": 3,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "The review found the only must-find issue, the unchecked HTTP status. It names the same defect at the same location.",
    "precision": "There are no false positives. The review did not flag network-failure handling, which is on the must-not-flag list.",
    "severity_calibration": "The review rates it Medium, which matches the expected medium severity.",
    "actionability": "The fix is concrete: check response.ok or the status and throw. The citation src/webhook.ts:2 is valid, and CITATION_CHECK reports ok.",
    "reasoning": "The explanation is correct. fetch resolves on 4xx/5xx, so the function reports success when the endpoint rejected the webhook, and failures look like successes. The review also states the impact. It does not say the thrown error should include the status, which is a minor gap.",
    "format": "The review follows Summary / Findings / Verdict. It has a single finding, so ordering is not an issue.",
    "tone": "The review is concise, constructive and free of filler."
  },
  "matched": [
    "unchecked_http_status"
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
