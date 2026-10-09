---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 03-race-condition
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 75.0
hard_fail: missed_critical, fabricated
---

# 03-race-condition / v4

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
`RequestStats` uses a non-thread-safe `Dictionary` that `RequestHandler.HandleAllAsync` mutates from multiple concurrent `Task.Run` calls, and `Snapshot()` leaks the mutable internal dictionary — together these create real correctness and race-condition defects.

## Findings

**[High] src/counter.cs:30 — Concurrent `Dictionary` mutation is not thread-safe**

```csharp
await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));
```

`HandleAllAsync` fans out `stats.Inc(p)` across thread-pool threads that run concurrently. `Dictionary<string,int>` is not thread-safe for concurrent writes; the read-modify-write in `Inc` (`src/counter.cs:11-13`) can lose increments and, under concurrent structural modification, can corrupt internal state or throw. Fix: use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or serialize access with a lock.

**[Medium] src/counter.cs:22 — `Snapshot()` returns the live internal dictionary**

```csharp
return counts;
```

Callers receive a mutable reference to the internal state: they can read it while `Inc` concurrently mutates it (risk of `InvalidOperationException` during enumeration, torn reads) and can write to it, bypassing the class's encapsulation. Fix: return a copy, e.g., `return new Dictionary<string,int>(counts);` (with the concurrency issue above fixed, `new Dictionary<string,int>(counts)` on a `ConcurrentDictionary` is a safe snapshot).

**[Low] src/counter.cs:10 — Unnecessary manual get-then-set in `Inc`**

```csharp
if (counts.TryGetValue(path, out var count))
```

`counts[path] = counts.GetValueOrDefault(path) + 1` (or `CollectionsMarshal.GetValueRefOrAddDefault`) expresses the same logic in one lookup; strictly cosmetic/perf nit, but worth folding into the thread-safety fix.

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 2 | Identifies the concurrent Inc update and Snapshot leak, but misses the expected unlocked read in Count. That omission is critical under the rubric. |
| Precision | 2 | The two main findings are valid. The low-severity get-then-set nit is cosmetic and not a meaningful defect; its suggested alternatives do not themselves provide thread safety. |
| Severity calibration | 2 | The concurrency risk in Inc is correctly rated High and the Snapshot leak is reasonably rated Medium. However, the review omits a critical expected issue in Count. |
| Actionability | 3 | Offers concrete fixes: ConcurrentDictionary with AddOrUpdate or locking for Inc, and returning a copy for Snapshot. It does not give a fix for the unmentioned Count race. |
| Reasoning correctness | 2 | Explains the concurrent writes and mutable-reference risks, but does not account for Count reading the dictionary while it may be mutated. |
| Format adherence | 3 | Clear summary, individually labeled findings, code excerpts, and verdict; the structure is easy to follow. |
| Tone and concision | 3 | Professional and direct, without inflammatory or dismissive language. |

- Matched: race_in_inc, snapshot_leak
- Missed: unlocked_read
- False positives: Low-severity cosmetic/performance nit about manual get-then-set in Inc
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{"fixture":"03-race-condition","scores":{"recall":2,"precision":2,"severity_calibration":2,"actionability":3,"reasoning":2,"format":3,"tone":3},"rationale":{"recall":"Identifies the concurrent Inc update and Snapshot leak, but misses the expected unlocked read in Count. That omission is critical under the rubric.","precision":"The two main findings are valid. The low-severity get-then-set nit is cosmetic and not a meaningful defect; its suggested alternatives do not themselves provide thread safety.","severity_calibration":"The concurrency risk in Inc is correctly rated High and the Snapshot leak is reasonably rated Medium. However, the review omits a critical expected issue in Count.","actionability":"Offers concrete fixes: ConcurrentDictionary with AddOrUpdate or locking for Inc, and returning a copy for Snapshot. It does not give a fix for the unmentioned Count race.","reasoning":"Explains the concurrent writes and mutable-reference risks, but does not account for Count reading the dictionary while it may be mutated.","format":"Clear summary, individually labeled findings, code excerpts, and verdict; the structure is easy to follow.","tone":"Professional and direct, without inflammatory or dismissive language."},"matched":["race_in_inc","snapshot_leak"],"missed":["unlocked_read"],"false_positives":["Low-severity cosmetic/performance nit about manual get-then-set in Inc"],"typo_recall":null,"hard_fail":{"missed_critical":true,"fabricated":true,"missed_behavioral_typo":false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
