---
prompt_version: v6
prompt_file: prompts/code-review.v6.md
fixture: 03-race-condition
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 95.0
hard_fail: false
---

# 03-race-condition / v6

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
The new `RequestStats` counter is used from multiple threads by `HandleAllAsync` but wraps a plain `Dictionary` with no synchronization, so all reads and writes are racy.

## Findings
[High] src/counter.cs:12 — unsynchronized read/write of shared `counts` during concurrent `Inc`
`        if (counts.TryGetValue(path, out var count))`
`Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))))` invokes `Inc` on multiple threads over a non-thread-safe `Dictionary`. Races cause lost increments and can corrupt the dictionary's internal buckets (leading to exceptions or hangs). Fix: use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or guard all accesses with a `lock`.

[High] src/counter.cs:20 — unsynchronized read of `counts` in `Count`
`        return counts.TryGetValue(path, out var count) ? count : 0;`
`Total` can be called while `HandleAllAsync` is mutating the dictionary; a `TryGetValue` concurrent with a write/resize is undefined and may throw or return stale/corrupted results. Fix: same as above (`ConcurrentDictionary` or lock on every access).

[Medium] src/counter.cs:25 — `Snapshot` returns the live mutable dictionary
`        return counts;`
Callers receive the internal `Dictionary`, so they can observe or mutate it concurrently with `Inc`, reintroducing races and breaking encapsulation. Fix: return a copy (`new Dictionary<string,int>(counts)` under the lock / `ConcurrentDictionary.ToArray()`-based snapshot).

## Verdict
Request changes


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | All three must-find items are found: race_in_inc at line 12, unlocked_read at line 20, and snapshot_leak at line 25. |
| precision | 3 | No false positives. The review cites HandleAllAsync only as evidence for the race, which is allowed, and it does not flag Dictionary usage or the method names. |
| severity_calibration | 2 | race_in_inc is High, which matches. snapshot_leak is Medium, which matches. unlocked_read is rated High but expected Medium, so it is one level off. |
| actionability | 3 | Each finding has the correct file:line and a concrete fix (lock, ConcurrentDictionary.AddOrUpdate, or return a copy under the lock). CITATION_CHECK is ok. |
| reasoning | 3 | The explanations are correct. They cover lost increments, dictionary corruption, and the way a concurrent read can interleave with a write or resize. They also tie the races to the concurrent call site. |
| format | 3 | Follows Summary / Findings / Verdict and orders findings by severity. |
| tone | 3 | Concise, constructive, and free of filler. |

- Matched: race_in_inc, unlocked_read, snapshot_leak
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
  "scores": {
    "recall": 3,
    "precision": 3,
    "severity_calibration": 2,
    "actionability": 3,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "All three must-find items are found: race_in_inc at line 12, unlocked_read at line 20, and snapshot_leak at line 25.",
    "precision": "No false positives. The review cites HandleAllAsync only as evidence for the race, which is allowed, and it does not flag Dictionary usage or the method names.",
    "severity_calibration": "race_in_inc is High, which matches. snapshot_leak is Medium, which matches. unlocked_read is rated High but expected Medium, so it is one level off.",
    "actionability": "Each finding has the correct file:line and a concrete fix (lock, ConcurrentDictionary.AddOrUpdate, or return a copy under the lock). CITATION_CHECK is ok.",
    "reasoning": "The explanations are correct. They cover lost increments, dictionary corruption, and the way a concurrent read can interleave with a write or resize. They also tie the races to the concurrent call site.",
    "format": "Follows Summary / Findings / Verdict and orders findings by severity.",
    "tone": "Concise, constructive, and free of filler."
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
