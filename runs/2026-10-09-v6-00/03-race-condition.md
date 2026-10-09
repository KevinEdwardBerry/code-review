---
prompt_version: v6
prompt_file: prompts/code-review.v6.md
fixture: 03-race-condition
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}
---

# 03-race-condition / v6

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
A new request-statistics counter that performs unsynchronized concurrent access to a shared `Dictionary`, making it unsafe under the demonstrated parallel workload.

## Findings
- **[High] src/counter.cs:35 — Concurrent unsynchronized mutation of shared `Dictionary`**
  `await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));`
  `HandleAllAsync` invokes `stats.Inc` on multiple threads simultaneously, but `counts` is a plain `Dictionary<string,int>` mutated without synchronization. `Dictionary` is not thread-safe for concurrent writes; this can corrupt internal state, lose increments, or throw. Fix: use `ConcurrentDictionary<string,int>` with `AddOrUpdate`, or guard `Inc` with a `lock`.

- **[Medium] src/counter.cs:20 — Unsynchronized read of `counts` during concurrent writes**
  `return counts.TryGetValue(path, out var count) ? count : 0;`
  `Total` calls `Count`, which reads the dictionary with no synchronization; reading a `Dictionary` while another thread writes is undefined and may throw or return stale/corrupt results. Fix: same as above — `ConcurrentDictionary` or a shared lock.

- **[Medium] src/counter.cs:25 — `Snapshot` exposes the live mutable dictionary**
  `return counts;`
  Returns the internal dictionary by reference, so callers can mutate internal state and can iterate it while `Inc` writes, which can throw `InvalidOperationException`. Fix: return a copy (e.g., `new Dictionary<string,int>(counts)` under the lock) or an immutable/read-only snapshot.

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | All three expected issues are identified: the concurrent unsynchronized mutation of the shared Dictionary, the unsynchronized Count read, and the Snapshot returning the live internal dictionary. |
| precision | 3 | No false positives or unrelated findings; each identified issue corresponds to an expected defect. |
| severity_calibration | 3 | The high race condition and two medium issues are correctly ranked, matching the expected severity assignments. |
| actionability | 3 | Concrete fixes are provided for each finding with correct file:line citations, including ConcurrentDictionary/AddOrUpdate, locking, and returning a copy. |
| reasoning | 3 | Explanations are correct and describe concrete impacts: lost increments, dictionary corruption, undefined concurrent reads, and InvalidOperationException during enumeration. |
| format | 3 | Follows the requested Summary / Findings / Verdict structure and orders findings by severity. |
| tone | 3 | Constructive, concise, and focused on actionable feedback. |

- Matched: race_in_inc, unlocked_read, snapshot_leak
- Missed: None
- False positives: None
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
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
    "recall": "All three expected issues are identified: the concurrent unsynchronized mutation of the shared Dictionary, the unsynchronized Count read, and the Snapshot returning the live internal dictionary.",
    "precision": "No false positives or unrelated findings; each identified issue corresponds to an expected defect.",
    "severity_calibration": "The high race condition and two medium issues are correctly ranked, matching the expected severity assignments.",
    "actionability": "Concrete fixes are provided for each finding with correct file:line citations, including ConcurrentDictionary/AddOrUpdate, locking, and returning a copy.",
    "reasoning": "Explanations are correct and describe concrete impacts: lost increments, dictionary corruption, undefined concurrent reads, and InvalidOperationException during enumeration.",
    "format": "Follows the requested Summary / Findings / Verdict structure and orders findings by severity.",
    "tone": "Constructive, concise, and focused on actionable feedback."
  },
  "matched": [
    "race_in_inc",
    "unlocked_read",
    "snapshot_leak"
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
