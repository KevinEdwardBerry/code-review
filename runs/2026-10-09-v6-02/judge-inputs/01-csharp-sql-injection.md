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
diff --git a/src/CustomerRepository.cs b/src/CustomerRepository.cs
new file mode 100644
--- /dev/null
+++ b/src/CustomerRepository.cs
@@ -0,0 +1,23 @@
+using Microsoft.Data.SqlClient;
+
+public sealed record Customer(int Id, string Email);
+
+public sealed class CustomerRepository(string connectionString)
+{
+    public async Task<Customer?> FindByEmailAsync(
+        string email,
+        CancellationToken cancellationToken = default)
+    {
+        await using var connection = new SqlConnection(connectionString);
+        await connection.OpenAsync(cancellationToken);
+
+        var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";
+        await using var command = new SqlCommand(sql, connection);
+        await using var reader = await command.ExecuteReaderAsync(cancellationToken);
+
+        if (!await reader.ReadAsync(cancellationToken))
+            return null;
+
+        return new Customer(reader.GetInt32(0), reader.GetString(1));
+    }
+}


# EXPECTED
# Expected: 01-csharp-sql-injection

## Must find
- `sqli_email` (critical): `FindByEmailAsync` interpolates the caller-controlled `email` value into SQL at `src/CustomerRepository.cs:14` (`var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`). An email containing SQL syntax can alter the predicate or inject additional SQL when the command executes. Fix: use a parameterized query (`WHERE Email = @email`) and bind `email` through a `SqlCommand` parameter with the appropriate database type.

## Must not flag
- The use of `Microsoft.Data.SqlClient`, async disposal, the repository/record declarations, or cancellation-token handling.
- The possibility of SQL injection from any line other than the interpolated SQL statement; report this as one finding anchored to the vulnerable line.

## Hard fail
- Missing `sqli_email` sets `missed_critical`.


# CITATION_CHECK
{
  "citations_checked": 1,
  "problems": [],
  "ok": true
}


# REVIEW
## Summary
New `CustomerRepository` that builds a SQL query via string interpolation, introducing a SQL injection vulnerability.

## Findings
[Critical] src/CustomerRepository.cs:14 — SQL injection via interpolated `email`
> `var sql = $"SELECT Id, Email FROM Customers WHERE Email = '{email}'";`

`email` is an unvalidated caller-supplied string interpolated directly into the SQL text. A value such as `' OR '1'='1` (or a `'; DROP TABLE ...--` payload) alters the query, allowing arbitrary data reads or destructive statements depending on connection permissions. Fix by parameterizing:

```csharp
const string sql = "SELECT Id, Email FROM Customers WHERE Email = @email";
await using var command = new SqlCommand(sql, connection);
command.Parameters.AddWithValue("@email", email);
```

## Verdict
Request changes

