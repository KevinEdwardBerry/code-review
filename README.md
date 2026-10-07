# code-review

A reusable AI code-review prompt, plus an evaluation harness for improving it iteratively.

## Layout
- `prompts/code-review.vN.md` - prompt versions. Treat a version as immutable once evaluated; create a new file for each change.
- `fixtures/*.diff` + `*.expected.md` - test diffs with seeded issues (bugs, security, typos) and a clean diff for false positives.
- `rubric/rubric.md` - criteria, weights, hard-fail flags. `rubric/judge-prompt.md` - the LLM judge template.
- `runs/<date>-<version>-<increment>/` - one folder per evaluation run. Contains one file per fixture plus a `result-summary.md` with the full AI responses, score tables, and observations.
- `CHANGELOG.md` - a minimal index with one entry per evaluated run, linking to the run folder's detailed summary.
- `.devin/skills/eval/SKILL.md` - the `/eval` skill.

## Workflow
1. Copy the latest prompt to a new version (`prompts/code-review.v2.md`) and edit it.
2. Run `/eval v2`. It reviews every fixture with an isolated subagent (prompt + diff only), judges each review against the expected findings, writes `runs/`, and prepends a `CHANGELOG.md` entry.
3. Read the top-level `CHANGELOG.md` entry, then open the linked `result-summary.md` for full details. To override a score, fill in the "Human override" section of the run file and note the corrected totals in the changelog.
4. Repeat. Add a fixture whenever a real review miss appears; scores are only comparable across versions on the same fixture set (each entry lists its fixtures).

## Notes
- The judge is an AI; spot-check its rationale, especially for hard fails.
- `/eval` never edits prompts, fixtures, or the rubric, and never commits.
