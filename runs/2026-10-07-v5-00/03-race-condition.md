---
prompt_version: v5
prompt_file: prompts/code-review.v5.md
fixture: 03-race-condition
date: 2026-10-07
reviewer_model: subagent_explore (default subagent model)
reviewer_profile: subagent_explore
judge_model: subagent_general (parent model)
judge_profile: subagent_general
weighted_score: 75.0
hard_fail: true
---

# 03-race-condition / v5

## Models
- Reviewer: subagent_explore (subagent_explore (default subagent model))
- Judge: subagent_general (subagent_general (parent model))

## AI response

### Summary
The change adds a `RequestStats` class that counts requests per path using a plain `Dictionary<string, int>`. It is simple and correct for single-threaded use, but it has two real defects: it is not thread-safe and `Snapshot` leaks the mutable internal state.

### Findings
- **[high] src/counter.cs:10-17 - `Inc` is not thread-safe**
  - Problem: A request counter is almost always invoked concurrently. `Dictionary` does not tolerate concurrent mutation; two simultaneous `Inc` calls can lose increments, and concurrent write/read can corrupt internal buckets (in older runtimes this could even hang or throw). No locking or `ConcurrentDictionary` is used.
  - Fix: Use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or guard all accesses with a `lock`.
  - Code snippet:
    ```
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    ```

- **[medium] src/counter.cs:29 - `Snapshot` returns the mutable internal dictionary**
  - Problem: `return counts;` hands callers a live reference to private state. Callers can mutate it (corrupting stats), and iterating it while `Inc` runs throws `InvalidOperationException` — making it both an encapsulation break and a crash vector combined with the thread-safety issue above.
  - Fix: Return a copy, e.g. `return new Dictionary<string, int>(counts);` (under the lock / after `ToArray` if made concurrent), or expose `IReadOnlyDictionary` over a copied snapshot.
  - Code snippet:
    ```
    return counts;
    ```

### Verdict
request changes

## Judge scores (AI)

| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 1 | Found `race_in_inc` (Inc thread-safety) and `snapshot_leak` (Snapshot internal dictionary leak) but missed the high-severity `unlocked_read` issue in `Count`. Since a high must-find was omitted, it does not satisfy 'all must-find' or 'all but one minor' for a higher recall band. |
| Precision | 3 | The review only identifies real defects; it suggests `ConcurrentDictionary` as an acceptable extra and does not flag any must-not-flag items. No false positives. |
| Severity calibration | 3 | `Inc` is correctly ranked high and `Snapshot` is ranked medium, which matches the expected high/medium range for `snapshot_leak`. |
| Actionability | 2 | Each raised finding includes a concrete code fix, but the `Snapshot` line reference (counter.cs:29) is off by one from the actual `return counts;` line, so it loses the 'correct file:line for each finding' top mark. |
| Reasoning | 3 | Explanations correctly describe the impact of the concurrency defect (lost increments, dictionary corruption/throws) and the encapsulation/crash risk of exposing the internal dictionary. |
| Format | 3 | Follows Summary / Findings / Verdict, with findings ordered from high to medium severity and consistent formatting. |
| Tone | 3 | Constructive, professional, and concise with no filler or rudeness. |

- Matched: [race_in_inc, snapshot_leak]
- Missed: [unlocked_read]
- False positives: []
- Typo recall: n/a

Hard fail: `missed_critical` = true

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
  "scores": {
    "recall": 1,
    "precision": 3,
    "severity_calibration": 3,
    "actionability": 2,
    "reasoning": 3,
    "format": 3,
    "tone": 3
  },
  "rationale": {
    "recall": "Found `race_in_inc` (Inc thread-safety) and `snapshot_leak` (Snapshot internal dictionary leak) but missed the high-severity `unlocked_read` issue in `Count`. Since a high must-find was omitted, it does not satisfy 'all must-find' or 'all but one minor' for a higher recall band.",
    "precision": "The review only identifies real defects; it suggests `ConcurrentDictionary` as an acceptable extra and does not flag any must-not-flag items. No false positives.",
    "severity_calibration": "`Inc` is correctly ranked high and `Snapshot` is ranked medium, which matches the expected high/medium range for `snapshot_leak`.",
    "actionability": "Each raised finding includes a concrete code fix, but the `Snapshot` line reference (counter.cs:29) is off by one from the actual `return counts;` line, so it loses the 'correct file:line for each finding' top mark.",
    "reasoning": "Explanations correctly describe the impact of the concurrency defect (lost increments, dictionary corruption/throws) and the encapsulation/crash risk of exposing the internal dictionary.",
    "format": "Follows Summary / Findings / Verdict, with findings ordered from high to medium severity and consistent formatting.",
    "tone": "Constructive, professional, and concise with no filler or rudeness."
  },
  "matched": ["race_in_inc", "snapshot_leak"],
  "missed": ["unlocked_read"],
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
