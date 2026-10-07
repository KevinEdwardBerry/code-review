---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 03-race-condition
date: 2026-10-07
reviewer_profile: subagent_explore
reviewer_model: subagent_explore default model
judge_profile: subagent_explore
judge_model: subagent_explore default model
weighted_score: 100.0
hard_fail: false
---

# 03-race-condition / v1


## Models
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model)

## AI response

### Summary
Adds a `RequestStats` class that counts requests per path using a `Dictionary<string, int>` with increment, lookup, and snapshot methods. The logic is correct for single-threaded use, but the class is not thread-safe and `Snapshot` leaks the mutable internal state — both significant for something named "request stats," which implies concurrent use in a server.

### Findings

- **[high] src/counter.cs:27 — `Snapshot()` returns the live internal dictionary**
  - Problem: Callers receive a reference to `counts` itself, so they can mutate internal state (e.g., `Snapshot().Clear()` or set arbitrary values), and worse, if `Inc` runs while a caller iterates the snapshot it throws `InvalidOperationException` ("collection was modified"). This silently breaks the encapsulation the class exists to provide.
  - Fix: Return a copy: `return new Dictionary<string, int>(counts);`

- **[high] src/counter.cs:7–24 — no thread safety on shared mutable state**
  - Problem: `Inc` uses a check-then-act pattern (`ContainsKey` then index write) on a `Dictionary`, which is not thread-safe. For a request-counter (typically hit from many threads concurrently), concurrent `Inc` calls can lose increments or corrupt the dictionary's internal buckets, which can cause crashes or hangs.
  - Fix: Either use `ConcurrentDictionary<string, int>` with `counts.AddOrUpdate(path, 1, (_, v) => v + 1)` (and `TryGetValue` in `Count`), or guard all three methods with a `lock` on a private object. If single-threaded use is intended, document it on the class.

- **[low] src/counter.cs:10, 20 — `null` path throws `ArgumentNullException`**
  - Problem: `Dictionary` indexer/`ContainsKey` throws on `null` keys. Whether that matters depends on callers (not visible in the diff), but a defensive `ArgumentNullException.ThrowIfNull(path)` — or normalizing null/empty to a default key — would make behavior explicit.
  - Fix: Add `ArgumentNullException.ThrowIfNull(path);` at the top of `Inc` and `Count`, or document that null is rejected.

### Verdict
Request changes — the internal-state leak via `Snapshot` and the missing synchronization are real defects for a request-stats type; both are one-line fixes (return a copy, lock or use `ConcurrentDictionary`).

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | All three must-find issues are covered: Snapshot leak is flagged explicitly at src/counter.cs:27; the check-then-act race in Inc is described in detail; and the unsynchronized Count read is covered by the same combined finding which explicitly says to 'guard all three methods with a lock' or use TryGetValue in Count. |
| Precision | 3 | No false positives. The extra null-path low finding is a genuine behavior (Dictionary indexer/ContainsKey throw on null keys), correctly hedged as dependent on unseen callers — trivial, acceptable noise rather than a hallucination. Dictionary usage and method names were not flagged, per must-not-flag. |
| Severity calibration | 3 | Both core defects rated [high], matching expected high/high-medium. The speculative null-key concern is appropriately demoted to [low]. |
| Actionability | 3 | Each finding has a concrete fix with correct file and line references: `new Dictionary<string, int>(counts)` for Snapshot, `ConcurrentDictionary.AddOrUpdate` or a lock covering all three methods for the race, and `ArgumentNullException.ThrowIfNull` for the low item. |
| Reasoning | 3 | Explanations are correct and describe real impact: mutation of internal state, InvalidOperationException on concurrent iteration, lost increments, and internal bucket corruption. Reasoning goes beyond surface-level. |
| Format | 3 | Exactly follows Summary / Findings / Verdict structure, findings ordered by severity (high, high, low). |
| Tone | 3 | Constructive, concise, no filler; verdict clearly explains rationale. |

- Matched: unlocked_read, snapshot_leak, race_in_inc
- Missed: none
- False positives: none
- Typo recall: null

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
  "scores": {
    "recall": 3,
    "precision": 3,
    "severity_calibration": 3,
    "actionability": 3,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "All three must-find issues are covered: Snapshot leak is flagged explicitly at src/counter.cs:27; the check-then-act race in Inc is described in detail; and the unsynchronized Count read is covered by the same combined finding which explicitly says to 'guard all three methods with a lock' or use TryGetValue in Count.",
    "precision": "No false positives. The extra null-path low finding is a genuine behavior (Dictionary indexer/ContainsKey throw on null keys), correctly hedged as dependent on unseen callers — trivial, acceptable noise rather than a hallucination. Dictionary usage and method names were not flagged, per must-not-flag.",
    "severity_calibration": "Both core defects rated [high], matching expected high/high-medium. The speculative null-key concern is appropriately demoted to [low].",
    "actionability": "Each finding has a concrete fix with correct file and line references: `new Dictionary<string, int>(counts)` for Snapshot, `ConcurrentDictionary.AddOrUpdate` or a lock covering all three methods for the race, and `ArgumentNullException.ThrowIfNull` for the low item.",
    "reasoning": "Explanations are correct and describe real impact: mutation of internal state, InvalidOperationException on concurrent iteration, lost increments, and internal bucket corruption. Reasoning goes beyond surface-level.",
    "format": "Exactly follows Summary / Findings / Verdict structure, findings ordered by severity (high, high, low).",
    "tone": "Constructive, concise, no filler; verdict clearly explains rationale."
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
