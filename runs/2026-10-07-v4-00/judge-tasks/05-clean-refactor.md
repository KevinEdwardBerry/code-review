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
### Summary
The change refactors `OrderCalculator.OrderTotal` from an explicit accumulation loop to a LINQ `Sum`, and replaces `total + total * taxRate` with `subtotal * (1 + taxRate)`. The refactor is cleaner, but the tax computation reordering can produce different rounding results for `decimal` arithmetic.

### Findings
- **medium** src/totals.cs:12 - Reordered tax calculation can yield different decimal rounding
  - Problem: The original computed `total + (total * taxRate)`; the new code computes `subtotal * (1 + taxRate)`. These are mathematically equivalent but not computally equivalent for `decimal`, which has finite (~28–29 digit) precision and rounds intermediate results. The original rounds `total * taxRate` first and then adds; the new version adds `1 + taxRate` and rounds a single product. For subtotals/rates whose products exceed the precision limit (large totals or rates with many significant digits), the two expressions can differ by a cent, silently changing billing output compared to the prior released behavior.
  - Fix: If bit-for-bit parity with the previous behavior matters, keep the two-step form: `decimal tax = subtotal * taxRate; return subtotal + tax;`. Otherwise, add/verify unit tests covering rounding-sensitive totals and confirm the new rounding is acceptable.
  - Code snippet:
    ```
    +        decimal subtotal = items.Sum(item => item.Price * item.Quantity);
    +        return subtotal * (1 + taxRate);
    ```

- **low** src/totals.cs:11 - `items.Sum` changes the null-argument failure mode slightly
  - Problem: With a null `items` argument, both versions throw, but `Enumerable.Sum` throws `ArgumentNullException` (documented, via `ArgumentNullException.ThrowIfNull`) whereas the old `foreach` threw `NullReferenceException`. Any caller or test asserting `NullReferenceException` would break. This is a minor contract surface change; also note `Sum` on an empty list returns `0m`, matching the old loop, so no issue there.
  - Fix: No code change strictly required; consider an explicit `ArgumentNullException.ThrowIfNull(items)` at the top for clarity, and update any tests that assert the old exception type.
  - Code snippet:
    ```
    +        decimal subtotal = items.Sum(item => item.Price * item.Quantity);
    ```

- **nit** src/totals.cs:1-3 - New `using System;` may be unnecessary
  - Problem: `using System;` was added but nothing in the shown code obviously requires it beyond `ArgumentNullException`/`Console`-type members; `List<>` needs `System.Collections.Generic` and `Sum` needs `System.Linq`. In a file-scoped snippet this is likely harmless, but if the project treats unused usings as warnings it could flag.
  - Fix: Remove `using System;` if it is genuinely unused, or keep it if `Item`/other members in the file require it (context is truncated).
  - Code snippet:
    ```
    +using System;
    ```

### Verdict
approve with nits

