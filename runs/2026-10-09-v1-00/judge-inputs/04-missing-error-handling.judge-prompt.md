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
- `fd_leak` (medium): `writeBackup` never closes `fd` (`fs.closeSync`), leaking the descriptor (also leaks if `writeSync` throws). Fix: try/finally or `fs.writeFileSync`.
- `fetch_no_status` (medium): `fetchRemoteConfig` does not check `res.ok`, so error responses are parsed as config. Fix: check `res.ok` and throw.
- `no_validation` (medium/low): `loadConfig` returns unvalidated `JSON.parse` output typed as `AppConfig`; missing/invalid file or malformed JSON throws with no context, and fields are not validated.

## Acceptable extras
- nit: sync fs calls block the event loop.

## Must not flag
- The `AppConfig` interface itself.

## Hard fail
- None of the above found sets `missed_critical`.


# CITATION_CHECK
{
  "citations_checked": 0,
  "problems": [],
  "ok": true
}


# REVIEW
# Code Review: `src/config.ts`

Thanks for the addition — a few issues here that I'd want addressed before merge, ranging from correctness bugs to missing validation.

## 🔴 Bugs / Correctness

**1. `writeBackup` leaks the file descriptor**
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
The file descriptor is never closed via `fs.closeSync(fd)`. Under repeated calls this leaks FDs and on some platforms can produce incomplete writes or `EMFILE` errors. If you want the simpler API, `fs.writeFileSync(path, data)` does the same thing in one call without the leak. If you keep `openSync`, wrap in `try/finally` with `fs.closeSync(fd)`.

**2. `loadConfig` returns untyped, unvalidated data**
```ts
const cfg = JSON.parse(raw)
return cfg
```
`JSON.parse` returns `any`, so this silently satisfies the `AppConfig` return type while providing no guarantee the file actually contains `port`/`dbUrl` — a missing or mistyped field becomes a runtime failure far downstream. Either validate explicitly, or use a schema validator (zod, valibot, etc.). If you don't want a dependency, a manual check like `typeof cfg.port === "number"` before returning goes a long way.

**3. `fetchRemoteConfig` ignores HTTP errors and lacks validation**
```ts
const res = await fetch(url)
return res.json()
```
- No check of `res.ok` — a 404/500 HTML error page will be passed to `res.json()` and produce a confusing `SyntaxError` instead of a meaningful message.
- `res.json()` also returns `any`, so same unvalidated-shape problem as `loadConfig`.
- Consider a timeout (`AbortSignal.timeout(...)`) — a hung remote will otherwise block indefinitely.
- `res.json()` returns `Promise<any>` and you're returning it directly into `Promise<AppConfig>`; fine, but see the type-safety note below.

## 🟡 Minor / Consistency

**4. Sync vs async mixing**
`loadConfig` and `writeBackup` are synchronous while `fetchRemoteConfig` is async. If `loadConfig` is called at startup that's defensible, but `writeBackup` doing synchronous I/O on a hot path will block the event loop. Worth a comment or making it async (`fs.promises.writeFile`).

**5. Style inconsistency**
The file mixes `;` and no-`;` line endings (`port: number;` vs `import ... "fs"`). Pick whichever matches the project convention.

**6. Unhandled errors**
`JSON.parse` on malformed config throws a bare `SyntaxError`; consider wrapping with context like `Failed to load config at ${path}: ...` — debugging "Unexpected token" with no filename is painful.

## Suggested shape

```ts
export function loadConfig(path: string): AppConfig {
  const raw = fs.readFileSync(path, "utf8")
  const cfg: unknown = JSON.parse(raw)
  if (typeof cfg !== "object" || cfg === null
      || typeof (cfg as AppConfig).port !== "number"
      || typeof (cfg as AppConfig).dbUrl !== "string") {
    throw new Error(`Invalid config at ${path}`)
  }
  return cfg as AppConfig
}
```

**Verdict:** Request changes — the FD leak and the two unchecked `any` → `AppConfig` casts are the must-fixes.

