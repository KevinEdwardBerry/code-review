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
## Code Review: `src/config.ts` config helpers

### Issues

**1. `writeBackup` leaks the file descriptor (high severity)**
```ts
const fd = fs.openSync(path, "w");
fs.writeSync(fd, data);
```
`fd` is never closed with `fs.closeSync(fd)`. Repeated calls exhaust the process's fd limit. Also, `fs.writeSync` on a string may perform a partial write — there's no loop or byte-count check. This whole function is better expressed as `fs.writeFileSync(path, data)`, which is atomic-equivalent, closes properly, and handles partial writes. If `openSync` is intentionally used (e.g., to control flags/mode), wrap it:
```ts
const fd = fs.openSync(path, "w");
try {
  fs.writeSync(fd, data, null, "utf8");
} finally {
  fs.closeSync(fd);
}
```

**2. `loadConfig` performs no validation of `cfg` (medium)**
`JSON.parse` returns `any` and it's cast implicitly to `AppConfig`. A malformed file (missing `port`, `port` as a string, etc.) propagates silently and fails far from the cause. Validate the shape before returning:
```ts
const cfg = JSON.parse(raw);
if (typeof cfg.port !== "number" || typeof cfg.dbUrl !== "string") {
  throw new Error(`Invalid config at ${path}`);
}
```
Or use a schema validator (zod, ajv). Also consider whether `JSON.parse`/`readFileSync` errors should be wrapped with the path for context — a bare `ENOENT` stack doesn't tell the caller which file failed.

**3. `fetchRemoteConfig` has the same validation gap, plus no HTTP error handling (medium)**
```ts
const res = await fetch(url);
return res.json();
```
- `res.ok` is never checked — a 404/500 body will be parsed as config, likely producing a silently wrong `AppConfig` or a confusing JSON error. Should be:
```ts
if (!res.ok) throw new Error(`fetch ${url} failed: ${res.status}`);
```
- No timeout/AbortSignal — a hung remote endpoint leaves this awaiting forever. Consider `AbortSignal.timeout(...)`.
- `res.json()` returns `any`; same runtime-validation concern as #2.

**4. Inconsistent sync/async API surface (minor)**
`loadConfig` is synchronous but `fetchRemoteConfig` is async, and the file writes are sync. Fine for startup code, but if `writeBackup` is called on a hot path, blocking I/O + the fd leak compounds. Worth documenting intent.

**5. Security note (minor)**
`writeBackup` writes with default permissions and `path`/`url` are unchecked. If `path` can come from user input, this is a path-traversal/write-anywhere risk; if `url` is user-controlled, `fetchRemoteConfig` is an SSRF vector. Likely internal-only, but flag it if either is reachable from request data.

### Recommendations (priority order)
1. Replace `writeBackup` with `fs.writeFileSync`, or close the fd in a `finally`.
2. Check `res.ok` and add a timeout in `fetchRemoteConfig`.
3. Validate the parsed shape in both loaders before returning `AppConfig` — ideally share one `validateConfig(raw: unknown): AppConfig` helper so the two paths can't drift.

### What looks fine
- Typing the interface and returning `Promise<AppConfig>` is reasonable.
- `readFileSync`/`openSync` at startup is acceptable for a config module.

