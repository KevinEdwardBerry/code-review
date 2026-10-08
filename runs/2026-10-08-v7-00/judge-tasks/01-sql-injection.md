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
diff --git a/src/users.sql b/src/users.sql
index 1a2b3c4..5d6e7f8 100644
--- a/src/users.sql
+++ b/src/users.sql
@@ -1,6 +1,18 @@
+-- User queries
 
 
+CREATE PROCEDURE FindUserByName
+    @name NVARCHAR(255)
+AS
+BEGIN
+    DECLARE @query NVARCHAR(MAX)
+    SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
+    EXEC sp_executesql @query
+END
+
+SELECT id, name, email FROM users WHERE name = '" + name + "'"


# EXPECTED
# Expected: 01-sql-injection

## Must find
- `sqli` (critical): src/users.sql `FindUserByName` builds SQL by string concatenation with user input (new lines 9-10). Fix: use parameterized query with `sp_executesql` properly: `EXEC sp_executesql N'SELECT id, name, email FROM users WHERE name = @name', N'@name NVARCHAR(255)', @name`.

## Acceptable extras (not false positives)
- low/nit: the additional query also shows SQL injection via string concatenation.

## Must not flag
- Use of T-SQL syntax, stored procedures, or the procedure name.

## Hard fail
- Missing `sqli` sets `missed_critical`.


# REVIEW
# Code Review: `src/users.sql`

## Critical Issues

### 1. SQL Injection (BLOCKER)
Both additions build SQL via string concatenation with unparameterized user input:

```sql
SET @query = 'SELECT id, name, email FROM users WHERE name = ''' + @name + ''''
EXEC sp_executesql @query
```
and
```sql
SELECT id, name, email FROM users WHERE name = '" + name + "'"
```

An input like `' OR '1'='1` or `'; DROP TABLE users; --` would execute arbitrary SQL. This defeats the entire purpose of a stored procedure.

**Fix** — the proc doesn't need dynamic SQL at all:
```sql
CREATE PROCEDURE FindUserByName
    @name NVARCHAR(255)
AS
BEGIN
    SELECT id, name, email FROM users WHERE name = @name;
END
```
If dynamic SQL were truly needed, use parameters: `EXEC sp_executesql @query, N'@name NVARCHAR(255)', @name`.

### 2. Invalid SQL Syntax (BLOCKER)
```sql
SELECT id, name, email FROM users WHERE name = '" + name + "'
```
This line sits at file top-level, outside any procedure, and mixes SQL with application-language string concatenation (`" + name + "`). It will fail to parse/execute as SQL. It looks like application code (e.g., PHP/JS) was accidentally pasted into the `.sql` file — it should be removed and replaced with a parameterized query in the calling code, or a call to the stored procedure.

## Minor Issues

- **Inconsistent style:** keywords are uppercase but there's no `;` statement terminators; `EXEC` lacks parentheses (valid, but `EXEC(...)` or `EXECUTE` is cleaner).
- **`NVARCHAR(MAX)`** for `@query` is unnecessary here, though harmless.
- No `SET NOCOUNT ON;` in the procedure (minor convention).
- The comment `-- User queries` followed by `+` on blank lines suggests formatting noise in the diff; ensure the file doesn't contain stray artifacts.

## Recommendation
Do not merge. Rewrite the procedure as a static parameterized query and delete the orphaned concatenated SELECT line entirely — and audit the application layer for any similar string-concatenated queries, since the pasted line suggests this pattern exists elsewhere.

