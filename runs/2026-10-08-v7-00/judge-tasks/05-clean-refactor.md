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
diff --git a/src/totals.cs b/src/totals.cs
index 5e6f708..91a2b3c 100644
--- a/src/totals.cs
+++ b/src/totals.cs
@@ -1,14 +1,12 @@
+using System;
+using System.Collections.Generic;
+using System.Linq;
 
-public class OrderCalculator
+public class OrderCalculator
 {
-    public decimal OrderTotal(List<Item> items, decimal taxRate)
+    public decimal OrderTotal(List<Item> items, decimal taxRate)
     {
-        decimal total = 0;
-        foreach (var item in items)
-        {
-            total = total + item.Price * item.Quantity;
-        }
-        decimal tax = total * taxRate;
-        return total + tax;
+        decimal subtotal = items.Sum(item => item.Price * item.Quantity);
+        return subtotal * (1 + taxRate);
     }
 }


# EXPECTED
# Expected: 05-clean-refactor

The change is a behavior-preserving refactor using LINQ's `Sum` method. There are no seeded issues.

## Must find
- None.

## Acceptable extras
- nit: add a comment that `taxRate` should be a `decimal` to avoid type coercion issues, or add unit tests.

## Must not flag (false positives)
- Any claim that the arithmetic changed behavior.
- Style complaints about using `Sum` or LINQ.
- Any critical/high/medium finding.

Ideal verdict: approve or approve with nits.


# REVIEW
Code review findings:

## Summary
The refactor replaces a manual accumulation loop with LINQ `Sum` and consolidates the tax calculation into a single expression. Functionally equivalent, but there are a few points worth noting.

## Findings

**1. Correctness — equivalent, with one subtle improvement (no severity: low/nit)**
- `subtotal * (1 + taxRate)` is mathematically identical to `total + total * taxRate`, and arguably clearer in intent.
- One minor difference: the old code computed `total * taxRate` first, then added. Floating-point rounding for `decimal` can differ microscopically between `t + t*r` and `t*(1+r)` in edge cases, but for `decimal` this is essentially a non-issue.

**2. Missing `Item` type context**
- `Item` is referenced but its definition isn't in the diff. If `Price` or `Quantity` aren't `decimal`/`int` respectively (e.g., `double` Price), `item.Price * item.Quantity` would resolve to a different `Sum` overload. Worth confirming types, though presumably it compiled.

**3. Null handling — unchanged behavior (info)**
- `items.Sum(...)` throws `ArgumentNullException` on a null list; the old `foreach` threw `NullReferenceException`. Neither handles null gracefully — behavior still broken on null input, just with a different exception. If null is a real possibility, consider `items?.Sum(...) ?? 0m`.

**4. Overflow semantics — unchanged (info)**
- `decimal` arithmetic throws `OverflowException` on overflow rather than wrapping, same as before. No change.

**5. Style**
- The added `using System;` and `using System.Collections.Generic;` may already exist elsewhere or be unnecessary if this file previously relied on implicit usings/global usings — verify no duplicate/unused usings. `System` isn't needed for anything visible here.
- `Sum` iterates once — same O(n) performance as the loop; allocation of the lambda delegate is negligible (compiler may cache it).

## Verdict
Approve. The change is a clean, idiomatic simplification. Only actionable nits: consider null-safety on `items` if callers may pass null, and trim the unused `using System;`.

