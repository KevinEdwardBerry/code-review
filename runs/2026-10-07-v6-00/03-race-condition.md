---
prompt_version: v6
prompt_file: prompts/code-review.v6.md
fixture: 03-race-condition
date: 2026-10-07
reviewer_model: unknown
reviewer_profile: subagent_explore
judge_model: unknown
judge_profile: subagent_general
weighted_score: 95.0
hard_fail: none
---

# 03-race-condition / v6

## Models
- Reviewer: subagent_explore (unknown)
- Judge: subagent_general (unknown)

## AI response
### Summary
The change adds a `RequestStats` class wrapping a `Dictionary<string, int>` to count requests per path. The core counting logic is correct, but `Snapshot()` leaks the internal mutable dictionary and the class is unsafe under concurrent access, which is a realistic scenario for per-request statistics.

### Findings

- **medium** src/counter.cs:27 — `Snapshot()` returns the live internal dictionary, exposing mutable internal state
  - Problem: Returning `counts` directly gives every caller a reference to the private dictionary. Callers can add, remove, or clear entries, silently corrupting the stats; they can also mutate it while `Inc`/`Count` run, which can throw or corrupt the non-thread-safe `Dictionary`. It also breaks the encapsulation the class is trying to provide.
  - Fix: Return a copy: `return new Dictionary<string, int>(counts);` (or expose `IReadOnlyDictionary<string, int>` backed by a copied dictionary).
  - Code snippet:
    ```
    public Dictionary<string, int> Snapshot()
    {
        return counts;
    }
    ```

- **medium** src/counter.cs:9-18 — No synchronization on a per-request counter; `Dictionary` is not thread-safe
  - Problem: For a request-statistics type, `Inc` will plausibly be called from multiple request-handling threads. Concurrent `Inc`/`Count`/`Snapshot` calls on a shared `Dictionary` can corrupt internal buckets or throw `IndexOutOfRangeException`/`InvalidOperationException`. If the class is only ever used single-threaded this is fine, but nothing documents or enforces that.
  - Fix: Guard all three methods with a `lock` on a private object, or use `ConcurrentDictionary<string, int>` with `AddOrUpdate`/`GetOrAdd` (note `ConcurrentDictionary.GetEnumerator` is snapshot-safe, which also fixes the `Snapshot` issue).
  - Code snippet:
    ```
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    ```

- **low** src/counter.cs:11-18 — Double dictionary lookup in `Inc` (`ContainsKey` then indexer)
  - Problem: `ContainsKey` + indexer performs two hash lookups per call; on a hot request path this is wasteful. Same pattern in `Count`.
  - Fix: Use a single lookup: `counts.TryGetValue(path, out var n); counts[path] = n + 1;` (or `CollectionsMarshal.GetValueRefOrAddDefault` on .NET Core for zero extra lookups).
  - Code snippet:
    ```
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    ```

### Verdict
`request changes`


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Review identified all three expected concurrency issues: Snapshot() leaks the internal dictionary, concurrent Inc/Count/Snapshot access is unsafe, and the Inc check-then-increment pattern is non-atomic. The second finding explicitly mentions Count in the concurrency problem, covering the unlocked_read concern. |
| Precision | 3 | No false positives and no must-not-flag items flagged. The double-lookup nit is an acceptable extra. |
| Severity Calibration | 2 | Snapshot was correctly ranked medium. However, the combined Inc/Count race finding was ranked medium when race_in_inc and unlocked_read are expected high; one level off. |
| Actionability | 3 | Each finding provides a concrete fix and correct file:line references, including using a lock, ConcurrentDictionary, and returning a dictionary copy. |
| Reasoning | 3 | Explanations correctly describe impact: dictionary corruption, IndexOutOfRangeException/InvalidOperationException, broken encapsulation, and caller mutation. |
| Format | 3 | Follows Summary / Findings / Verdict and orders findings by severity. |
| Tone | 3 | Constructive, focused, and free of filler. |

- Matched: unlocked_read, snapshot_leak, race_in_inc
- Missed: none
- False positives: none
- Typo recall: N/A

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
    "recall": "Review identified all three expected concurrency issues: Snapshot() leaks the internal dictionary, concurrent Inc/Count/Snapshot access is unsafe, and the Inc check-then-increment pattern is non-atomic. The second finding explicitly mentions Count in the concurrency problem, covering the unlocked_read concern.",
    "precision": "No false positives and no must-not-flag items flagged. The double-lookup nit is an acceptable extra.",
    "severity_calibration": "Snapshot was correctly ranked medium. However, the combined Inc/Count race finding was ranked medium when race_in_inc and unlocked_read are expected high; one level off.",
    "actionability": "Each finding provides a concrete fix and correct file:line references, including using a lock, ConcurrentDictionary, and returning a dictionary copy.",
    "reasoning": "Explanations correctly describe impact: dictionary corruption, IndexOutOfRangeException/InvalidOperationException, broken encapsulation, and caller mutation.",
    "format": "Follows Summary / Findings / Verdict and orders findings by severity.",
    "tone": "Constructive, focused, and free of filler."
  },
  "matched": [
    "unlocked_read",
    "snapshot_leak",
    "race_in_inc"
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
