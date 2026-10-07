You are a strict, impartial evaluator of AI code reviews. Score the REVIEW against the EXPECTED findings using the RUBRIC.

Rules:
- Judge only against the EXPECTED file and the DIFF. Do not reward findings that are not real.
- Mark a finding as a match if it identifies the same defect at the same location, even if worded differently.
- Verify every cited line/code in the review exists in the DIFF; otherwise set `fabricated` true.
- Output ONLY valid JSON, no prose, no code fences, matching the schema below.

Schema:
{
  "fixture": "<fixture name>",
  "scores": {
    "recall": 0-3,
    "precision": 0-3,
    "severity_calibration": 0-3,
    "actionability": 0-3,
    "reasoning": 0-3,
    "format": 0-3,
    "tone": 0-3
  },
  "rationale": {
    "recall": "...", "precision": "...", "severity_calibration": "...",
    "actionability": "...", "reasoning": "...", "format": "...", "tone": "..."
  },
  "matched": ["<expected item id>", ...],
  "missed": ["<expected item id>", ...],
  "false_positives": ["<short description>", ...],
  "typo_recall": {"misspelling": "found/total", "swap": "found/total", "missing_letter": "found/total"},
  "hard_fail": {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}
}

`typo_recall` is only required for the typos fixture; use null elsewhere.

# RUBRIC
# Rubric

Each criterion is scored 0-3 per fixture. Weighted total = sum(score/3 * weight), out of 100.

| # | Criterion | Weight | 0 | 1 | 2 | 3 |
|---|-----------|--------|---|---|---|---|
| 1 | Recall | 30 | Finds none of the seeded issues | Finds under half | Finds most (all must-find, or all but one minor) | Finds every seeded issue |
| 2 | Precision | 20 | Several false positives / hallucinations | One clear false positive or flags a must-not-flag item | Only trivial noise | No false positives; clean diff yields no/nit-only findings |
| 3 | Severity calibration | 15 | Severities inverted or absent | Several wrong | One off by one level | All match expected (within one level for nits) |
| 4 | Actionability | 15 | No fixes | Vague fixes | Concrete fixes, some missing line refs | Concrete fix and correct file:line for each finding |
| 5 | Reasoning correctness | 10 | Explanations wrong | Partly wrong | Correct but shallow | Correct and explains impact |
| 6 | Format adherence | 5 | Ignores format | Partially follows | Minor deviations | Exactly follows Summary / Findings / Verdict, ordered by severity |
| 7 | Tone and concision | 5 | Rude or very noisy | Noisy | Mostly focused | Constructive, no filler |

## Hard-fail flags
Set a flag to true when it applies; the fixture is marked FAIL regardless of score.
- `missed_critical`: a critical or high expected issue was not found.
- `fabricated`: cites code, lines, or APIs that are not in the diff.
- `missed_behavioral_typo`: a behavior-changing typo (misspelled identifier/key) was not found.

## Typos fixture (06) extras
- Report recall per typo category: `misspelling`, `swap`, `missing_letter`.
- Behavior-changing typos must be ranked above cosmetic ones (severity calibration).
- Flagging any must-not-flag item counts as a false positive.
- Noise: a long list of nit typos that buries a high-impact one lowers Precision and Tone.

## Human overrides
The AI judge proposes scores. To override, fill the "Human override" section in the run file with the changed scores and a reason; the final totals use overrides where present.


# DIFF
diff --git a/src/counter.cs b/src/counter.cs
index 3c4d5e6..7f8091a 100644
--- a/src/counter.cs
+++ b/src/counter.cs
@@ -1,3 +1,28 @@
+using System;
+using System.Collections.Generic;
+
+public class RequestStats
+{
+    private Dictionary<string, int> counts = new Dictionary<string, int>();
+
+    // Inc records one request for the given path.
+    public void Inc(string path)
+    {
+        if (counts.ContainsKey(path))
+        {
+            counts[path]++;
+        }
+        else
+        {
+            counts[path] = 1;
+        }
+    }
+
+    // Count returns the number of requests recorded for the given path.
+    public int Count(string path)
+    {
+        return counts.ContainsKey(path) ? counts[path] : 0;
+    }
+
+    // Snapshot returns the current counts.
+    public Dictionary<string, int> Snapshot()
+    {
+        return counts;
+    }
+}


