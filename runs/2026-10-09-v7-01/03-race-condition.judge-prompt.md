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
- `race_in_inc` (high): `Inc` does a check-then-act on a plain `Dictionary`: `TryGetValue` at `src/counter.cs:12`, then `counts[path] = count + 1;` at `src/counter.cs:13` (or `counts[path] = 1;` at `src/counter.cs:15`). Concurrent callers can lose increments or corrupt the dictionary. Fix: take a `lock` around the whole operation, or use `ConcurrentDictionary.AddOrUpdate`. The concurrent call site at `src/counter.cs:35` is acceptable supporting evidence and may be cited as part of this finding or as its own finding.
- `unlocked_read` (medium): `Count` reads `counts` without synchronization at `src/counter.cs:20` (`return counts.TryGetValue(path, out var count) ? count : 0;`) while `Inc` can write concurrently. Fix: read under the same `lock`, or use `ConcurrentDictionary`.
- `snapshot_leak` (medium): `Snapshot` returns the internal dictionary directly at `src/counter.cs:25` (`return counts;`), exposing it to unsynchronized enumeration and mutation by callers. Fix: return a copy made under the lock.

## Context
- `RequestHandler.HandleAllAsync` calls `Inc` concurrently via `Task.Run`/`Task.WhenAll` (`src/counter.cs:35`), so `RequestStats` is shared across threads. This is the evidence that makes the races demonstrable.
- Each unsynchronized access (`Inc`, `Count`, `Snapshot`) must be reviewed as its own path and anchored to its own line.

## Acceptable extras
- nit: consider using `ConcurrentDictionary<string, int>` instead of `Dictionary<string, int>` with manual locking.

## Must not flag
- The use of Dictionary or the method names.
- The `RequestHandler` class itself or its use of `Task.Run`, except as the evidence for the race.

## Hard fail
- Missing `race_in_inc` sets `missed_critical` (high).
- Missing both `unlocked_read` and `snapshot_leak` sets `missed_critical`.


# CITATION_CHECK
{
  "citations_checked": 4,
  "problems": [],
  "ok": true
}


# REVIEW
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

