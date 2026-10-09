---
prompt_version: v6
prompt_file: prompts/code-review.v6.md
fixture: 03-race-condition
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 86.7
hard_fail: false
---

# 03-race-condition / v6

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
New code introduces a `RequestStats` counter and a handler that increments it concurrently via `Task.Run`, but the underlying `Dictionary` is accessed without any synchronization, making the feature racy and the returned snapshot mutable.

## Findings

[High] src/counter.cs:13 — unsynchronized concurrent write to shared Dictionary
`counts[path] = count + 1;` (also `  15 | +counts[path] = 1;`, enabled by `  35 | +await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));`)
`Task.Run` invokes `Inc` on multiple threads; `Dictionary<K,V>` is not thread-safe for concurrent writes. This can corrupt the internal structure, lose increments, or throw. Fix: guard all accesses with a `lock`, use `Interlocked`, or switch to `ConcurrentDictionary<string,int>` with `AddOrUpdate`.

[High] src/counter.cs:20 — unsynchronized concurrent read of shared Dictionary
`return counts.TryGetValue(path, out var count) ? count : 0;`
`Total` → `Count` reads the dictionary while `HandleAllAsync` may be writing it; reads concurrent with writes are undefined and can return stale/corrupt data or throw. Fix: synchronize this read under the same lock or use `ConcurrentDictionary`.

[Medium] src/counter.cs:25 — Snapshot returns the live internal dictionary
`return counts;`
Callers receive the mutable backing collection: they can read it while writes occur (unsafe enumeration can throw `InvalidOperationException`) and can mutate it directly, bypassing any synchronization. Fix: return a copy under the lock, e.g. `return new Dictionary<string,int>(counts);` or an immutable/read-only snapshot.

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 3 | Identifies all three expected defects: concurrent Inc updates, an unsynchronized Count read, and Snapshot exposing the backing dictionary. |
| Precision | 3 | All reported defects are supported by the diff; no must-not-flag issue is raised. |
| Severity calibration | 2 | Inc is correctly marked High and Snapshot Medium. Count is marked High rather than the expected Medium, a one-level mismatch. |
| Actionability | 2 | Findings cite relevant lines and propose fixes, but `Interlocked` alone is not sufficient for concurrent Dictionary updates. |
| Reasoning correctness | 2 | Explains concurrency and mutation risks, though “undefined” is imprecise for concurrent reads and writes. |
| Format adherence | 3 | Uses clear summary, findings, and verdict sections with location and severity for each finding. |
| Tone and concision | 3 | Focused and professional, without filler. |

- Matched: race_in_inc, unlocked_read, snapshot_leak
- Missed: None
- False positives: None
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{"fixture":"03-race-condition","scores":{"recall":3,"precision":3,"severity_calibration":2,"actionability":2,"reasoning":2,"format":3,"tone":3},"rationale":{"recall":"Identifies all three expected defects: concurrent Inc updates, an unsynchronized Count read, and Snapshot exposing the backing dictionary.","precision":"All reported defects are supported by the diff; no must-not-flag issue is raised.","severity_calibration":"Inc is correctly marked High and Snapshot Medium. Count is marked High rather than the expected Medium, a one-level mismatch.","actionability":"Findings cite the relevant lines and propose fixes. However, Interlocked alone is not a sufficient fix for concurrent updates to a Dictionary.","reasoning":"Explains the concurrency and mutation risks. The read finding's impact is described correctly, though calling concurrent reads and writes undefined is imprecise.","format":"Uses clear summary, findings, and verdict sections with location and severity for each finding.","tone":"Focused and professional, without filler."},"matched":["race_in_inc","unlocked_read","snapshot_leak"],"missed":[],"false_positives":[],"typo_recall":null,"hard_fail":{"missed_critical":false,"fabricated":false,"missed_behavioral_typo":false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
Citation check: ok (3 citations checked).