---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 03-race-condition
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: N/A (judge failed)
hard_fail: unscored (judge failed)
---

# 03-race-condition / v4

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed; failed after one retry)

## AI response
## Summary
The new `RequestStats` counter is not thread-safe but is driven concurrently by `HandleAllAsync`, making the code racy by construction.

## Findings

[High] src/counter.cs:34 — concurrent unsynchronized mutation of `Dictionary<string,int>`
```csharp
await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));
```
`HandleAllAsync` explicitly fans out `stats.Inc(p)` calls across the thread pool, while `Inc` (lines 11–15, `counts[path]++;`) performs a read-modify-write on a plain `Dictionary`, which is not thread-safe. Impact: lost increments (inaccurate counts) and potential internal dictionary corruption/exceptions under concurrent writes. Fix: use a `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)` (or `Interlocked`/`lock` on the existing dictionary).

[Medium] src/counter.cs:26 — `Snapshot()` returns the live internal dictionary
```csharp
        return counts;
```
Callers receive the mutable backing store rather than a snapshot: they can mutate counts or observe it mid-mutation while `HandleAllAsync` is running. Fix: return `new Dictionary<string,int>(counts)` under the same lock used for mutation (or materialize a copy from a `ConcurrentDictionary`).

## Verdict
Request changes

## Judge status
Judge failed after the initial judgment and one retry because neither response satisfied the requested schema. No score, matched/missed lists, or hard-fail determination is assigned.

### Initial judge output (invalid schema)
```json
{"fixture":null,"scores":{"Recall":1,"Precision":3,"Severity":2,"Actionability":3,"Reasoning":3,"Format":3,"Tone":3},"rationale":"The review identifies the Inc race and live-dictionary snapshot leak, with valid references and actionable fixes. It misses the separate unsynchronized Count read while the dictionary is concurrently modified, a high-severity finding that triggers hard_fail.","matched":["race_in_inc","snapshot_leak"],"missed":["unlocked_read"],"false_positives":[],"typo_recall":null,"hard_fail":true}
```

### Retry output (invalid schema)
```json
{"fixture":"03-race-condition","scores":{"recall":2,"precision":3,"severity_calibration":2,"actionability":3,"reasoning":2,"format":3,"tone":3},"hard_fail":{"missed_critical":true,"fabricated":false,"missed_behavioral_typo":false}}
```

- Matched: not scored
- Missed: not scored
- False positives: not scored
- Typo recall: N/A

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
The initial judge identified `unlocked_read` as missed; treat the review's omission of a separate `Count` read finding as a potential regression, not a scored hard fail. Prior v3 score: 88.3; current delta unavailable.
