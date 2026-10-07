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
diff --git a/src/pagination.js b/src/pagination.js
index 2b3c4d5..6e7f809 100644
--- a/src/pagination.js
+++ b/src/pagination.js
@@ -1,3 +1,22 @@
 // Pagination helpers
 
+/**
+ * Returns the items for a 1-based page number.
+ */
+function getPage(items, page, pageSize) {
+  const start = page * pageSize;
+  const end = start + pageSize;
+  return items.slice(start, end);
+}
+
+/**
+ * Returns the total number of pages.
+ */
+function totalPages(items, pageSize) {
+  return Math.floor(items.length / pageSize);
+}
+
+module.exports = { getPage, totalPages };


# EXPECTED
# Expected: 02-off-by-one

## Must find
- `page_offset` (high): `getPage` documents a 1-based page but computes `start = page * pageSize`; page 1 skips the first page of items. Fix: `(page - 1) * pageSize`.
- `total_pages_floor` (medium): `totalPages` uses `Math.floor`, dropping the final partial page. Fix: `Math.ceil`.

## Acceptable extras
- low/nit: no validation for page < 1 or pageSize <= 0 (division by zero gives Infinity).

## Must not flag
- Use of `module.exports`, or the style of the JSDoc comments.

## Hard fail
- Missing `page_offset` sets `missed_critical` (high).


# REVIEW
### Summary
Adds `getPage` and `totalPages` pagination helpers, but both contain off-by-one/truncation bugs: `getPage` treats `page` as 0-based despite documenting 1-based input, and `totalPages` floors instead of ceiling, dropping the last partial page.

### Findings
- **high src/pagination.js:6 - `getPage` uses 0-based offset despite 1-based contract**
  - Problem: The docstring says `page` is 1-based, but `start = page * pageSize` skips the first `pageSize` items on page 1 and returns the wrong slice for every page (page 1 returns items `pageSize..2*pageSize`, etc.).
  - Fix: Use `const start = (page - 1) * pageSize;`.
  - Code snippet:
    ```js
    const start = page * pageSize;
    ```

- **high src/pagination.js:15 - `totalPages` drops the last partial page**
  - Problem: `Math.floor(items.length / pageSize)` undercounts whenever `items.length` is not an exact multiple of `pageSize` (e.g. 25 items, pageSize 10 → 2 instead of 3), making the final page unreachable.
  - Fix: Use `Math.ceil(items.length / pageSize)`.
  - Code snippet:
    ```js
    return Math.floor(items.length / pageSize);
    ```

- **medium src/pagination.js:6-7 - invalid `page`/`pageSize` inputs produce silent wrong results**
  - Problem: `page <= 0` yields a negative `start`, so `items.slice` returns trailing items rather than an error or empty page; `pageSize <= 0` yields `NaN` (`totalPages`) or empty/incorrect slices. With 1-based semantics, page 0 should not silently return data.
  - Fix: Validate inputs, e.g. `if (page < 1) throw/return []` and `if (pageSize < 1) throw/return 0`, or clamp to valid ranges per intended contract.
  - Code snippet:
    ```js
    const start = page * pageSize;
    const end = start + pageSize;
    ```

### Verdict
request changes

