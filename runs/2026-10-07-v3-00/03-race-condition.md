---
prompt_version: v3
prompt_file: prompts/code-review.v3.md
fixture: 03-race-condition
date: 2026-10-07
reviewer_model: subagent_explore default model
reviewer_profile: subagent_explore
judge_model: subagent_explore default model
judge_profile: subagent_explore
weighted_score: 95.0
hard_fail: none
---

# 03-race-condition / v3

## Models
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model)

## AI response
### Summary
Adds a `RequestStats` class that tracks per-path request counts in a plain `Dictionary<string,int>`. The logic is simple and correct in single-threaded use, but `Snapshot()` leaks the live mutable dictionary and nothing is thread-safe for what is presumably a request-tracking use case.

### Findings

- **high** src/counter.cs:26 - `Snapshot()` returns the internal dictionary, exposing mutable shared state
  - Problem: Returning `counts` directly hands callers a live reference to the private field. Any caller can add, remove, or `Clear()` entries, silently corrupting stats; they can also observe mutations in real time and hit `InvalidOperationException` if they enumerate while `Inc` writes. This defeats the encapsulation the `private` field is supposed to provide.
  - Fix: Return a copy, e.g. `return new Dictionary<string, int>(counts);` or expose `IReadOnlyDictionary<string,int>` over a defensive copy.
  - Code snippet:
    ```csharp
    public Dictionary<string, int> Snapshot()
    {
        return counts;
    }
    ```

- **medium** src/counter.cs:9-22 - No thread-safety despite request-counting context
  - Problem: `Dictionary<,>` is not thread-safe. If `Inc`/`Count`/`Snapshot` are ever called from concurrent request handlers (the class name implies a web/request context), the `ContainsKey` + index pattern in `Inc` is a check-then-act race, and a `Snapshot` copy concurrent with writes can corrupt the dictionary or throw. This is only a must-fix if the class is shared across threads — the diff alone doesn't show usage, but "request stats" strongly suggests it.
  - Fix: Use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, n) => n + 1);` and `TryGetValue`/`GetValueOrDefault` in `Count`, or guard all access with a `lock`.
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    ```

- **low** src/counter.cs:9 - `Inc(null)` throws `ArgumentNullException`
  - Problem: `Dictionary` forbids null keys, so `Inc(null)` and `Count(null)` throw. If `path` can plausibly be null (e.g., unmatched route), decide explicitly whether to reject or normalize rather than relying on the incidental exception.
  - Fix: Add `ArgumentNullException.ThrowIfNull(path);` for a clear contract, or map null/empty to a sentinel like `""`.
  - Code snippet:
    ```csharp
    public void Inc(string path)
    ```

- **nit** src/counter.cs:10 - Redundant `ContainsKey` + indexer double lookup
  - Problem: Two hash lookups per increment; `TryGetValue` does it in one. Purely a micro-optimization.
  - Fix: `counts[path] = counts.TryGetValue(path, out var n) ? n + 1 : 1;`
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    ```

### Verdict
request changes (the `Snapshot()` encapsulation leak is a real defect; thread-safety should be addressed or documented before merge).

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | All three expected issues are identified: snapshot_leak as a dedicated high finding (src/counter.cs:26), and unlocked_read + race_in_inc captured in the thread-safety finding (src/counter.cs:9-22) which explicitly names the check-then-act race in Inc and concurrent read/write hazards in Count/Snapshot. |
| precision | 3 | No false positives. The Inc(null) low finding and the double-lookup nit are legitimate minor extras consistent with the acceptable-extras spirit; nothing must-not-flag was flagged. |
| severity_calibration | 2 | snapshot_leak correctly rated high. However, the race conditions (expected high) were rated medium, hedged on 'if the class is shared across threads' — off by one level for two high-severity items. The nit and low are appropriate. |
| actionability | 3 | Every finding has a concrete fix (defensive copy, ConcurrentDictionary/lock, ThrowIfNull, TryGetValue) and a correct file:line reference with a snippet. |
| reasoning | 3 | Explanations are correct and explain impact: encapsulation defeat, InvalidOperationException during concurrent enumeration, check-then-act race, dictionary corruption. |
| format | 3 | Follows Summary / Findings / Verdict exactly, findings ordered by severity. |
| tone | 3 | Constructive, concise, no filler; verdict appropriately qualifies the severity of each issue. |

- Matched: unlocked_read, snapshot_leak, race_in_inc
- Missed: 
- False positives: 
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
    "recall": "All three expected issues are identified: snapshot_leak as a dedicated high finding (src/counter.cs:26), and unlocked_read + race_in_inc captured in the thread-safety finding (src/counter.cs:9-22) which explicitly names the check-then-act race in Inc and concurrent read/write hazards in Count/Snapshot.",
    "precision": "No false positives. The Inc(null) low finding and the double-lookup nit are legitimate minor extras consistent with the acceptable-extras spirit; nothing must-not-flag was flagged.",
    "severity_calibration": "snapshot_leak correctly rated high. However, the race conditions (expected high) were rated medium, hedged on 'if the class is shared across threads' — off by one level for two high-severity items. The nit and low are appropriate.",
    "actionability": "Every finding has a concrete fix (defensive copy, ConcurrentDictionary/lock, ThrowIfNull, TryGetValue) and a correct file:line reference with a snippet.",
    "reasoning": "Explanations are correct and explain impact: encapsulation defeat, InvalidOperationException during concurrent enumeration, check-then-act race, dictionary corruption.",
    "format": "Follows Summary / Findings / Verdict exactly, findings ordered by severity.",
    "tone": "Constructive, concise, no filler; verdict appropriately qualifies the severity of each issue."
  },
  "matched": ["unlocked_read", "snapshot_leak", "race_in_inc"],
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
