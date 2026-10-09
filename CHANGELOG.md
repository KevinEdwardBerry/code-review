# Changelog

Newest first. Each entry links to the run folder and its detailed `result-summary.md`. Entries are added by `/eval <version>`.

<!-- ENTRIES -->
## v6 - 2026-10-09

- Prompt: `prompts/code-review.v6.md`
- Run folder: [runs/2026-10-09-v6-00/](runs/2026-10-09-v6-00/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **95.0/100** (+19.7 vs v1-00)
- Hard fails: None

### What changed
v6 adds explicit annotated-diff evidence rules, lowest-severity calibration, required Summary/Findings/Verdict format, and typo-ranking guidance to the bare v1 baseline.

### Suggested next changes
1. Add a remote-fetch/JSON-validation checklist for I/O fixtures.
2. Provide concrete severity examples to prevent over-ranking secondary issues and cosmetic typos.
3. Keep the mechanical citation and no-speculation rules; they produced zero fabricated findings.

---

## v1 - 2026-10-09 (rerun)

- Prompt: `prompts/code-review.v1.md`
- Run folder: [runs/2026-10-09-v1-00/](runs/2026-10-09-v1-00/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **75.3/100** (-18.6 vs v4-01; +4.7 vs prior v1 run, fixture 01 differs)
- Hard fails: None

### What changed
Rerun of the unchanged v1 baseline prompt (bare reviewer instruction, no format or rules); scored against the current six fixtures with the mechanical citation check.

### Suggested next changes
1. Add the required Summary / Findings / Verdict format with severity ordering.
2. Add a no-speculation / no-self-contradiction rule to cut false positives.
3. Require separate findings for each unsynchronized access path (Count read missed on 03).
4. Add typo ranking and a do-not-flag rule for proper names and variant spellings.

Full details: [runs/2026-10-09-v1-00/result-summary.md](runs/2026-10-09-v1-00/result-summary.md)

---

## Harness update - 2026-10-09 (no evaluation)

- Added `scripts/difftool.mjs` (line annotation + mechanical citation check), `prompts/code-review.v5.md` (unevaluated; uses annotated diffs, consolidated rules), citation check in the judge prompt, and `--repeats`/not-comparable handling in `/eval`.
- Correction to v4-01: the 01-csharp-sql-injection citation (`:14`) was correct; the scripted check confirms the wrong citations on 02, 03, 05 and 06 only.
- Scores before this entry are single-sample and not comparable to future repeated runs.

---
## v4 - 2026-10-09 (rerun)

- Prompt: `prompts/code-review.v4.md`
- Run folder: [runs/2026-10-09-v4-01/](runs/2026-10-09-v4-01/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **93.9/100** (+7.5 vs previous v4 run)
- Hard fails: 02-off-by-one — fabricated; 03-race-condition — missed_critical; 05-clean-refactor — fabricated; 06-typos — fabricated

### What changed
The v3-to-v4 prompt diff adds detailed line reconstruction and exact evidence checks, stronger anti-speculation/concurrency guidance, and more explicit severity, reference-format, and typo-grouping instructions.

### Suggested next changes
- Require exact mechanical verification of each cited line and quoted excerpt; omit mismatched anchors.
- Review every independent function and shared-state read, write, and snapshot path before responding.
- Keep clean-diff responses within the requested headings and `None.` format; avoid unneeded verification commentary.

- Full details: [result-summary.md](runs/2026-10-09-v4-01/result-summary.md)

---
## v4 - 2026-10-09 (rerun)

- Prompt: `prompts/code-review.v4.md`
- Run folder: [runs/2026-10-09-v4-00/](runs/2026-10-09-v4-00/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **86.4/100** (-10.3 vs previous v4; not directly comparable because previous run scored three fixtures)
- Hard fails: 03-race-condition — missed_critical, fabricated; 06-typos — fabricated

### What changed
No prompt changes since the previous v4 evaluation; this rerun re-evaluates all six fixtures with successful judge outputs.

### Suggested next changes
- Enforce a final audit that each cited new-file line matches its quoted changed code.
- Review all independent functions and shared-state reads, writes, and snapshots before finalizing.
- Suppress speculative buffer/performance concerns without demonstrated impact; calibrate severity and typo ranking.
- Full details: [result-summary.md](runs/2026-10-09-v4-00/result-summary.md)

---
## v4 - 2026-10-08

- Prompt: `prompts/code-review.v4.md`
- Run folder: [runs/2026-10-08-v4-00/](runs/2026-10-08-v4-00/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general; 03, 04, 06 judge failed after retry)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition (judge failed), 04-missing-error-handling (judge failed), 05-clean-refactor, 06-typos (judge failed)
- Overall: **96.7/100** (+6.4 vs v3; three judged fixtures, not directly comparable to v3's five-fixture score)
- Hard fails: none confirmed among scored fixtures; 03, 04, and 06 unscored

### What changed
Added explicit new-file line reconstruction, anti-speculative optimization guidance, stricter concurrent-path citations, and concise grouping guidance for cosmetic typos.

### Suggested next changes
- Require exact matching of each finding's quoted defect and cited new-file line; omit any uncertain anchor.
- Review concurrent reads, writes, and snapshots as separately anchored findings.
- Avoid unrelated doc-comment concerns unless the diff demonstrates a concrete contract defect.

- Full details: [result-summary.md](runs/2026-10-08-v4-00/result-summary.md)

---

## v3 - 2026-10-08

- Prompt: `prompts/code-review.v3.md`
- Run folder: [runs/2026-10-08-v3-00/](runs/2026-10-08-v3-00/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general; 06-typos judge failed after retry)
- Fixtures: 01-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos (judge failed)
- Overall: **90.3/100** (+2.8 vs v2-01; five judged fixtures, not directly comparable to six-fixture prior score)
- Hard fails: 02-off-by-one — fabricated; 06-typos — unscored (judge failed)

### What changed
Added exact new-file line/excerpt verification, stronger anti-speculation rules, explicit concurrent shared-state path review, tighter nit guidance, and typo-severity ordering.

### Suggested next changes
- Verify every line number against new-file numbering and anchor it to the quoted defect; omit unverified references.
- Suppress hypothetical future-growth and micro-optimization nits without demonstrated impact.
- Keep concurrency reads, writes, and snapshots separately cited; resolve judge failure before comparing the typo fixture.
- Full details: [result-summary.md](runs/2026-10-08-v3-00/result-summary.md)

---
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