# EXPECTED
# Expected: 03-race-condition

## Must find
- `unlocked_read` (high): `Count` reads `counts` without synchronization; concurrent read/write of the dictionary can cause data corruption or exceptions. Fix: use `lock` statement or `ReaderWriterLockSlim` in `Count`.
- `snapshot_leak` (high/medium): `Snapshot` returns the internal dictionary directly, exposing it to unsynchronized access by callers. Fix: copy the dictionary under lock.
- `race_in_inc` (high): `Inc` checks `ContainsKey` and then accesses/modifies the dictionary without atomicity; between the check and the increment, another thread could modify the same key. Fix: use `lock` statement around the entire operation.

## Acceptable extras
- nit: consider using `ConcurrentDictionary<string, int>` instead of `Dictionary<string, int>` with manual locking.

## Must not flag
- The use of Dictionary or the method names.

## Hard fail
- Missing `unlocked_read` and `snapshot_leak` sets `missed_critical`.


# REVIEW
### Summary
The change adds a `RequestStats` class that counts requests per path using a plain `Dictionary<string, int>` with a check-then-act pattern. It is not thread-safe despite clearly being intended for concurrent request tracking, and `Snapshot()` leaks the mutable internal state.

### Findings
- **critical** src/counter.cs:13-21 - Race condition in `Inc` corrupts the dictionary and loses counts
  - Problem: `counts.ContainsKey(path)` followed by `counts[path]++` / `counts[path] = 1` is a non-atomic check-then-act. Concurrent calls can both miss the key and overwrite each other (lost updates), and concurrent writes/reads on a `Dictionary<K,V>` can corrupt internal buckets, throw `NullReferenceException`/`IndexOutOfRangeException`, or hang readers — a real corrupting race for a per-request counter.
  - Fix: Guard all access with a `lock` (or `ReaderWriterLockSlim`), or use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`.
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    else
    {
        counts[path] = 1;
    }
    ```

- **high** src/counter.cs:27-30 - `Snapshot()` returns the live internal dictionary
  - Problem: Returning `counts` directly exposes mutable internal state: callers can mutate counts, and any caller that enumerates the returned dictionary while `Inc` runs will hit `InvalidOperationException` ("collection was modified") or observe torn data. It also defeats any future locking since readers bypass the lock.
  - Fix: Return a copy under the lock, e.g. `lock (gate) return new Dictionary<string,int>(counts);` (or an `IReadOnlyDictionary` snapshot).
  - Code snippet:
    ```csharp
    public Dictionary<string, int> Snapshot()
    {
        return counts;
    }
    ```

- **medium** src/counter.cs:24-25 - `Count` performs an unsynchronized read
  - Problem: Even if `Inc` were fixed, `Count` reads `counts` without synchronization; concurrent `Dictionary` read+write is undefined and can throw or return garbage. It also does two lookups (`ContainsKey` + indexer) — correct but wasteful.
  - Fix: Read under the same lock and use `TryGetValue`: `lock (gate) { return counts.TryGetValue(path, out var c) ? c : 0; }`
  - Code snippet:
    ```csharp
    return counts.ContainsKey(path) ? counts[path] : 0;
    ```

- **low** src/counter.cs:13 - `Inc` does two dictionary lookups per call
  - Problem: The `ContainsKey` + indexer/setter pattern performs two hash lookups; a single `TryGetValue` (under the lock) is simpler and faster.
  - Fix: `if (counts.TryGetValue(path, out var c)) counts[path] = c + 1; else counts[path] = 1;` — or use `CollectionsMarshal.GetValueRefOrAddDefault` for a single lookup.
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path)) { counts[path]++; }
    ```

### Verdict
request changes

