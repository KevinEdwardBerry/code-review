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
diff --git a/src/config.ts b/src/config.ts
index 4d5e6f7..80910ab 100644
--- a/src/config.ts
+++ b/src/config.ts
@@ -1,2 +1,22 @@
 import * as fs from "fs"
 
+export interface AppConfig {
+  port: number;
+  dbUrl: string;
+}
+
+export function loadConfig(path: string): AppConfig {
+  const raw = fs.readFileSync(path, "utf8")
+  const cfg = JSON.parse(raw)
+  return cfg
+}
+
+export function writeBackup(path: string, data: string): void {
+  const fd = fs.openSync(path, "w")
+  fs.writeSync(fd, data)
+}
+
+export async function fetchRemoteConfig(url: string): Promise<AppConfig> {
+  const res = await fetch(url)
+  return res.json()
+}


# EXPECTED
# Expected: 04-missing-error-handling

## Must find
- `fd_leak` (medium): `writeBackup` opens `fd` at `src/config.ts:15` (`const fd = fs.openSync(path, "w")`) and never closes it (`fs.closeSync`), leaking the descriptor (also leaks if `writeSync` throws at `src/config.ts:16`). Fix: try/finally with `fs.closeSync(fd)`, or `fs.writeFileSync`.
- `fetch_no_status` (medium): `fetchRemoteConfig` does not check `res.ok` before `return res.json()` at `src/config.ts:21`, so error responses are parsed as config. Fix: check `res.ok` and throw.
- `no_validation` (low): `loadConfig` returns unvalidated `JSON.parse` output typed as `AppConfig` (`src/config.ts:10-11`); fields are not validated and a missing file or malformed JSON throws with no context. Fix: validate the parsed fields and wrap errors with the file path.

## Acceptable extras
- nit: sync fs calls block the event loop.

## Must not flag
- The `AppConfig` interface itself.

## Hard fail
- Missing both `fd_leak` and `fetch_no_status` sets `missed_critical`.


# CITATION_CHECK
{
  "citations_checked": 2,
  "problems": [],
  "ok": true
}


# REVIEW
## Summary
Adds config loading, a backup writer, and a remote config fetcher; low overall risk but the backup writer leaks its file descriptor.

## Findings

[Medium] src/config.ts:15 — File descriptor opened but never closed
> `const fd = fs.openSync(path, "w")`

`fs.writeSync(fd, data)` at src/config.ts:16 uses `fd`, but no `fs.closeSync(fd)` ever runs — neither on success nor if `writeSync` throws. Each call leaks a file descriptor, which can exhaust the process fd limit under repeated use. Fix: wrap in try/finally calling `fs.closeSync(fd)`, or use `fs.writeFileSync(path, data)` which handles this internally.

## Verdict
Request changes
