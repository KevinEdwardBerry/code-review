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
diff --git a/src/config.ts b/src/config.ts
index 4d5e6f7..80910ab 100644
--- a/src/config.ts
+++ b/src/config.ts
@@ -1,3 +1,26 @@
 import * as fs from "fs";
 
+export interface AppConfig {
+  port: number;
+  dbUrl: string;
+}
+
+export function loadConfig(path: string): AppConfig {
+  const raw = fs.readFileSync(path, "utf8");
+  const cfg = JSON.parse(raw);
+  return cfg;
+}
+
+export function writeBackup(path: string, data: string): void {
+  const fd = fs.openSync(path, "w");
+  fs.writeSync(fd, data);
+}
+
+export async function fetchRemoteConfig(url: string): Promise<AppConfig> {
+  const res = await fetch(url);
+  return res.json();
+}


# EXPECTED
# Expected: 04-missing-error-handling

## Must find
- `fd_leak` (medium): `writeBackup` never closes `fd` (`fs.closeSync`), leaking the descriptor (also leaks if `writeSync` throws). Fix: try/finally or `fs.writeFileSync`.
- `fetch_no_status` (medium): `fetchRemoteConfig` does not check `res.ok`, so error responses are parsed as config. Fix: check `res.ok` and throw.
- `no_validation` (medium/low): `loadConfig` returns unvalidated `JSON.parse` output typed as `AppConfig`; missing/invalid file or malformed JSON throws with no context, and fields are not validated.

## Acceptable extras
- nit: sync fs calls block the event loop.

## Must not flag
- The `AppConfig` interface itself.

## Hard fail
- None of the above found sets `missed_critical`.


# REVIEW
### Summary
The change adds a `src/config.ts` module with config loading, a file-backup writer, and a remote config fetcher. The code has no error handling, validation, or resource cleanup, so several real defects exist.

### Findings
- **high src/config.ts:20 - `fetchRemoteConfig` never checks the HTTP response status**
  - Problem: `fetch` resolves without throwing for non-2xx responses (404, 500, etc.). The code calls `res.json()` unconditionally, so a server error page or empty body will produce a parse exception or an object that is not an `AppConfig`, propagated to callers as if it were a valid config or an unrelated parse error. Combined with the missing validation, callers can receive a wrong-shaped object on common failure paths.
  - Fix: Check `res.ok` (or `res.status`) before parsing and throw a descriptive error; validate the parsed shape before returning.
  - Code snippet:
    ```
    +  const res = await fetch(url);
    +  return res.json();
    ```

- **medium src/config.ts:15 - file descriptor in `writeBackup` is never closed**
  - Problem: `fs.openSync` returns an `fd` that is written to but never `fs.closeSync`'d. Each call leaks a file descriptor; under repeated calls this exhausts the process fd limit, and on some platforms buffered data may not be fully flushed before process exit.
  - Fix: Use `fs.writeFileSync(path, data)` instead, or wrap `writeSync` in a `try/finally` that calls `fs.closeSync(fd)`.
  - Code snippet:
    ```
    +  const fd = fs.openSync(path, "w");
    +  fs.writeSync(fd, data);
    ```

- **medium src/config.ts:10 - `JSON.parse` result returned unvalidated against `AppConfig`**
  - Problem: `JSON.parse` returns `any`, which is silently cast to `AppConfig`. A config file missing `port`/`dbUrl` or containing the wrong types (e.g. `port` as a string) will be returned as a valid `AppConfig`, deferring failure to downstream consumers where it is harder to diagnose. TypeScript's return type provides no runtime guarantee here.
  - Fix: Validate the parsed object (e.g. check `typeof cfg.port === "number"` and `typeof cfg.dbUrl === "string"`, or use a schema validator like zod) and throw a clear error on mismatch.
  - Code snippet:
    ```
    +  const cfg = JSON.parse(raw);
    +  return cfg;
    ```

- **low src/config.ts:9 - no error context when reading/parsing the config file fails**
  - Problem: If the file is missing or contains invalid JSON, `readFileSync`/`JSON.parse` throw raw errors (`ENOENT`, `SyntaxError`) with no indication that the failure came from loading config at `path`, making operational debugging harder.
  - Fix: Wrap the read/parse in try/catch and rethrow a wrapped error including `path`, e.g. `throw new Error(\`Failed to load config from ${path}: ${err.message}\`)`.
  - Code snippet:
    ```
    +  const raw = fs.readFileSync(path, "utf8");
    +  const cfg = JSON.parse(raw);
    ```

### Verdict
request changes

