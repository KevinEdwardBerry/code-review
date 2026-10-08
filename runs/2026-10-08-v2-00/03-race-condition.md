---
prompt_version: v2
prompt_file: prompts/code-review.v2.md
fixture: 03-race-condition
date: 2026-10-08
reviewer_model: not exposed
reviewer_profile: subagent_explore
judge_model: not exposed
judge_profile: subagent_general
weighted_score: 71.7
hard_fail: missed_critical
---

# 03-race-condition / v2

## Models
- Reviewer: subagent_explore (model not exposed)
- Judge: subagent_general (model not exposed)

## AI response
## Summary
New `RequestStats` class for per-path request counters; low overall risk with one encapsulation defect in `Snapshot` and minor inefficiencies.

## Findings

[Medium] src/counter.cs:25-28 — `Snapshot()` returns the internal mutable dictionary
```csharp
public Dictionary<string, int> Snapshot()
{
    return counts;
}
```
Callers receive a live reference to the private `counts` map, so they can mutate (or clear) it without going through `Inc()`, corrupting the counters — the opposite of what "snapshot" implies, and reads/writes on that shared reference also race with `Inc()` if used across threads. Fix: return a copy, e.g. `return new Dictionary<string, int>(counts);`.

[Low] src/counter.cs:10-13 — Double dictionary lookup in `Inc` (`ContainsKey` + indexer)
```csharp
if (counts.ContainsKey(path))
    counts[path]++;
else
    counts[path] = 1;
```
Performs two hash lookups per increment and, in a multithreaded context, the check-then-act is not atomic. Fix: `counts.TryGetValue(path, out var c); counts[path] = c + 1;` — one lookup, same result. If `Inc` is called concurrently, wrap in a lock or use `ConcurrentDictionary` (the diff itself provides no synchronization, so flag only if callers are concurrent).

[Low] src/counter.cs:17-20 — `Count` also does two lookups via `ContainsKey` + indexer; use `counts.TryGetValue(path, out var c) ? c : 0`.

## Verdict
Approve with nits

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---:|---|
| Recall | 2 | Identifies snapshot_leak and race_in_inc, but misses the Count read/write synchronization defect. |
| Precision | 3 | The findings describe real behavior or inefficiency in the diff; no fabricated or clearly false findings. |
| Severity calibration | 1 | The concurrent Inc race is rated Low despite being expected High, and the missed Count race is also High. |
| Actionability | 2 | Provides concrete locations and fixes, but the Snapshot copy suggestion omits locking, and TryGetValue alone does not make Inc atomic. |
| Reasoning | 2 | Correctly explains the exposed mutable dictionary and the check-then-act race in Inc, but does not identify Count's unsynchronized dictionary read. |
| Format | 3 | Uses Summary, Findings, and Verdict sections, with findings ordered by severity. |
| Tone | 3 | Constructive and concise. |

- Matched: snapshot_leak, race_in_inc
- Missed: unlocked_read
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
  "scores": {
    "recall": 2,
    "precision": 3,
    "severity_calibration": 1,
    "actionability": 2,
    "reasoning": 2,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Identifies snapshot_leak and race_in_inc, but misses the Count read/write synchronization defect.",
    "precision": "The findings describe real behavior or inefficiency in the diff; no fabricated or clearly false findings.",
    "severity_calibration": "The concurrent Inc race is rated Low despite being expected High, and the missed Count race is also High.",
    "actionability": "Provides concrete locations and fixes, but the Snapshot copy suggestion omits locking, and TryGetValue alone does not make Inc atomic.",
    "reasoning": "Correctly explains the exposed mutable dictionary and the check-then-act race in Inc, but does not identify Count's unsynchronized dictionary read.",
    "format": "Uses Summary, Findings, and Verdict sections, with findings ordered by severity.",
    "tone": "Constructive and concise."
  },
  "matched": [
    "snapshot_leak",
    "race_in_inc"
  ],
  "missed": [
    "unlocked_read"
  ],
  "false_positives": [],
  "typo_recall": null,
  "hard_fail": {
    "missed_critical": true,
    "fabricated": false,
    "missed_behavioral_typo": false
  }
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
