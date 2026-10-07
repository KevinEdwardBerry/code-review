---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 03-race-condition
date: 2026-10-07
reviewer_model: default subagent model
reviewer_profile: subagent_explore
judge_model: parent model
judge_profile: subagent_general
weighted_score: 78.3
hard_fail: none
---

# 03-race-condition / v4

## Models
- Reviewer: subagent_explore (default subagent model)
- Judge: subagent_general (parent model)

## AI response
### Summary
The change adds a `RequestStats` class that counts requests per path using a plain `Dictionary<string, int>` with a check-then-act pattern. It is not thread-safe despite clearly being intended for concurrent request tracking, and `Snapshot()` leaks the mutable internal state.

### Findings
- **critical** src/counter.cs:13-21 - Race condition in `Inc` corrupts the dictionary and loses counts
  - Problem: `counts.ContainsKey(path)` followed by `counts[path]++` / `counts[path] = 1` is a non-atomic check-then-act. Concurrent calls can both miss the key and overwrite each other (lost updates), and concurrent writes/reads on a `Dictionary<K,V>` can corrupt internal buckets, throw `NullReferenceException`/`IndexOutOfRangeException`, or hang readers — a real corrupting race for a per-request counter.
  - Fix: Guard all access with a `lock` (or `ReaderWriterLockSlim`), or use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`.
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    else
    {
        counts[path] = 1;
    }
    ```

- **high** src/counter.cs:27-30 - `Snapshot()` returns the live internal dictionary
  - Problem: Returning `counts` directly exposes mutable internal state: callers can mutate counts, and any caller that enumerates the returned dictionary while `Inc` runs will hit `InvalidOperationException` ("collection was modified") or observe torn data. It also defeats any future locking since readers bypass the lock.
  - Fix: Return a copy under the lock, e.g. `lock (gate) return new Dictionary<string,int>(counts);` (or an `IReadOnlyDictionary` snapshot).
  - Code snippet:
    ```csharp
    public Dictionary<string, int> Snapshot()
    {
        return counts;
    }
    ```

- **medium** src/counter.cs:24-25 - `Count` performs an unsynchronized read
  - Problem: Even if `Inc` were fixed, `Count` reads `counts` without synchronization; concurrent `Dictionary` read+write is undefined and can throw or return garbage. It also does two lookups (`ContainsKey` + indexer) — correct but wasteful.
  - Fix: Read under the same lock and use `TryGetValue`: `lock (gate) { return counts.TryGetValue(path, out var c) ? c : 0; }`
  - Code snippet:
    ```csharp
    return counts.ContainsKey(path) ? counts[path] : 0;
    ```

- **low** src/counter.cs:13 - `Inc` does two dictionary lookups per call
  - Problem: The `ContainsKey` + indexer/setter pattern performs two hash lookups; a single `TryGetValue` (under the lock) is simpler and faster.
  - Fix: `if (counts.TryGetValue(path, out var c)) counts[path] = c + 1; else counts[path] = 1;` — or use `CollectionsMarshal.GetValueRefOrAddDefault` for a single lookup.
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path)) { counts[path]++; }
    ```

### Verdict
request changes


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Found all three must-find issues: race_in_inc, snapshot_leak, and unlocked_read. |
| Precision | 2 | No fabricated findings, but included an unseeded low nit about two dictionary lookups in Inc (trivial noise). |
| Severity calibration | 1 | Race in Inc is critical (expected high) and Count unsynchronized read is medium (expected high); snapshot_leak at high matches the expected high/medium range. Multiple one-level mis-calibrations. |
| Actionability | 2 | Provides concrete, correct fixes and relevant code snippets, but cited file:line ranges are slightly off (e.g., Inc 13-21, Snapshot 27-30). |
| Reasoning correctness | 3 | Explanations are correct and explain the concurrent-access impact (lost updates, exceptions, torn data). |
| Format adherence | 3 | Follows Summary / Findings / Verdict, ordered by descending severity. |
| Tone and concision | 3 | Constructive, concise, no filler or rudeness. |

- Matched: race_in_inc, snapshot_leak, unlocked_read
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
  "scores": {
    "recall": 3,
    "precision": 2,
    "severity_calibration": 1,
    "actionability": 2,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Found all three must-find issues: race_in_inc, snapshot_leak, and unlocked_read.",
    "precision": "No fabricated findings, but included an unseeded low nit about two dictionary lookups in Inc (trivial noise).",
    "severity_calibration": "Race in Inc is critical (expected high) and Count unsynchronized read is medium (expected high); snapshot_leak at high matches the expected high/medium range. Multiple one-level mis-calibrations.",
    "actionability": "Provides concrete, correct fixes and relevant code snippets, but cited file:line ranges are slightly off (e.g., Inc 13-21, Snapshot 27-30).",
    "reasoning": "Explanations are correct and explain the concurrent-access impact (lost updates, exceptions, torn data).",
    "format": "Follows Summary / Findings / Verdict, ordered by descending severity.",
    "tone": "Constructive, concise, no filler or rudeness."
  },
  "matched": [
    "race_in_inc",
    "snapshot_leak",
    "unlocked_read"
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
