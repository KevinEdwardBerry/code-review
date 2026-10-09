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
diff --git a/src/accounts.ts b/src/accounts.ts
index 6f70819..a2b3c4d 100644
--- a/src/accounts.ts
+++ b/src/accounts.ts
@@ -1,2 +1,42 @@
 // Account service
 
+export interface Account {
+  username: string;
+  email: string;
+  address: string;
+}
+
+const DEFAULTS = {
+  maxRetries: 3,
+  timeoutMs: 5000
+}
+
+/**
+ * Creates a new account and sends a welcome email.
+ * We recieve the raw form input and normalize it.
+ */
+export function createAccount(input: Account, opts: Partial<typeof DEFAULTS> = {}) {
+  const retires = opts.maxRetries ?? DEFAULTS.maxRetries
+  const username = input.username.trim().toLowerCase()
+
+  if (username.length < 3) {
+    throw new Error("Username lenght must be at least 3 charaters.")
+  }
+
+  const account: Account = {
+    username: username,
+    email: input.email,
+    address: input.address
+  }
+
+  console.log(`Created account for ${account.username}, retrying up to ${retires} times`)
+  return account
+}
+
+export function getAdress(account: Account): string {
+  return account.address
+}
+
+export const TEXT = "teh quick brown fox"
+
+export const LABEL = "Acme Colour Labs"


# EXPECTED
# Expected: 06-typos

Typos are of three kinds: `misspelling`, `swap` (transposed letters), `missing_letter`. None of them changes behavior, so all are Low or Medium at most; no finding here may be High or Critical.

## Must find (public API / user-facing)
- `t1_adress_api` (low/medium, missing_letter): the exported function `getAdress` (`src/accounts.ts:36`) should be `getAddress`. Costly to rename later, so flag now.
- `t2_lenght` (low, swap): the user-facing error message at `src/accounts.ts:23` uses "lenght" instead of "length".
- `t3_charaters` (low, missing_letter): the same message at `src/accounts.ts:23` uses "charaters" instead of "characters". May be reported in one finding together with `t2_lenght`.
- `t6_teh_text` (low, swap): the exported string constant `TEXT` (`src/accounts.ts:40`) uses "teh" instead of "the". String literals are in scope unless explicitly documented as acceptable.

## Must find (cosmetic)
- `t4_retires` (nit/low, swap): the local variable `retires` (`src/accounts.ts:19`) should be `retries`.
- `t5_recieve` (nit/low, misspelling): the comment at `src/accounts.ts:16` ("We recieve the raw form input") should be "receive".

## Typo categories for recall
- misspelling: t5 (1)
- swap: t2, t4, t6 (3)
- missing_letter: t1, t3 (2)

## Must not flag (false positives)
- `Colour` in `LABEL` (`src/accounts.ts:42`): valid British spelling in a proper name.

## Ranking expectation
`t1_adress_api` should rank above the user-facing message typos (`t2`, `t3`), which should rank above the public string typo (`t6`), which should rank above the cosmetic identifier/comment typos (`t4`, `t5`). Low-impact cosmetic typos (`t4`, `t5`) may be grouped into one finding.

## Hard fail
- None: this version has no behavior-changing typo.


# CITATION_CHECK
{
  "citations_checked": 4,
  "problems": [],
  "ok": true
}


# REVIEW
## Summary
Low-risk new account module whose only demonstrated defects are spelling errors in an exported name, user-facing text, a public string, a comment, and a local variable.

## Findings
[Medium] src/accounts.ts:36 — Misspelled exported function name `getAdress`
> `export function getAdress(account: Account): string {`
The typo becomes part of the public API; callers will bind to the misspelled name and fixing it later is a breaking change. Rename to `getAddress` now.

[Low] src/accounts.ts:23 — Misspellings in user-facing error message
> `throw new Error("Username lenght must be at least 3 charaters.")`
"lenght" and "charaters" appear in text shown to users. Fix to "Username length must be at least 3 characters."

[Low] src/accounts.ts:40 — Typo in public string constant
> `export const TEXT = "teh quick brown fox"`
"teh" should be "the" in this exported literal.

[Low] src/accounts.ts:16 — Grouped cosmetic typos in comment and local identifier
> `* We recieve the raw form input and normalize it.`
"recieve" → "receive".
> `const retires = opts.maxRetries ?? DEFAULTS.maxRetries`
Local variable `retires` → `retries` (also used at line 32).

## Verdict
Approve with nits

