# Changelog

Newest first. Each entry links to the run folder and its detailed `result-summary.md`. Entries are added by `/eval <version>`.

<!-- ENTRIES -->

## v2 - 2026-10-07

- Prompt: `prompts/code-review.v2.md`
- Run folder: [runs/2026-10-07-v2-00/](runs/2026-10-07-v2-00/)
- Reviewer model: subagent_explore default model | Judge model: subagent_explore default model
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **93.9/100** (-1.1 vs v1)
- Hard fails: 03-race-condition (`missed_critical` — unlocked read in `Count` not found)
- [Detailed results](runs/2026-10-07-v2-00/result-summary.md)

### What changed
Severity levels gained concrete examples and tightened definitions; findings must now quote a code snippet alongside file:line; new rule caps optional/validation extras below must-find issues. Fixtures unchanged. Severity calibration improved (01, 04 now exact), but recall regressed on 03 — the `Count` read race was folded into the `Inc` finding — and 06 picked up two noise items (non-seeded doc-claim finding, `teh` test comment).

### Suggested next changes
- Concurrency checklist: check every method that touches shared state, including getters/read-only paths, not just mutators.
- Extend must-not-flag typos to comments/fixtures describing intentional misspellings.
- Tell reviewers to derive new-file line numbers from `@@` hunk headers to fix persistent line drift.
- Clarify high vs medium: high = documented contract broken for typical inputs; medium = wrong only on edge/remainder cases.

---

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
