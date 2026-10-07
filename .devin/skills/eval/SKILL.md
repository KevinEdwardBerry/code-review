---
name: eval
description: Evaluate a code-review prompt version against all fixtures, write runs/ and update CHANGELOG.md
argument-hint: "<version, e.g. v1>"
triggers:
  - user
allowed-tools:
  - read
  - grep
  - glob
  - edit
  - exec
permissions:
  allow:
    - Write(runs/**)
    - Write(CHANGELOG.md)
  deny:
    - Write(prompts/**)
    - Write(fixtures/**)
    - Write(rubric/**)
---

Evaluate a version of the code-review prompt. The user's argument is the version (`v1` or `1`); normalize to `vN`.

## 1. Resolve inputs
- Prompt file: `prompts/code-review.<vN>.md`. If missing, list `prompts/` and stop with a clear error.
- Fixtures: every `fixtures/*.diff`, each paired with `fixtures/<same-name>.expected.md`. If an expected file is missing, stop and report it.
- Read `rubric/rubric.md`, `rubric/judge-prompt.md`, `templates/run.md`, `templates/changelog-entry.md`, and `CHANGELOG.md`.
- Today's date (YYYY-MM-DD) from the system info. Never overwrite existing files in `runs/`: if `runs/<date>-<vN>-<fixture>.md` exists, use the suffix `-r2`, `-r3`, ... for every run file in this evaluation and label the CHANGELOG entry "(re-run)".

## 2. Reviewer step (isolated)
For each fixture, launch a subagent (profile `subagent_explore`, no file access needed) in parallel. Its task is exactly the prompt file contents with `{{DIFF}}` replaced by the fixture diff. Do NOT give it the expected file, the rubric, or any hint about seeded issues. Tell it to answer using only the text in the task, reading no files. Save its response verbatim.

## 3. Judge step
For each fixture, launch a separate subagent (in parallel, ideally with a different `model` than the reviewer) whose task is `rubric/judge-prompt.md` with `{{RUBRIC}}`, `{{DIFF}}`, `{{EXPECTED}}` and `{{REVIEW}}` filled in. It must return only JSON. Parse it; if it is invalid or fails the schema, retry once with the error, then record the fixture as "judge failed" and continue.

## 4. Scoring
Per fixture: weighted score = sum(score/3 * weight) using the weights in `rubric/rubric.md`, rounded to one decimal. Hard fail if any `hard_fail` flag is true. Overall = mean of fixture scores. Find the most recent previous entry in `CHANGELOG.md` and compute per-fixture and overall deltas (if the fixture was not in that entry, show "new").

## 5. Write runs
For each fixture write `runs/<date>-<vN>-<fixture>.md` from `templates/run.md`: verbatim AI response, score table with rationale, matched/missed/false positives, typo recall, judge JSON, and an empty "Human override" section. Record the reviewer and judge model names (as best you know them).

## 6. Update CHANGELOG
Fill `templates/changelog-entry.md` and insert it directly below the `<!-- ENTRIES -->` marker (newest first). Include:
- what changed versus the previous evaluated prompt (run a diff between the two prompt files; for the first version write "Baseline"),
- the fixture list (so score comparability is clear),
- the score table, hard fails, and delta,
- observations: patterns in misses and false positives, per-typo-category recall, and 2-4 concrete suggested prompt changes,
- for each fixture, a link to its run file and the full AI response inside a `<details>` block.

## 7. Report
Print a short summary: overall score and delta, per-fixture totals, hard fails, regressions, and the suggested next changes. Do not commit and do not modify `prompts/`, `fixtures/`, or `rubric/`.
