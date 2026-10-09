---
prompt_version: v8
prompt_file: prompts/code-review.v8.md
fixture: 03-race-condition
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: none
---

# 03-race-condition / v8

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
The new `RequestStats` uses a plain `Dictionary` mutated from `Task.Run` calls in `HandleAllAsync`, creating unsynchronized read/write paths and exposing the live dictionary via `Snapshot`.

## Findings
[High] src/counter.cs:12 — Unsynchronized check-then-act increment on shared `Dictionary`
> `        if (counts.TryGetValue(path, out var count))`
`Task.Run(() => stats.Inc(p))` at line 35 invokes `Inc` concurrently; the non-atomic TryGetValue-then-set can lose increments and concurrent dictionary writes can corrupt internal state (exceptions / torn data). Fix: guard with a `lock`, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd` + `Increment`.

[Medium] src/counter.cs:20 — Unsynchronized read of `counts` while writers mutate it
> `        return counts.TryGetValue(path, out var count) ? count : 0;`
`Count` may run concurrently with `Inc` writes; `Dictionary` reads during mutation can throw or return stale/torn results. Fix: take the same lock (or use `ConcurrentDictionary`).

[Medium] src/counter.cs:25 — `Snapshot` returns the live mutable dictionary and iterates without synchronization
> `        return counts;`
Callers get direct mutable access to shared state and any enumeration races with concurrent `Inc` writes. Fix: return a copy under the lock (e.g., `new Dictionary<string,int>(counts)` inside the lock, or `ToDictionary` on a `ConcurrentDictionary`).

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Finds all three seeded issues: unsynchronized check-then-act increment (race_in_inc), unsynchronized read (unlocked_read), and exposed live dictionary (snapshot_leak). |
| Precision | 3 | No false positives; no must-not-flag items flagged; clean diff findings only. |
| Severity calibration | 3 | Severity matches expected: high for race_in_inc, medium for unlocked_read and snapshot_leak. |
| Actionability | 3 | Each finding provides a concrete fix and correct file:line citation. |
| Reasoning | 3 | Explanations correctly describe the concurrency risk, potential exceptions/torn data, and impact for each finding. |
| Format | 3 | Follows Summary / Findings / Verdict structure, ordered by severity. |
| Tone | 3 | Constructive, concise, no filler. |

- Matched: race_in_inc, unlocked_read, snapshot_leak
- Missed: (none)
- False positives: (none)
- Typo recall: n/a

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
    "recall": "Finds all three seeded issues: unsynchronized check-then-act increment (race_in_inc), unsynchronized read (unlocked_read), and exposed live dictionary (snapshot_leak).",
    "precision": "No false positives; no must-not-flag items flagged; clean diff findings only.",
    "severity_calibration": "Severity matches expected: high for race_in_inc, medium for unlocked_read and snapshot_leak.",
    "actionability": "Each finding provides a concrete fix and correct file:line citation.",
    "reasoning": "Explanations correctly describe the concurrency risk, potential exceptions/torn data, and impact for each finding.",
    "format": "Follows Summary / Findings / Verdict structure, ordered by severity.",
    "tone": "Constructive, concise, no filler."
  },
  "matched": ["race_in_inc", "unlocked_read", "snapshot_leak"],
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
