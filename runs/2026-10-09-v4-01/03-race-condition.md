---
prompt_version: v4
prompt_file: prompts/code-review.v4.md
fixture: 03-race-condition
date: 2026-10-09
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 90.0
hard_fail: missed_critical
---

# 03-race-condition / v4

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
The change adds a request-stats counter that is mutated from parallel tasks via a non-thread-safe `Dictionary`, and exposes its internal mutable state through `Snapshot`.

## Findings

[High] src/counter.cs:35 — `await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));` — `Inc` is invoked concurrently from multiple thread-pool threads, but `counts` is a plain `Dictionary` guarded by no lock. `Dictionary` is not thread-safe for concurrent writes: simultaneous `TryGetValue`/indexer-set pairs can lose increments (read-modify-write race at src/counter.cs:13-16, `counts[path] = count + 1;`), and concurrent structural mutations can corrupt the internal buckets, causing exceptions or infinite loops in readers. Fix: use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or serialize access with a `lock`.

[Medium] src/counter.cs:26 — `return counts;` in `Snapshot()` returns the live internal dictionary rather than a copy. Callers can mutate the stats state directly, and enumerating the returned dictionary while `Inc` writes to it throws `InvalidOperationException`. Fix: `return new Dictionary<string, int>(counts);` (taken under the same lock/concurrent collection used for writes).

## Verdict
Request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 2 | Identifies the concurrent write race in Inc and the exposed mutable Snapshot dictionary, but not Count's unsynchronized read. |
| Precision | 3 | No unsupported findings; the concurrent dictionary suggestion is an acceptable fix. |
| Severity calibration | 3 | The write race is High and snapshot leak Medium, within expected ranges. |
| Actionability | 3 | Provides concrete fixes and relevant file/line references for both findings. |
| Reasoning | 3 | Correctly explains the concurrency risk and consequences of exposing the live dictionary. |
| Format | 3 | Uses Summary, Findings, and Verdict in order. |
| Tone | 3 | Focused, constructive, and concise. |

- Matched: `race_in_inc`, `snapshot_leak`
- Missed: `unlocked_read`
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
  "scores": {"recall": 2, "precision": 3, "severity_calibration": 3, "actionability": 3, "reasoning": 3, "format": 3, "tone": 3},
  "rationale": {
    "recall": "Identifies the concurrent write race in Inc and the exposed mutable Snapshot dictionary, but does not specifically identify Count's unsynchronized read.",
    "precision": "No unsupported findings; the concurrent dictionary suggestion is an acceptable fix.",
    "severity_calibration": "The concurrent write issue is marked High and the snapshot leak Medium, both within the expected severity ranges.",
    "actionability": "Provides concrete fixes and relevant file and line references for both findings.",
    "reasoning": "Correctly explains the concurrency risk and the consequences of exposing the live dictionary.",
    "format": "Uses the required Summary, Findings, and Verdict sections in order.",
    "tone": "Focused, constructive, and concise."
  },
  "matched": ["race_in_inc", "snapshot_leak"],
  "missed": ["unlocked_read"],
  "false_positives": [],
  "typo_recall": null,
  "hard_fail": {"missed_critical": true, "fabricated": false, "missed_behavioral_typo": false}
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
