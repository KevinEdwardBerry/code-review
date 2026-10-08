---
prompt_version: v3
prompt_file: prompts/code-review.v3.md
fixture: 03-race-condition
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 88.3
hard_fail: false
---

# 03-race-condition / v3

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
New request-stats code is demonstrably raced: `Inc` mutates a non-thread-safe `Dictionary` from concurrent `Task.Run` calls, and `Snapshot` leaks the mutable internal state.

## Findings

**[High] src/counter.cs:33 — unsynchronized concurrent writes to `Dictionary` corrupt state and lose counts**

```csharp
await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));
```

`HandleAllAsync` explicitly invokes `stats.Inc(p)` on multiple thread-pool threads concurrently, while `Inc` (lines 12–16) performs a non-atomic `ContainsKey`/index-set sequence on a plain `Dictionary<string,int>`. Concurrent `Inc` calls can overwrite each other's increments (two threads both seeing `ContainsKey == false`, then both setting `counts[path] = 1`) and, worse, concurrent mutation of `Dictionary` is documented to produce undefined behavior (corrupted internal buckets, exceptions, hangs). Reads via `Count`/`Snapshot` racing with writes are likewise unsafe.

Fix: guard all accesses with a `lock`, use `Interlocked`-safe primitives, or replace `counts` with `ConcurrentDictionary<string,int>` and `AddOrUpdate(path, 1, (_, c) => c + 1)`, and make `Count` use `TryGetValue`.

**[Medium] src/counter.cs:23 — `Snapshot` returns the live mutable dictionary**

```csharp
public Dictionary<string, int> Snapshot()
{
    return counts;
}
```

Callers of `Snapshot` receive the internal `counts` reference, so any external mutation corrupts the stats and any enumeration races with concurrent `Inc` writes (throwing `InvalidOperationException`). Fix: return a copy under the same lock used for mutation, e.g. `return new Dictionary<string,int>(counts);` inside the lock (or materialize a copy from a `ConcurrentDictionary`).

**[Low] src/counter.cs:19 — redundant double dictionary lookup in `Count`**

```csharp
return counts.ContainsKey(path) ? counts[path] : 0;
```

Two lookups where `TryGetValue` suffices (`counts.TryGetValue(path, out var c) ? c : 0`). Minor, but halves lookups and avoids an extra bounds check per call.

## Verdict
Request changes — the demonstrated concurrent `Inc` calls make the shared `Dictionary` unsafe; this needs a lock or `ConcurrentDictionary` before merging.

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Covers concurrent Inc mutations, unsynchronized reads through Count, and Snapshot exposing the mutable dictionary. The Count race is mentioned in the concurrent-writes finding rather than as its own finding. |
| Precision | 2 | The Count double-lookup comment is a minor, unseeded optimization nit; the other findings match expected defects. |
| Severity calibration | 3 | The concurrent mutation is High and Snapshot is Medium, consistent with the expected severity ranges. The extra lookup nit is marked Low. |
| Actionability | 2 | Gives concrete locking/copying fixes and relevant line references for Inc and Snapshot. The Count synchronization issue is not separately tied to its source line. |
| Reasoning | 3 | Explains the concurrent use in HandleAllAsync, the non-atomic Inc sequence, and the risks of exposing the live dictionary. |
| Format | 3 | Uses Summary, Findings, and Verdict in the requested order, with findings ordered by severity. |
| Tone | 3 | Constructive and focused. |

- Matched: unlocked_read, snapshot_leak, race_in_inc
- Missed: none
- False positives: redundant double dictionary lookup in Count (minor unseeded nit)
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
  "scores": {
    "recall": 3,
    "precision": 2,
    "severity_calibration": 3,
    "actionability": 2,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Covers concurrent Inc mutations, unsynchronized reads through Count, and Snapshot exposing the mutable dictionary. The Count race is mentioned in the concurrent-writes finding rather than as its own finding.",
    "precision": "The Count double-lookup comment is a minor, unseeded optimization nit; the other findings match expected defects.",
    "severity_calibration": "The concurrent mutation is High and Snapshot is Medium, consistent with the expected severity ranges. The extra lookup nit is marked Low.",
    "actionability": "Gives concrete locking/copying fixes and relevant line references for Inc and Snapshot. The Count synchronization issue is not separately tied to its source line.",
    "reasoning": "Explains the concurrent use in HandleAllAsync, the non-atomic Inc sequence, and the risks of exposing the live dictionary.",
    "format": "Uses Summary, Findings, and Verdict in the requested order, with findings ordered by severity.",
    "tone": "Constructive and focused."
  },
  "matched": ["unlocked_read", "snapshot_leak", "race_in_inc"],
  "missed": [],
  "false_positives": ["Redundant double dictionary lookup in Count (minor unseeded nit)."],
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
