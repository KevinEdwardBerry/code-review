---
prompt_version: v7
prompt_file: prompts/code-review.v7.md
fixture: 03-race-condition
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 88.3
hard_fail: none
---

# 03-race-condition / v7

## Models
- Reviewer: subagent_explore (not exposed)
- Judge: subagent_general (not exposed)

## AI response
## Summary
The change adds a request counter that mutates a plain `Dictionary` from parallel tasks, making it thread-unsafe.

## Findings
[High] src/counter.cs:13 — Unsynchronized write to shared dictionary
`            counts[path] = count + 1;`
`Inc` is invoked via `Task.Run` inside `Task.WhenAll` (line 35), so multiple threads concurrently mutate `counts`. `Dictionary<TKey,TValue>` is not thread-safe; concurrent writes can lose increments and corrupt internal state, potentially throwing on later reads/writes. Fix: guard `Inc`/`Count`/`Snapshot` with a lock, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd`.

[Medium] src/counter.cs:15 — Second unsynchronized write path
`            counts[path] = 1;`
Same race as above for the first-increment path; must be under the same lock or use `ConcurrentDictionary`.

[Medium] src/counter.cs:20 — Unsynchronized read of shared dictionary
`        return counts.TryGetValue(path, out var count) ? count : 0;`
`Count` can read `counts` while another thread is writing it, which is undefined behavior for `Dictionary` (torn reads/exceptions possible). Fix: take the same lock, or use `ConcurrentDictionary`.

[Medium] src/counter.cs:25 — Snapshot returns the live dictionary and reads it unsynchronized
`        return counts;`
This exposes the mutable internal dictionary to callers and returns it while other threads may be mutating it. Fix: return a copy under the lock (e.g., `new Dictionary<string,int>(counts)`) or use `ConcurrentDictionary` and return a snapshot copy.

## Verdict
Request changes


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Found all seeded issues: the race in Inc, the unsynchronized read in Count, and the Snapshot leak. |
| Precision | 2 | No fabricated or must-not-flag findings; the only issue is a redundant duplicate report of the same race condition at line 15. |
| Severity | 2 | The race in Inc is correctly high at line 13, but the duplicate report at line 15 is split out as medium instead of being part of the same high finding; Count and Snapshot are correctly medium. |
| Actionability | 3 | Each finding has a concrete fix and correct file:line citations, with CITATION_CHECK passing. |
| Reasoning | 3 | Explanations correctly describe lost increments, Dictionary corruption/undefined behavior, and external mutation risk. |
| Format | 3 | Follows Summary / Findings / Verdict, ordered by severity. |
| Tone | 3 | Constructive, concise, no filler. |


- Matched: race_in_inc, unlocked_read, snapshot_leak
- Missed: none
- False positives: Redundant duplicate report of the race_in_inc finding at line 15
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{"fixture": "03-race-condition", "scores": {"recall": 3, "precision": 2, "severity_calibration": 2, "actionability": 3, "reasoning": 3, "format": 3, "tone": 3}, "rationale": {"recall": "Found all seeded issues: the race in Inc, the unsynchronized read in Count, and the Snapshot leak.", "precision": "No fabricated or must-not-flag findings; the only issue is a redundant duplicate report of the same race condition at line 15.", "severity_calibration": "The race in Inc is correctly high at line 13, but the duplicate report at line 15 is split out as medium instead of being part of the same high finding; Count and Snapshot are correctly medium.", "actionability": "Each finding has a concrete fix and correct file:line citations, with CITATION_CHECK passing.", "reasoning": "Explanations correctly describe lost increments, Dictionary corruption/undefined behavior, and external mutation risk.", "format": "Follows Summary / Findings / Verdict, ordered by severity.", "tone": "Constructive, concise, no filler."}, "matched": ["race_in_inc", "unlocked_read", "snapshot_leak"], "missed": [], "false_positives": ["Redundant duplicate report of the race_in_inc finding at line 15"], "typo_recall": null, "hard_fail": {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}}

```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
