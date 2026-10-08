# Changelog

Newest first. Each entry links to the run folder and its detailed `result-summary.md`. Entries are added by `/eval <version>`.

<!-- ENTRIES -->

## v7 - 2026-10-08

- Prompt: `prompts/code-review-v7.md`
- Run folder: [runs/2026-10-08-v7-00/](runs/2026-10-08-v7-00/)
- Reviewer model: subagent_explore (unknown concrete model) | Judge model: subagent_general (unknown concrete model)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **80.3/100** (-12.2 vs v6)
- Hard fails: none

### What changed
Stripped the prompt down to a minimal one-line instruction, removing all severity, line-citation, concurrency, typo, and output-format guidance.

### Suggested next changes
- Restore severity examples and the `## Severity` definitions to calibrate rankings.
- Restore the exact `file:line` citation requirement and a worked `@@` hunk-header example.
- Restore concurrency, behavior-preserving rewrite, and typo must-not-flag rules from v6.
- Restore the Summary/Findings/Verdict output format and forbid emojis/extra sections.

---


## v6 - 2026-10-07

- Prompt: `prompts/code-review.v6.md`
- Run folder: [runs/2026-10-07-v6-00/](runs/2026-10-07-v6-00/)
- Reviewer model: subagent_explore (unknown concrete model) | Judge model: subagent_general (unknown concrete model)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **92.5/100** (+9.4 vs v5)
- Hard fails: none

### What changed
Implemented v5's suggested improvements: added a worked clean-refactor example, two `@@` hunk-header line-counting examples, an explicit concurrency rule for read-only accessors, and a must-not-flag typo list covering literal data, British spellings, and local abbreviations.

### Suggested next changes
1. Add a worked race-condition severity example: non-atomic `Inc` and unsynchronized `Count`/`Snapshot` are `high`, not `medium`.
2. Add concrete must-not-flag typo examples (`usernam`, `TEXT = "teh ..."`, `Colour` in a proper name).
3. Clarify that behavior-changing typos which silently fail logic are `high`, not `critical`.
4. Make exact `file:line` citations a hard actionability requirement.

---


## v5 - 2026-10-07

- Prompt: `prompts/code-review.v5.md`
- Run folder: [runs/2026-10-07-v5-00/](runs/2026-10-07-v5-00/)
- Reviewer model: subagent_explore (default subagent model) | Judge model: subagent_general (parent model)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **83.1/100** (+9.5 vs v4)
- Hard fails: 03-race-condition (missed_critical), 05-clean-refactor (fabricated)
- [Detailed results](runs/2026-10-07-v5-00/result-summary.md)

### What changed
Tightened severity ranking by concrete impact, added worked hunk-header line-number example and exact-citation rule, formalized clean-refactor and typo must-not-flag rules, and added concrete severity-boundary examples.

### Suggested next changes
1. Add an explicit, worked clean-refactor example and forbid style/usings or unnecessary-import findings on behavior-preserving rewrites.
2. Strengthen the concurrency checklist to explicitly require reviewing all read-only accessors and getters that touch shared mutable state.
3. Add a second `@@` hunk-header counting example and make exact `file:line` citations a stated requirement for every finding.
4. Clarify that literal string constants, test fixtures, British spellings in proper names, and consistently-used local abbreviations are not actionable typos.

---

## v4 - 2026-10-07

- Prompt: `prompts/code-review.v4.md`
- Run folder: [runs/2026-10-07-v4-00/](runs/2026-10-07-v4-00/)
- Reviewer model: subagent_explore (default subagent model) | Judge model: subagent_general (parent model)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **73.6/100** (-19.7 vs v3)
- Hard fails: 05-clean-refactor (fabricated)
- [Detailed results](runs/2026-10-07-v4-00/result-summary.md)

### What changed
Broadened review scope to correctness, security, concurrency, performance, tests and maintainability; rewrote severity/rules with stronger anti-invention/anti-speculation guidance and formalized output; added line-number derivation from hunk headers.

### Suggested next changes
1. Add a clean-refactor example: mathematically-equivalent rewrites should be `approve`/`approve with nits`, not request changes.
2. Add a concrete high-vs-medium severity example using pagination and SQL injection edge cases.
3. Clarify that literal data, test fixtures, and domain spellings are must-not-flag and that local variable abbreviations are nits.
4. Add a worked `@@` hunk-header counting example and require exact `file:line` citations.

---

## v3 - 2026-10-07

- Prompt: `prompts/code-review.v3.md`
- Run folder: [runs/2026-10-07-v3-00/](runs/2026-10-07-v3-00/)
- Reviewer model: subagent_explore default model | Judge model: subagent_explore default model
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **93.3/100** (-0.6 vs v2)
- Hard fails: none
- [Detailed results](runs/2026-10-07-v3-00/result-summary.md)

### What changed
Concurrency checklist now explicitly covers every method touching shared state, not just mutators; rules add line-number derivation from `@@` hunk headers and explicitly exclude intentional misspellings in comments/fixtures; severity definitions were reworded to sharpen the high/medium boundary.

### Suggested next changes
- Add a worked severity-boundary example distinguishing "high = wrong for every typical input" from "medium = wrong only on edge/remainder cases" (e.g., `totalPages` floor, `fd_leak`).
- Include a concrete `@@` hunk-header counting example so cited line numbers stop drifting.
- Clarify that leftover documentation-only vulnerable snippets are acceptable extras/low, not high-severity defects.
- Encourage one finding per distinct defect instead of bundled typo groups to raise actionability.

---

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
