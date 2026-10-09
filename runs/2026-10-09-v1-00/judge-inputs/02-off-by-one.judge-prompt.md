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
diff --git a/src/pagination.js b/src/pagination.js
index 2b3c4d5..6e7f809 100644
--- a/src/pagination.js
+++ b/src/pagination.js
@@ -1,2 +1,19 @@
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


# CITATION_CHECK
{
  "citations_checked": 0,
  "problems": [],
  "ok": true
}


# REVIEW
# Code Review: `src/pagination.js`

**Verdict: Request changes** — both functions contain correctness bugs.

## Critical issues

### 1. Off-by-one error in `getPage` (line ~7)
The docstring says pages are 1-based, but the math is 0-based:

```js
const start = page * pageSize;   // BUG
const start = (page - 1) * pageSize;  // correct for 1-based
```

As written, `getPage(items, 1, 10)` skips the first 10 items and returns items 10–19. Page 1 would silently drop data — the worst kind of pagination bug since nothing crashes.

### 2. `totalPages` drops the partial last page (line ~15)

```js
return Math.floor(items.length / pageSize);  // BUG
return Math.ceil(items.length / pageSize);   // correct
```

With 25 items and pageSize 10, this returns 2 instead of 3, so the last 5 items are unreachable. Combined with bug 1, data loss in both directions.

## Additional concerns

- **No input validation**: `pageSize <= 0` yields `Infinity`/`NaN` from `totalPages` and odd slices from `getPage`. `page < 1` produces negative indices (`slice` silently wraps to end-of-array — very surprising behavior). Consider throwing on `page < 1`, `pageSize < 1`, or non-integer inputs.
- **Out-of-range `page`**: returns `[]` silently, which may be acceptable, but worth documenting.
- **Naming**: `totalPages` takes `items` (the array) rather than a count — fine, but naming the param `items` while `getPage` also takes `items` is consistent, so OK. Just flagging that a `count`-based variant is often more reusable.
- **Mutability/copy**: `slice` returns a shallow copy — good, but the JSDoc should specify return type (`Array`, `number`) and `@param`/`@returns` tags for consistency with typical doc style.

## Suggested fix

```js
function getPage(items, page, pageSize) {
  if (pageSize < 1) throw new RangeError('pageSize must be >= 1');
  if (page < 1) throw new RangeError('page must be >= 1');
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

function totalPages(items, pageSize) {
  if (pageSize < 1) throw new RangeError('pageSize must be >= 1');
  return Math.ceil(items.length / pageSize);
}
```

**Tests to add before merging**: page 1 boundary, last partial page, empty array, `pageSize` > length, and invalid inputs. These are exactly the cases that would have caught both bugs.

