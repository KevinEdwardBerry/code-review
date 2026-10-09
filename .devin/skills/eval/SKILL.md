---
name: eval
description: Evaluate a code-review prompt version against all fixtures, write a run folder under runs/, and update CHANGELOG.md
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
    - Bash(node scripts/difftool.mjs *)
  deny:
    - Write(prompts/**)
    - Write(fixtures/**)
    - Write(rubric/**)
---

Evaluate a version of the code-review prompt exactly once. The user's argument is the version (`v1` or `1`); normalize to `vN`. Run the reviewer and judge pipeline once for each fixture.

## 1. Resolve inputs
- Prompt file: `prompts/code-review.<vN>.md`. If missing, list `prompts/` and stop with a clear error.
- Fixtures: every `fixtures/*.diff`, each paired with `fixtures/<same-name>.expected.md`. If an expected file is missing, stop and report it.
- Read `rubric/rubric.md`, `rubric/judge-prompt.md`, `templates/run.md`, `templates/run-details.md`, `templates/changelog-entry.md`, and `CHANGELOG.md`.
- Today's date (YYYY-MM-DD) from the system info.
- Determine the run folder: `runs/<date>-<vN>-<increment>/` where `<increment>` is the next unused two-digit number starting from `00`. Do not overwrite an existing run folder; always pick a new increment for re-runs. If the same prompt version already has a run, label the changelog entry `(rerun)` and compare against the mean of prior runs for that version, not just the latest.

## 2. Reviewer step (isolated)
For each fixture, launch a subagent (profile `subagent_explore`, no file access needed) in parallel. Its task is exactly the prompt file contents with `{{DIFF}}` replaced by the fixture diff. For prompts whose text says the diff is annotated (v5+), substitute the output of `node scripts/difftool.mjs annotate <diff>`; otherwise the raw diff. Do NOT give it the expected file, the rubric, or any hint about seeded issues. Tell it to answer using only the text in the task, reading no files. Save its response verbatim, then run `node scripts/difftool.mjs check <diff> <saved-review>` (use the raw diff) and keep its JSON as the citation check. Record the subagent profile and, if available, the concrete model name used.

## 3. Judge step
For each fixture, launch a separate subagent (in parallel, ideally with a different `model` than the reviewer) whose task is `rubric/judge-prompt.md` with `{{RUBRIC}}`, `{{DIFF}}` (raw), `{{EXPECTED}}`, `{{CITATION_CHECK}}` and `{{REVIEW}}` filled in. Always use a different `model` for the judge than the reviewer when one can be chosen, and record both concrete model names; if a name is not exposed, say so rather than guessing. It must return only JSON. Parse it; if it is invalid or fails the schema, retry once with the error, then record the fixture as "judge failed" and continue. Record the subagent profile and, if available, the concrete model name used.

## 4. Scoring
Per fixture: weighted score = sum(score/3 * weight) using the weights in `rubric/rubric.md`, rounded to one decimal. Hard fail if any `hard_fail` flag is true. Overall = mean of fixture scores. Find the most recent previous evaluated entry in `CHANGELOG.md` and compute per-fixture and overall deltas (if the fixture was not in that entry, show "new"). Only show a delta when both runs used the same fixture set and every fixture was successfully judged; otherwise write "not comparable" and say why.

## 5. Write per-fixture run files
For each fixture write `<run_folder>/<fixture>.md` from `templates/run.md`: verbatim AI response, score table with rationale, matched/missed/false positives, typo recall, judge JSON, and an empty "Human override" section. Record the reviewer and judge model names/profile names (as best you know them).

## 6. Write detailed run summary
Fill `templates/run-details.md` and write it as `<run_folder>/result-summary.md`. Include:
- prompt version, date, and models used,
- what changed versus the previous evaluated prompt (run a diff between the two prompt files; for the first version write "Baseline"),
- the fixture list (so score comparability is clear),
- the score table, hard fails, and deltas,
- observations: patterns in misses and false positives, per-typo-category recall, and 2-4 concrete suggested prompt changes,
- per-fixture links to the run files and the full AI response inside a `<details>` block.

## 7. Update CHANGELOG
Fill `templates/changelog-entry.md` and insert it directly below the `<!-- ENTRIES -->` marker (newest first). Keep it minimal:
- prompt version and run folder link,
- reviewer/judge models,
- fixtures evaluated,
- overall score and delta,
- hard fails,
- one-line "what changed" summary,
- 2-4 concrete suggested next changes,
- a link to `<run_folder>/result-summary.md` for full details.

## 8. Report
Print a short summary: overall score and delta, per-fixture totals, hard fails, regressions, and the suggested next changes. Do not run any git commands (no staging, no saving to history) and do not modify `prompts/`, `fixtures/`, or `rubric/`.
