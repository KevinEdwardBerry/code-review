You are a strict, impartial evaluator of AI code reviews. Score the REVIEW against the EXPECTED findings using the RUBRIC.

Rules:
- Judge only against the EXPECTED file and the DIFF. Do not reward findings that are not real.
- Mark a finding as a match if it identifies the same defect at the same location, even if worded differently.
- A mechanical CITATION_CHECK (script output) is provided. Set `fabricated` true if it reports any problem, or if the review cites code/APIs not in the DIFF. Do not set `fabricated` for line numbers when CITATION_CHECK reports ok. Lower actionability for each reported citation problem.
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
- Flagging an item that is explicitly listed as `Must not flag` (e.g. a documented acceptable spelling, brand name, British/variant spelling in a proper name, or literal data explicitly marked as acceptable) is a false positive. Clear misspellings in string literals are in scope unless the project explicitly marks them as acceptable.
- Noise: a long list of nit typos that buries a high-impact one lowers Precision and Tone.

## Human overrides
The AI judge proposes scores. To override, fill the "Human override" section in the run file with the changed scores and a reason; the final totals use overrides where present.


# DIFF
diff --git a/src/counter.cs b/src/counter.cs
index 3c4d5e6..7f8091a 100644
--- a/src/counter.cs
+++ b/src/counter.cs
@@ -0,0 +1,39 @@
+using System;
+using System.Collections.Generic;
+using System.Linq;
+using System.Threading.Tasks;
+
+public class RequestStats
+{
+    private Dictionary<string, int> counts = [];
+
+    public void Inc(string path)
+    {
+        if (counts.TryGetValue(path, out var count))
+            counts[path] = count + 1;
+        else
+            counts[path] = 1;
+    }
+
+    public int Count(string path)
+    {
+        return counts.TryGetValue(path, out var count) ? count : 0;
+    }
+
+    public Dictionary<string, int> Snapshot()
+    {
+        return counts;
+    }
+}
+
+public class RequestHandler
+{
+    private readonly RequestStats stats = new RequestStats();
+
+    public async Task HandleAllAsync(IEnumerable<string> paths)
+    {
+        await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));
+    }
+
+    public int Total(string path) => stats.Count(path);
+}


# EXPECTED
# Expected: 03-race-condition

## Must find
- `unlocked_read` (high): `Count` reads `counts` without synchronization; concurrent read/write of the dictionary can cause data corruption or exceptions. Fix: use `lock` statement or `ReaderWriterLockSlim` in `Count`.
- `snapshot_leak` (high/medium): `Snapshot` returns the internal dictionary directly, exposing it to unsynchronized access by callers. Fix: copy the dictionary under lock.
- `race_in_inc` (high): `Inc` checks `ContainsKey` and then accesses/modifies the dictionary without atomicity; between the check and the increment, another thread could modify the same key. Fix: use `lock` statement around the entire operation.

## Context
- `RequestHandler.HandleAllAsync` calls `Inc` concurrently via `Task.Run`/`Task.WhenAll`, so `RequestStats` is shared across threads. This is the evidence that makes the races demonstrable.

## Acceptable extras
- nit: consider using `ConcurrentDictionary<string, int>` instead of `Dictionary<string, int>` with manual locking.

## Must not flag
- The use of Dictionary or the method names.
- The `RequestHandler` class itself or its use of `Task.Run`.

## Hard fail
- Missing `unlocked_read` and `snapshot_leak` sets `missed_critical`.


# CITATION_CHECK
{
  "citations_checked": 0,
  "problems": [],
  "ok": true
}


# REVIEW
# Code Review: `src/counter.cs`

## Summary
The code compiles and works correctly in single-threaded use, but `RequestHandler.HandleAllAsync` explicitly invokes `stats.Inc` from multiple threads via `Task.Run`/`Task.WhenAll`. That makes the underlying `Dictionary` race-prone — this is the central defect.

## Findings

### 🔴 Critical — `Dictionary<string,int>` is not thread-safe (lines 7–16, 32–36)
`Inc` performs a read-modify-write (`TryGetValue` then indexed set) and `HandleAllAsync` runs it concurrently. Consequences:
- **Lost updates**: two threads can both read count `N` and both write `N+1`.
- **Corruption**: concurrent writes during a dictionary resize can corrupt internal buckets, leading to infinite loops or `IndexOutOfRangeException` on later reads — a well-documented failure mode for `Dictionary`.
- Even `Count`/`Snapshot` reading while another thread writes is unsafe.

**Fix options:**
- Use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)` or `Interlocked` on the value.
- Or guard all access with a `lock`.
- Better still: since `Task.Run` parallelism here buys nothing for a cheap increment, just iterate sequentially — the simplest correct code.

### 🟠 Major — `Snapshot()` returns the live mutable dictionary (lines 25–28)
Callers get a direct reference to internal state: they can mutate it, and their reads race with concurrent `Inc` calls (enumerating a `Dictionary` during mutation throws `InvalidOperationException`). Return a copy:
```csharp
public Dictionary<string,int> Snapshot()
{
    lock (gate) return new Dictionary<string,int>(counts);
}
```
(or `ToDictionary`/`IReadOnlyDictionary`).

### 🟡 Minor — Parallelism overhead
`Task.Run` per path for an O(1) increment will usually be *slower* than a sequential loop due to thread-pool scheduling. If `paths` is large, consider `Parallel.ForEach` with partitioned local counters merged at the end.

### 🟡 Minor — `Inc` can be simplified
Single-indexer form is equivalent and avoids a double lookup... actually, the current two-step form is fine, but `counts[path] = counts.GetValueOrDefault(path) + 1;` is cleaner. Style only.

### ℹ️ Note — `counts` isn't marked `readonly`
`private readonly Dictionary<...> counts` would prevent accidental reassignment.

## Recommendation
Request changes. At minimum: replace the dictionary with `ConcurrentDictionary` + `AddOrUpdate`, make `Snapshot` return a copy, and seriously consider dropping `Task.Run` entirely unless there's real CPU-bound work to parallelize.

