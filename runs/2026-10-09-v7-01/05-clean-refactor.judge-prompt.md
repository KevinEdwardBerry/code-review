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
diff --git a/src/totals.cs b/src/totals.cs
index 5e6f708..91a2b3c 100644
--- a/src/totals.cs
+++ b/src/totals.cs
@@ -1,17 +1,11 @@
 using System.Collections.Generic;
+using System.Linq;
 
-public class OrderCalculator
+public class OrderCalculator
 {
-    public decimal OrderTotal(List<Item> items, decimal taxRate)
+    public decimal OrderTotal(List<Item> items, decimal taxRate)
     {
-        var total = 0m;
-
-        foreach (var item in items)
-        {
-            total = total + item.Price * item.Quantity;
-        }
-
-        var tax = total * taxRate;
-        return total + tax;
+        var subtotal = items.Sum(item => item.Price * item.Quantity);
+        return subtotal * (1 + taxRate);
     }
 }


# EXPECTED
# Expected: 05-clean-refactor

The change replaces a manual accumulation loop and separate tax step in `OrderTotal` with LINQ `Sum` and `subtotal * (1 + taxRate)`. It is a behavior-preserving refactor. There are no seeded issues.

## Must find
- None. The ideal review is `None.` under Findings.

## Acceptable extras
- nit (Low): add unit tests for the refactored method.

## Must not flag (false positives)
- Any claim that the arithmetic or result changed (including decimal rounding or associativity speculation).
- Style complaints about using `Sum` or LINQ.
- The removed and re-added `public class OrderCalculator` and `public decimal OrderTotal(...)` lines: they are textually identical and are diff churn, not a change.
- Any critical/high/medium finding.

Ideal verdict: approve or approve with nits.


# CITATION_CHECK
{
  "citations_checked": 0,
  "problems": [],
  "ok": true
}


# REVIEW
## Summary
Low-risk refactor replacing a manual accumulation loop with LINQ `Sum`; behavior is equivalent.

## Findings
None.

## Verdict
Approve

