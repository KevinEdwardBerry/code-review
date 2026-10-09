---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 03-race-condition
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 60.0
hard_fail: false
---

# 03-race-condition / v1

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
# Code Review: `src/counter.cs`

## Summary
The code compiles and works correctly in single-threaded use, but `RequestHandler.HandleAllAsync` explicitly invokes `stats.Inc` from multiple threads via `Task.Run`/`Task.WhenAll`. That makes the underlying `Dictionary` race-prone — this is the central defect.

## Findings

### 🔴 Critical — `Dictionary<string,int>` is not thread-safe (lines 7–16, 32–36)
`Inc` performs a read-modify-write (`TryGetValue` then indexed set) and `HandleAllAsync` runs it concurrently. Consequences:
- **Lost updates**: two threads can both read count `N` and both write `N+1`.
- **Corruption**: concurrent writes during a dictionary resize can corrupt internal buckets, leading to infinite loops or `IndexOutOfRangeException` on later reads — a well-documented failure mode for `Dictionary`.
- Even `Count`/`Snapshot` reading while another thread writes is unsafe.

**Fix options:**
- Use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)` or `Interlocked` on the value.
- Or guard all access with a `lock`.
- Better still: since `Task.Run` parallelism here buys nothing for a cheap increment, just iterate sequentially — the simplest correct code.

### 🟠 Major — `Snapshot()` returns the live mutable dictionary (lines 25–28)
Callers get a direct reference to internal state: they can mutate it, and their reads race with concurrent `Inc` calls (enumerating a `Dictionary` during mutation throws `InvalidOperationException`). Return a copy:
```csharp
public Dictionary<string,int> Snapshot()
{
    lock (gate) return new Dictionary<string,int>(counts);
}
```
(or `ToDictionary`/`IReadOnlyDictionary`).

### 🟡 Minor — Parallelism overhead
`Task.Run` per path for an O(1) increment will usually be *slower* than a sequential loop due to thread-pool scheduling. If `paths` is large, consider `Parallel.ForEach` with partitioned local counters merged at the end.

### 🟡 Minor — `Inc` can be simplified
Single-indexer form is equivalent and avoids a double lookup... actually, the current two-step form is fine, but `counts[path] = counts.GetValueOrDefault(path) + 1;` is cleaner. Style only.

### ℹ️ Note — `counts` isn't marked `readonly`
`private readonly Dictionary<...> counts` would prevent accidental reassignment.

## Recommendation
Request changes. At minimum: replace the dictionary with `ConcurrentDictionary` + `AddOrUpdate`, make `Snapshot` return a copy, and seriously consider dropping `Task.Run` entirely unless there's real CPU-bound work to parallelize.


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 2 | The review finds race_in_inc: the read-modify-write in Inc is a lost-update race under concurrent HandleAllAsync. It finds snapshot_leak with a copy-under-lock fix. It only mentions unlocked_read in passing ('Even Count/Snapshot reading while another thread writes is unsafe'). It has no dedicated finding and no specific fix for Count. That counts as partial, so most must-finds are covered but not all. |
| Precision | 1 | It flags the Task.Run parallelism as a Minor finding and recommends removing it. The 'Must not flag' list says not to flag RequestHandler or its use of Task.Run, so this is a clear false positive. The Inc simplification finding is self-contradicting noise ('actually, the current form is fine'). The readonly note is also wrong: the diff has no readonly on counts, but this is trivial. |
| Severity calibration | 2 | The Dictionary race is rated Critical against an expected high, which is within one level. Snapshot is rated Major, which fits the expected high/medium. The style items are rated Minor or Note, which is acceptable. |
| Actionability | 2 | The fixes are concrete: ConcurrentDictionary with AddOrUpdate, or a lock, plus a code snippet for Snapshot. The line references are approximate and appear off against the diff (the review cites 7–16, 32–36 and 25–28, while the diff has Inc at roughly lines 80–86 and Snapshot at 93–96). The Snapshot snippet uses a `gate` field that is never defined. Count gets no specific fix. |
| Reasoning correctness | 2 | The explanations of lost updates, resize corruption and enumeration during mutation are correct and cover the impact. The claim that Task.Run is slower is a side issue. The review does not separately explain the unsynchronized read in Count. |
| Format adherence | 2 | It has Summary, Findings and a Recommendation section, with Findings ordered by severity. It uses 'Recommendation' rather than 'Verdict', and it adds Minor and Note items that dilute the structure. |
| Tone and concision | 2 | The tone is constructive, but the Minor and Note items add filler. One item shows visible self-correction ('... actually, the current form is fine'). |

- Matched: race_in_inc, snapshot_leak
- Missed: unlocked_read
- False positives: 
  - Flags Task.Run parallelism in RequestHandler as an issue, which is on the Must-not-flag list
  - Suggests simplifying Inc, then admits the current form is fine
  - Says counts isn't marked readonly, which is a trivial style nit
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
  "scores": {
    "recall": 2,
    "precision": 1,
    "severity_calibration": 2,
    "actionability": 2,
    "reasoning": 2,
    "format": 2,
    "tone": 2
  },
  "rationale": {
    "recall": "The review finds race_in_inc: the read-modify-write in Inc is a lost-update race under concurrent HandleAllAsync. It finds snapshot_leak with a copy-under-lock fix. It only mentions unlocked_read in passing ('Even Count/Snapshot reading while another thread writes is unsafe'). It has no dedicated finding and no specific fix for Count. That counts as partial, so most must-finds are covered but not all.",
    "precision": "It flags the Task.Run parallelism as a Minor finding and recommends removing it. The 'Must not flag' list says not to flag RequestHandler or its use of Task.Run, so this is a clear false positive. The Inc simplification finding is self-contradicting noise ('actually, the current form is fine'). The readonly note is also wrong: the diff has no readonly on counts, but this is trivial.",
    "severity_calibration": "The Dictionary race is rated Critical against an expected high, which is within one level. Snapshot is rated Major, which fits the expected high/medium. The style items are rated Minor or Note, which is acceptable.",
    "actionability": "The fixes are concrete: ConcurrentDictionary with AddOrUpdate, or a lock, plus a code snippet for Snapshot. The line references are approximate and appear off against the diff (the review cites 7–16, 32–36 and 25–28, while the diff has Inc at roughly lines 80–86 and Snapshot at 93–96). The Snapshot snippet uses a `gate` field that is never defined. Count gets no specific fix.",
    "reasoning": "The explanations of lost updates, resize corruption and enumeration during mutation are correct and cover the impact. The claim that Task.Run is slower is a side issue. The review does not separately explain the unsynchronized read in Count.",
    "format": "It has Summary, Findings and a Recommendation section, with Findings ordered by severity. It uses 'Recommendation' rather than 'Verdict', and it adds Minor and Note items that dilute the structure.",
    "tone": "The tone is constructive, but the Minor and Note items add filler. One item shows visible self-correction ('... actually, the current form is fine')."
  },
  "matched": [
    "race_in_inc",
    "snapshot_leak"
  ],
  "missed": [
    "unlocked_read"
  ],
  "false_positives": [
    "Flags Task.Run parallelism in RequestHandler as an issue, which is on the Must-not-flag list",
    "Suggests simplifying Inc, then admits the current form is fine",
    "Says counts isn't marked readonly, which is a trivial style nit"
  ],
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
