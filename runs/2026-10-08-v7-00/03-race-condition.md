---
prompt_version: v7
prompt_file: prompts/code-review-v7.md
fixture: 03-race-condition
date: 2026-10-08
reviewer_model: unknown concrete model
reviewer_profile: subagent_explore
judge_model: unknown concrete model
judge_profile: subagent_general
weighted_score: 75.0
hard_fail: none
---

# 03-race-condition / v7

## Models
- Reviewer: subagent_explore (unknown concrete model)
- Judge: subagent_general (unknown concrete model)

## AI response
## Code Review: `src/counter.cs`

### 🔴 Correctness / API design issues

1. **`Snapshot()` returns the internal mutable dictionary** (line ~26)
   - Callers can mutate, clear, or corrupt internal state: `stats.Snapshot()["/admin"] = 999;`
   - Fix: return a copy (`new Dictionary<string,int>(counts)`) or expose `IReadOnlyDictionary<string,int>`.

2. **Not thread-safe**
   - A request-stats counter is almost certainly incremented from concurrent request threads. `Dictionary` is not safe for concurrent read/write — `Inc` can lose updates or corrupt internal buckets.
   - Fix: use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd`, or guard all access with a `lock`.

3. **`Inc(null)` throws `ArgumentNullException`**
   - `Dictionary` does not accept null keys. Either validate (`ArgumentNullException.ThrowIfNull(path)`) explicitly or document the contract.

### 🟡 Minor / style

4. **Double lookup** — `ContainsKey` + indexer performs two hash lookups. Prefer `TryGetValue`:
   ```csharp
   counts.TryGetValue(path, out int n);
   counts[path] = n + 1;
   ```
   (Or `CollectionsMarshal.GetValueRefOrAddDefault` for a single lookup.)

5. **File/class name mismatch** — file is `counter.cs` but declares `public class RequestStats`. Convention is `RequestStats.cs`; some tooling/builds expect this.

6. **No namespace** — the class lands in the global namespace; wrap it in the project's namespace.

7. **Field could be `readonly`** — `counts` is never reassigned: `private readonly Dictionary<string,int> counts = new();`

8. **`Count` duplicates lookup logic** — could be `counts.TryGetValue(path, out var n) ? n : 0`.

### Suggested rewrite

```csharp
using System.Collections.Concurrent;
using System.Collections.Generic;

public sealed class RequestStats
{
    private readonly ConcurrentDictionary<string, int> counts = new();

    public void Inc(string path)
    {
        ArgumentNullException.ThrowIfNull(path);
        counts.AddOrUpdate(path, 1, (_, n) => n + 1);
    }

    public int Count(string path) => counts.TryGetValue(path, out var n) ? n : 0;

    public IReadOnlyDictionary<string, int> Snapshot() =>
        new Dictionary<string, int>(counts);
}
```

**Verdict:** Works for single-threaded use, but the mutable `Snapshot()` leak and lack of thread safety should be fixed before merge, given this is clearly intended to count HTTP requests.


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Finds the Snapshot internal-dictionary leak (snapshot_leak), the Inc race between ContainsKey and update (race_in_inc), and the broader unlocked Dictionary read/write issue that covers Count (unlocked_read). |
| Precision | 1 | Several unseeded extras: Inc(null) throwing ArgumentNullException, file/class name mismatch, missing namespace, readonly field, double lookup, and Count lookup duplication. |
| Severity calibration | 2 | Major issues are grouped under correctness and nits under style, but the null-key item is elevated to correctness while the expected set treats it as irrelevant. |
| Actionability | 2 | Concrete rewrites and fixes are given for the real issues, though line references are approximate and the thread-safety point lacks an exact file:line. |
| Reasoning correctness | 3 | Correctly explains the mutable Snapshot leak and why Dictionary is unsafe for concurrent read/write. |
| Format adherence | 2 | Has sections and a Verdict, but deviates from a clean Summary/Findings/Verdict ordering by mixing major and minor items. |
| Tone and concision | 3 | Constructive and focused, with no rude or excessive filler. |

- Matched: unlocked_read, snapshot_leak, race_in_inc
- Missed: none
- False positives: "Inc(null) throws ArgumentNullException"; "File/class name mismatch"; "No namespace"; "Field counts could be readonly"; "Double lookup in Inc"; "Count duplicates lookup logic"
- Typo recall: N/A

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "03-race-condition",
  "scores": {
    "recall": 3,
    "precision": 1,
    "severity_calibration": 2,
    "actionability": 2,
    "reasoning": 3,
    "format": 2,
    "tone": 3
  },
  "rationale": {
    "recall": "Finds the Snapshot internal-dictionary leak (snapshot_leak), the Inc race between ContainsKey and update (race_in_inc), and the broader unlocked Dictionary read/write issue that covers Count (unlocked_read).",
    "precision": "Several unseeded extras: Inc(null) throwing ArgumentNullException, file/class name mismatch, missing namespace, readonly field, double lookup, and Count lookup duplication.",
    "severity_calibration": "Major issues are grouped under correctness and nits under style, but the null-key item is elevated to correctness while the expected set treats it as irrelevant.",
    "actionability": "Concrete rewrites and fixes are given for the real issues, though line references are approximate and the thread-safety point lacks an exact file:line.",
    "reasoning": "Correctly explains the mutable Snapshot leak and why Dictionary is unsafe for concurrent read/write.",
    "format": "Has sections and a Verdict, but deviates from a clean Summary/Findings/Verdict ordering by mixing major and minor items.",
    "tone": "Constructive and focused, with no rude or excessive filler."
  },
  "matched": [
    "unlocked_read",
    "snapshot_leak",
    "race_in_inc"
  ],
  "missed": [],
  "false_positives": [
    "Inc(null) throws ArgumentNullException",
    "File/class name mismatch",
    "No namespace",
    "Field counts could be readonly",
    "Double lookup in Inc",
    "Count duplicates lookup logic"
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
