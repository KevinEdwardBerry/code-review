# Changelog

Newest first. Each entry links to the run folder and its detailed `result-summary.md`. Entries are added by `/eval <version>`.

<!-- ENTRIES -->

## v1 - 2026-10-07 (re-run)

- Prompt: `prompts/code-review.v1.md`
- Reviewer model: subagent_explore default model | Judge model: same
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **95.0/100** (+3.1 vs baseline)
- Hard fails: none
- [Detailed results](runs/2026-10-07-v1-01/result-summary.md)

### What changed
Fixtures updated: 01 (Python → T-SQL), 03 (Go → C#), 05 (Python → C#). Expected findings updated to match new languages. Prompt unchanged.

### Suggested next changes
- Tighten severity definitions with concrete examples to reduce one-level overrating on secondary findings.
- Instruct reviewers to quote code snippets alongside line numbers to improve actionability.
- Cap low-value extras or group them under a single "Other" bullet to reduce noise.
- Consider tightening the rubric on how to treat valid-but-unlisted findings.

## v1 - 2026-10-07

- Prompt: `prompts/code-review.v1.md`
- Reviewer model: subagent_explore default model | Judge model: same
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **91.9/100** (baseline, no previous version)
- Hard fails: none
- [Detailed results](runs/2026-10-07-v1-00/result-summary.md)

### What changed
Baseline.

### Suggested next changes
- Define severity with concrete examples and reserve critical for exploitable/data-loss issues.
- Instruct reviewers to cite quoted code snippets along with line references.
- Cap low-value extras or group them under a single "Other" bullet.
- Tighten rubric on valid-but-unlisted findings.
