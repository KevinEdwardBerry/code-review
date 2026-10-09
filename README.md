# code-review

A reusable AI code-review prompt, plus an evaluation harness for improving it iteratively.

## Layout
- `prompts/code-review.vN.md` - prompt versions. Treat a version as immutable once evaluated; create a new file for each change.
- `fixtures/*.diff` + `*.expected.md` - diffs with seeded issues (bugs, security, typos) and a clean diff for false positives. Fixtures are limited to C#, JavaScript, and TypeScript, the languages this prompt is used on.
- `scripts/difftool.mjs` - `annotate` (prefix new-file line numbers, used by v5+ prompts), `check` (mechanically verify a review's `file:line` + quoted excerpts), `expected` (verify line refs in expected files).
- `rubric/rubric.md` - criteria, weights, hard-fail flags. `rubric/judge-prompt.md` - the LLM judge template.
- `runs/<date>-<version>-<increment>/` - one folder per evaluation run. Contains one file per fixture plus a `result-summary.md` with the full AI responses, score tables, and observations.
- `CHANGELOG.md` - a minimal index with one entry per evaluated run, linking to the run folder's detailed summary.
- `.devin/skills/eval/SKILL.md` - the `/eval` skill.

## Workflow
1. Copy the latest prompt to a new version (`prompts/code-review.v2.md`) and edit it.
2. Run `/eval v2` once. It reviews every fixture with an isolated subagent (prompt + diff only), mechanically checks citations, judges each review against the expected findings, writes `runs/`, and prepends a `CHANGELOG.md` entry.
3. Read the top-level `CHANGELOG.md` entry, then open the linked `result-summary.md` for full details. To override a score, fill in the "Human override" section of the run file and note the corrected totals in the changelog.
4. Repeat. Add a fixture whenever a real review miss appears; scores are only comparable across versions on the same fixture set (each entry lists its fixtures).

## Notes
- Scores are only comparable for the same fixture set when all fixtures were successfully judged. `/eval` reports otherwise as "not comparable".
- `runs/` is kept in the repo on purpose as the permanent experiment record; move old runs into an archive folder if it grows.
- Changelog `(rerun)` labels are added by `/eval` when a version already has a run.
- The judge is an AI; spot-check its rationale, especially for hard fails.
- `/eval` never edits prompts, fixtures, or the rubric, and never runs git commands (staging and saving changes is up to you).
