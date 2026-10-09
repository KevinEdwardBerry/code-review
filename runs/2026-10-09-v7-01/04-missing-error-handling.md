---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 04-missing-error-handling
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: none
---

# 04-missing-error-handling / v7

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
Adds a small helper that POSTs a payload to a URL; the only demonstrated defect is that it silently ignores HTTP-level delivery failures.

## Findings
[Medium] src/webhook.ts:2 — HTTP error responses are silently treated as successful delivery
`  await fetch(url, {`
`fetch` resolves without throwing on non-2xx responses (4xx/5xx), so `deliverWebhook` reports success to callers even when the webhook was rejected, making failures invisible. Check `res.ok`/`res.status` and throw or return an error so callers can handle failed deliveries.

## Verdict
Approve with nits


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | The review correctly identifies the seeded `unchecked_http_status` issue in deliverWebhook. |
| Precision | 3 | No false positives or must-not-flag items are raised. |
| Severity | 3 | The finding is correctly rated Medium, matching the expected severity. |
| Actionability | 3 | The review gives a concrete fix (check res.ok/res.status and throw/return an error) and cites src/webhook.ts:2. |
| Reasoning | 3 | The explanation correctly states that fetch resolves on 4xx/5xx and that failures become invisible to callers. |
| Format | 3 | Follows the requested Summary / Findings / Verdict structure with findings ordered by severity. |
| Tone | 3 | Constructive, concise, and free of filler. |


- Matched: unchecked_http_status
- Missed: none
- False positives: none
- Typo recall: N/A

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
    "recall": "The review correctly identifies the seeded `unchecked_http_status` issue in deliverWebhook.",
    "precision": "No false positives or must-not-flag items are raised.",
    "severity_calibration": "The finding is correctly rated Medium, matching the expected severity.",
    "actionability": "The review gives a concrete fix (check res.ok/res.status and throw/return an error) and cites src/webhook.ts:2.",
    "reasoning": "The explanation correctly states that fetch resolves on 4xx/5xx and that failures become invisible to callers.",
    "format": "Follows the requested Summary / Findings / Verdict structure with findings ordered by severity.",
    "tone": "Constructive, concise, and free of filler."
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
