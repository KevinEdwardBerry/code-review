---
prompt_version: v2
prompt_file: prompts/code-review.v2.md
fixture: 03-race-condition
date: 2026-10-07
reviewer_model: subagent_explore default model
reviewer_profile: subagent_explore
judge_model: subagent_explore default model
judge_profile: subagent_explore
weighted_score: 85.0
hard_fail: true (missed_critical)
---

# 03-race-condition / v2

## Models
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model)

## AI response
### Summary
Adds a `RequestStats` class that counts requests per path in a `Dictionary`. Functionally correct for single-threaded use, but two real issues: the type is not thread-safe (a problem for a per-request counter in normal server use), and `Snapshot()` leaks the mutable internal dictionary.

### Findings

- **high src/counter.cs:8-18 - `Inc` is not thread-safe (check-then-act race)**
  - Problem: A request counter is almost always called concurrently. `ContainsKey` then `counts[path]++` is a check-then-act pattern, and `Dictionary` itself is unsafe for concurrent reads/writes — concurrent calls can lose increments or corrupt the internal hashtable (which can hang or throw).
  - Fix: Guard all access with a lock, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate(path, 1, (_, c) => c + 1)` / `GetOrAdd`+interlocked counting.
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

- **medium src/counter.cs:25-28 - `Snapshot()` returns the live internal dictionary**
  - Problem: Returning `counts` directly lets callers mutate internal state and iterate it while `Inc` mutates it — a caller doing `foreach` over the snapshot during concurrent writes will get `InvalidOperationException` or torn data. It also violates the implied contract of a "snapshot".
  - Fix: Return a copy under the lock: `lock (gate) return new Dictionary<string,int>(counts);` or use an immutable/read-only view.
  - Code snippet:
    ```csharp
    public Dictionary<string, int> Snapshot()
    {
        return counts;
    }
    ```

- **nit src/counter.cs:10-18 - `Inc` can be simplified**
  - `if (!counts.TryGetValue(path, out var c)) c = 0; counts[path] = c + 1;` avoids double lookup, though this is moot if you switch to `ConcurrentDictionary`.

### Verdict
request changes — the concurrency and encapsulation issues should be fixed before this ships, since the class will almost certainly be used from multiple threads.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 2 | Found the Inc check-then-act race and the Snapshot leak with correct locations and fixes. The unsynchronized read in Count (unlocked_read) was never identified as its own finding; it is only obliquely implied by 'Dictionary itself is unsafe for concurrent reads/writes' inside the Inc finding, which discusses write-write races, not the read path in Count. That is a missed high-severity expected item. |
| Precision | 3 | No false positives. The nit about simplifying Inc via TryGetValue is a genuine, minor improvement consistent with acceptable extras; it does not flag the Dictionary type or method names themselves. |
| Severity calibration | 2 | Inc race correctly rated high; Snapshot leak rated medium, within the expected high/medium band. The TryGetValue nit appropriately rated nit. Missing the Count read race entirely means severity coverage is incomplete, but what was rated was calibrated. |
| Actionability | 3 | Each finding has a concrete fix (lock or ConcurrentDictionary with AddOrUpdate/GetOrAdd; copy under lock) plus correct file:line ranges and code snippets. |
| Reasoning | 3 | Explanations are accurate and explain real impact: lost increments, hashtable corruption, InvalidOperationException during iteration, broken snapshot contract. |
| Format | 3 | Follows Summary / Findings / Verdict exactly, findings ordered by severity (high, medium, nit). |
| Tone | 3 | Constructive and focused; no filler or noise. |

- Matched: race_in_inc, snapshot_leak
- Missed: unlocked_read
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{"fixture": "03-race-condition", "scores": {"recall": 2, "precision": 3, "severity_calibration": 2, "actionability": 3, "reasoning": 3, "format": 3, "tone": 3}, "rationale": {"recall": "Found the Inc check-then-act race and the Snapshot leak with correct locations and fixes. The unsynchronized read in Count (unlocked_read) was never identified as its own finding; it is only obliquely implied by 'Dictionary itself is unsafe for concurrent reads/writes' inside the Inc finding, which discusses write-write races, not the read path in Count. That is a missed high-severity expected item.", "precision": "No false positives. The nit about simplifying Inc via TryGetValue is a genuine, minor improvement consistent with acceptable extras; it does not flag the Dictionary type or method names themselves.", "severity_calibration": "Inc race correctly rated high; Snapshot leak rated medium, within the expected high/medium band. The TryGetValue nit appropriately rated nit. Missing the Count read race entirely means severity coverage is incomplete, but what was rated was calibrated.", "actionability": "Each finding has a concrete fix (lock or ConcurrentDictionary with AddOrUpdate/GetOrAdd; copy under lock) plus correct file:line ranges and code snippets.", "reasoning": "Explanations are accurate and explain real impact: lost increments, hashtable corruption, InvalidOperationException during iteration, broken snapshot contract.", "format": "Follows Summary / Findings / Verdict exactly, findings ordered by severity (high, medium, nit).", "tone": "Constructive and focused; no filler or noise."}, "matched": ["race_in_inc", "snapshot_leak"], "missed": ["unlocked_read"], "false_positives": [], "typo_recall": null, "hard_fail": {"missed_critical": true, "fabricated": false, "missed_behavioral_typo": false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
