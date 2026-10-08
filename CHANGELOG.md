# Changelog

Newest first. Each entry links to the run folder and its detailed `result-summary.md`. Entries are added by `/eval <version>`.

<!-- ENTRIES -->
## v1 - 2026-10-08

- Prompt: `prompts/code-review.v1.md`
- Run folder: [runs/2026-10-08-v1-00/](runs/2026-10-08-v1-00/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **70.6/100** (new baseline; no previous evaluation)
- Hard fails: 05-clean-refactor — fabricated claim about class declaration churn

### What changed
Baseline; first evaluated prompt version.

### Suggested next changes
- Require Summary / Findings / Verdict with severity and exact file:line for every finding.
- Require diff evidence and concrete impact; omit speculative style or best-practice suggestions.
- Calibrate severity, separating blocking defects from optional nits.
- For clean changes, verify claimed behavior changes or diff churn directly against the patch.
- Full details: [result-summary.md](runs/2026-10-08-v1-00/result-summary.md)

---
