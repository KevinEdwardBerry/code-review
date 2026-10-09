# Changelog

Newest first. Each entry links to the run folder and its detailed `result-summary.md`. Entries are added by `/eval <version>`.

<!-- ENTRIES -->

## v8 - 2026-10-09

- Prompt: `prompts/code-review.v8.md`
- Run folder: [runs/2026-10-09-v8-00/](runs/2026-10-09-v8-00/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **99.2/100** (+2.8 vs v7-01 (96.4))
- Hard fails: none

### What changed
v8 refines the concurrency rule to treat a check-then-act sequence as one High finding and the evidence rule to quote each relevant line inside a single finding without splitting one defect across findings.

### Suggested next changes
1. Set explicit typo severity: user-facing text and public string literals are Low; exported API names may be Low/Medium.
2. Require typo findings to stay strictly lower in severity than any functional defect in the same change.
3. Add fresh fixtures (XSS, resource leak, auth bypass) to test v8 rule generalization.
4. Preserve the v8 concurrency and evidence wording; it fixed the v7 split-finding and over-severity regressions.

Full details: [runs/2026-10-09-v8-00/result-summary.md](runs/2026-10-09-v8-00/result-summary.md)

---

## v7 - 2026-10-09 (rerun)

- Prompt: `prompts/code-review.v7.md`
- Run folder: [runs/2026-10-09-v7-01/](runs/2026-10-09-v7-01/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **96.4/100** (-2.8 vs v7-00 (99.2))
- Hard fails: 06-typos — fabricated

### What changed
No changes vs the previous evaluated prompt; this is a rerun of the identical `prompts/code-review.v7.md` file.

### Suggested next changes
1. Require every cited line to have a matching quoted excerpt.
2. Group check-then-act race writes into a single High finding.
3. Rate exported/public-API typos as Medium.
4. Add fresh fixtures to test v7 rule generalization.


Full details: [runs/2026-10-09-v7-01/result-summary.md](runs/2026-10-09-v7-01/result-summary.md)

---
## v7 - 2026-10-09

- Prompt: `prompts/code-review.v7.md`
- Run folder: [runs/2026-10-09-v7-00/](runs/2026-10-09-v7-00/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **99.2/100** (+5.0 vs v6-02 (94.2); same fixtures, all judged; single run)
- Hard fails: none

### What changed
v7 adds first-line citation rule for multi-line statements, generic-ish severity calibration examples, and a no-non-typo-findings rule for typo changes; fixes the 04 fabricated-citation fail and 06/03 regressions, leaving 02 totalPages over-rated (High).

### Suggested next changes
1. Make calibration examples generic (not fixture-shaped) and require per-finding severity (02 `totalPages` still High).
2. Add fresh fixtures (XSS, resource leak, auth bypass, tempting-nit clean change) to check the v7 rules generalize.
3. Require the cited line to contain the defective operation (keeps the 04 fix robust).
4. Rerun v7 to measure variance before treating +5.0 as real.

Full details: [runs/2026-10-09-v7-00/result-summary.md](runs/2026-10-09-v7-00/result-summary.md)

---
## v6 - 2026-10-09 (rerun)

- Prompt: `prompts/code-review.v6.md`
- Run folder: [runs/2026-10-09-v6-02/](runs/2026-10-09-v6-02/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **94.2/100** (-1.1 vs v6-01 (95.3); -1.0 vs mean of prior v6 runs (95.2); indicative, same fixtures, full judge template used for all)
- Hard fails: 04-missing-error-handling — fabricated (citation `src/webhook.ts:6` quote does not match line `})`)

### What changed
Unchanged v6 prompt rerun; 06-typos dropped to 80.0 (extra non-typo finding, typo grouping) while 03 improved to 95.0.

### Suggested next changes
1. Cite the first line of the offending expression and quote exactly that line (never a closing `})`).
2. Add severity examples: page-count and read-race defects are Medium, not High.
3. On typo changes, forbid non-typo findings and list public-string typos separately above grouped nits.

Full details: [runs/2026-10-09-v6-02/result-summary.md](runs/2026-10-09-v6-02/result-summary.md)

---

## v6 - 2026-10-09 (rerun)

- Prompt: `prompts/code-review.v6.md`
- Run folder: [runs/2026-10-09-v6-01/](runs/2026-10-09-v6-01/)
- Reviewer model: not exposed (profile: subagent_explore) | Judge model: not exposed (profile: subagent_general)
- Fixtures: 01-csharp-sql-injection, 02-off-by-one, 03-race-condition, 04-missing-error-handling, 05-clean-refactor, 06-typos
- Overall: **95.3/100** (+0.3 vs prior v6 mean; indicative because judge prompts 02–06 used a condensed rubric)
- Hard fails: 04-missing-error-handling — fabricated citation (quote does not match cited line)

### What changed
v6 tightens evidence verification and adds explicit security/correctness/reliability/concurrency checks versus v5; numeric rerun deltas are indicative because fixtures 02–06 received condensed judge instructions.

### Suggested next changes
1. Require citation to the defective operation and exact matching quote.
2. Add severity examples for pagination/counting issues and rank public-string typos above local/comment nits.
3. Do not suggest `Interlocked` alone for concurrent `Dictionary` access.

Full details: [runs/2026-10-09-v6-01/result-summary.md](runs/2026-10-09-v6-01/result-summary.md)

---

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
