---
prompt_version: v2
prompt_file: prompts/code-review.v2.md
fixture: 03-race-condition
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 78.3
hard_fail: fabricated
---

# 03-race-condition / v2

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
Adds a request counter that mutates a non-thread-safe `Dictionary` from concurrent `Task.Run` calls, causing races and potentially lost counts or corruption.

## Findings

**[High] src/counter.cs:35 — unsynchronized concurrent mutation of `Dictionary<string,int>`**

```csharp
await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));
```

`stats.Inc(p)` runs `counts.ContainsKey(path)` then `counts[path]++/= 1` on multiple thread-pool threads concurrently. `Dictionary` is not thread-safe: the check-then-act sequence loses increments (two threads both see "missing" and write 1), and concurrent writes can corrupt internal state or throw `IndexOutOfRangeException`/`InvalidOperationException` during rehash. `Count`/`Snapshot` can also read during a resize. Fix: use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, v) => v + 1)`, or serialize all access with a lock.

**[Medium] src/counter.cs:23 — `Snapshot()` returns the live mutable dictionary**

```csharp
public Dictionary<string, int> Snapshot()
{
    return counts;
}
```

Callers receive the internal dictionary, so they can mutate it unsynchronized and enumerate it while `Inc` is writing (throws `InvalidOperationException` during enumeration under concurrent mutation). Fix: return a copy (`new Dictionary<string,int>(counts)` under the same lock) or `IReadOnlyDictionary` built from a snapshot; with `ConcurrentDictionary`, use `ToDictionary`/`ToArray`.

## Verdict
Request changes.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Identifies the unsynchronized Inc mutation, mentions concurrent reads in Count, and flags Snapshot returning the live dictionary. |
| Precision | 1 | The review includes the code expression `counts[path]++/= 1`, which does not appear in the diff. |
| Severity calibration | 3 | The concurrent mutation is rated High and the snapshot leak Medium, both consistent with the expected severities. |
| Actionability | 2 | Suggests locking or ConcurrentDictionary and returning a copy, but does not give a separate correct line reference or targeted fix for Count. |
| Reasoning | 2 | Explains the shared concurrent access and snapshot exposure impacts, though Count's unsynchronized read is only briefly mentioned rather than developed as a distinct finding. |
| Format | 3 | Uses the required Summary, Findings, and Verdict sections in severity order. |
| Tone | 3 | Constructive and concise. |

- Matched: `unlocked_read`, `snapshot_leak`, `race_in_inc`
- Missed: none
- False positives: cites nonexistent expression `counts[path]++/= 1`
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
  "scores": {"recall": 3, "precision": 1, "severity_calibration": 3, "actionability": 2, "reasoning": 2, "format": 3, "tone": 3},
  "rationale": {
    "recall": "Identifies the unsynchronized Inc mutation, mentions concurrent reads in Count, and flags Snapshot returning the live dictionary.",
    "precision": "The review includes the code expression `counts[path]++/= 1`, which does not appear in the diff.",
    "severity_calibration": "The concurrent mutation is rated High and the snapshot leak Medium, both consistent with the expected severities.",
    "actionability": "Suggests locking or ConcurrentDictionary and returning a copy, but does not give a separate correct line reference or targeted fix for Count.",
    "reasoning": "Explains the shared concurrent access and snapshot exposure impacts, though Count's unsynchronized read is only briefly mentioned rather than developed as a distinct finding.",
    "format": "Uses the required Summary, Findings, and Verdict sections in severity order.",
    "tone": "Constructive and concise."
  },
  "matched": ["unlocked_read", "snapshot_leak", "race_in_inc"],
  "missed": [],
  "false_positives": ["Cites the nonexistent expression `counts[path]++/= 1`."],
  "typo_recall": null,
  "hard_fail": {"missed_critical": false, "fabricated": true, "missed_behavioral_typo": false}
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
