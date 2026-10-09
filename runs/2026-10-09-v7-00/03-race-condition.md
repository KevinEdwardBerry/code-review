---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 03-race-condition
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed (judge used a separate subagent_general profile; a distinct concrete model could not be selected or verified)
judge_profile: subagent_general
weighted_score: 100.0
hard_fail: false
---

# 03-race-condition / v7

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed (judge used a separate subagent_general profile; a distinct concrete model could not be selected or verified))

## AI response
## Summary
The change adds a request counter that is shared across concurrent tasks without synchronization, producing race conditions and exposing mutable internal state.

## Findings

[High] src/counter.cs:13 — Unsynchronized write to shared `Dictionary` under concurrent `Inc` calls
> `counts[path] = count + 1;`
`HandleAllAsync` invokes `stats.Inc` concurrently via `Task.Run`/`Task.WhenAll`. `Dictionary` is not thread-safe; concurrent check-then-set on lines 12–15 loses increments and can corrupt internal state, permanently under-counting requests.
Fix: guard all access with a `lock`, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd`.

[Medium] src/counter.cs:20 — Unsynchronized read of shared `Dictionary`
> `return counts.TryGetValue(path, out var count) ? count : 0;`
`Count` reads the dictionary while other tasks may be writing it via `Inc`; concurrent read-during-write on `Dictionary` is not guaranteed safe and can return torn or stale results.
Fix: protect reads with the same lock used for writes, or use `ConcurrentDictionary` (`TryGetValue` is then safe).

[Medium] src/counter.cs:25 — `Snapshot` returns the live mutable dictionary
> `return counts;`
Callers receive the internal dictionary: they can mutate it unsafely and enumerate it while writes occur, causing `InvalidOperationException` or corrupted counts.
Fix: return a copy under the lock (e.g., `new Dictionary<string,int>(counts)` inside `lock`, or `ToDictionary` on a `ConcurrentDictionary`).

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | The review found all three must-find items, each anchored to its own line: race_in_inc at line 13, unlocked_read at line 20, and snapshot_leak at line 25. |
| precision | 3 | There are no false positives. The review doesn't flag the use of Dictionary or the method names. It cites RequestHandler only as evidence for the race. |
| severity_calibration | 3 | The severities match the expected ones: High for Inc, Medium for Count, and Medium for Snapshot. |
| actionability | 3 | Each finding has a concrete fix (lock or ConcurrentDictionary.AddOrUpdate, a copy made under the lock) and a correct file:line. CITATION_CHECK reports ok. |
| reasoning | 3 | The explanations are correct and cover impact: lost increments, possible corruption, unsafe reads during writes, and callers mutating or enumerating the live dictionary. |
| format | 3 | The review follows Summary / Findings / Verdict, with findings ordered by severity. |
| tone | 3 | The review is concise and constructive, with no filler. |

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
    "severity_calibration": 3,
    "actionability": 3,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "The review found all three must-find items, each anchored to its own line: race_in_inc at line 13, unlocked_read at line 20, and snapshot_leak at line 25.",
    "precision": "There are no false positives. The review doesn't flag the use of Dictionary or the method names. It cites RequestHandler only as evidence for the race.",
    "severity_calibration": "The severities match the expected ones: High for Inc, Medium for Count, and Medium for Snapshot.",
    "actionability": "Each finding has a concrete fix (lock or ConcurrentDictionary.AddOrUpdate, a copy made under the lock) and a correct file:line. CITATION_CHECK reports ok.",
    "reasoning": "The explanations are correct and cover impact: lost increments, possible corruption, unsafe reads during writes, and callers mutating or enumerating the live dictionary.",
    "format": "The review follows Summary / Findings / Verdict, with findings ordered by severity.",
    "tone": "The review is concise and constructive, with no filler."
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
