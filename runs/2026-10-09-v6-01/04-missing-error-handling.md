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
A minimal webhook delivery helper; the only demonstrated defect is that HTTP failures are silently ignored.

## Findings
[Medium] src/webhook.ts:6 — Response status never checked, so failed deliveries are silently reported as success
```
  })
```
`deliverWebhook` resolves successfully whenever `fetch` itself does not throw, meaning HTTP error responses (4xx/5xx, e.g., a 500 from the receiver or a 404 from a bad URL) are indistinguishable from a successful delivery. Callers cannot detect or retry failed deliveries. Fix: capture the response and throw or return its status when `!res.ok`, e.g. `const res = await fetch(...); if (!res.ok) throw new Error(\`Webhook delivery failed: ${res.status}\`)`.

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Identifies the expected unchecked HTTP status defect. |
| Precision | 3 | No findings beyond the expected defect. |
| Severity calibration | 3 | Labels the finding Medium, matching the expected severity. |
| Actionability | 2 | Provides a concrete fix, but the quote does not match the cited line according to the citation checker. |
| Reasoning correctness | 3 | Correctly explains that fetch can resolve with an HTTP error response, causing failed deliveries to appear successful. |
| Format adherence | 3 | Uses clear Summary, Findings, and Verdict sections. |
| Tone and concision | 3 | Focused and constructive. |

- Matched: unchecked_http_status
- Missed: None
- False positives: None
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{"fixture":"04-missing-error-handling","scores":{"recall":3,"precision":3,"severity_calibration":3,"actionability":2,"reasoning":3,"format":3,"tone":3},"rationale":{"recall":"Identifies the expected unchecked HTTP status defect.","precision":"No findings beyond the defect in the expected review.","severity_calibration":"Labels the finding Medium, matching the expected severity.","actionability":"Gives a concrete fix, but the citation checker reports that the quoted excerpt does not match the cited line, reducing actionability.","reasoning":"Correctly explains that fetch can resolve with an HTTP error response, causing failed deliveries to appear successful.","format":"Uses clear Summary, Findings, and Verdict sections.","tone":"Focused and constructive."},"matched":["unchecked_http_status"],"missed":[],"false_positives":[],"typo_recall":null,"hard_fail":{"missed_critical":false,"fabricated":true,"missed_behavioral_typo":false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
Citation check: failed (quote for `src/webhook.ts:6` does not match the cited line); judge hard-fail `fabricated` is true.