# Changelog

Newest first. Each entry links to the run folder and its detailed `result-summary.md`. Entries are added by `/eval <version>`.

<!-- ENTRIES -->
## v2 - 2026-10-08 (rerun)

- Prompt: `prompts/code-review.v2.md`
- Run folder: [runs/2026-10-08-v2-01/](runs/2026-10-08-v2-01/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **87.5/100** (+3.6 vs v2-00)
- Hard fails: 03-race-condition — fabricated; 06-typos — fabricated

### What changed
No prompt changes since the previous v2 evaluation; this rerun scored the same v2 prompt.

### Suggested next changes
- Require every cited line and excerpt to match the supplied diff's new-file line numbering.
- Suppress speculative boundary/config concerns and unseeded style nits without demonstrated defects.
- Keep concurrency paths and typo findings precisely quoted, separately located, and ranked by impact.
- Full details: [result-summary.md](runs/2026-10-08-v2-01/result-summary.md)

---

## v2 - 2026-10-08

- Prompt: `prompts/code-review.v2.md`
- Run folder: [runs/2026-10-08-v2-00/](runs/2026-10-08-v2-00/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **83.9/100** (+13.3 vs v1)
- Hard fails: 03-race-condition — missed_critical; 06-typos — fabricated

### What changed
Added evidence-based findings, severity and typo guidance, anti-speculation rules, and a required Summary / Findings / Verdict structure.

### Suggested next changes
- Add a targeted resource-lifecycle and HTTP/config-validation checklist for I/O changes.
- Require synchronized review of shared-state reads, writes, and snapshots; distinguish demonstrated races from assumed caller behavior.
- Require exact line references and preserve typo impact ranking; omit unsupported unused-option concerns.
- Full details: [result-summary.md](runs/2026-10-08-v2-00/result-summary.md)

---

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
