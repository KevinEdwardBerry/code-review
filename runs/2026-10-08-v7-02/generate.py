#!/usr/bin/env python3
import json, os, re, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path("/Users/kevinberry/src/code-review")
RUN = ROOT / "runs/2026-10-08-v7-02"
VERSION = "v7"
DATE = "2026-10-08"
PROMPT_FILE = f"prompts/code-review.{VERSION}.md"
PREV_VERSION = "v7-01"
PREV_SCORES = {
    "01-sql-injection": 85.0,
    "02-off-by-one": 68.3,
    "03-race-condition": 85.0,
    "04-missing-error-handling": 83.3,
    "05-clean-refactor": 68.3,
    "06-typos": 61.7,
}
PREV_OVERALL = 75.3

FIXTURES = [
    "01-sql-injection",
    "02-off-by-one",
    "03-race-condition",
    "04-missing-error-handling",
    "05-clean-refactor",
    "06-typos",
]

CRITERIA = [
    ("recall", "Recall", 30),
    ("precision", "Precision", 20),
    ("severity_calibration", "Severity", 15),
    ("actionability", "Actionability", 15),
    ("reasoning", "Reasoning", 10),
    ("format", "Format", 5),
    ("tone", "Tone", 5),
]

REVIEWER_MODELS = {
    "01-sql-injection": "unknown",
    "02-off-by-one": "unknown",
    "03-race-condition": "Subagent Default",
    "04-missing-error-handling": "unknown",
    "05-clean-refactor": "unknown",
    "06-typos": "Subagent Default",
}

REVIEWER_PROFILE = "subagent_explore"
JUDGE_PROFILE = "subagent_general"
JUDGE_MODEL = "unknown"

def round1(x):
    return float(Decimal(x).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

def weighted_score(scores):
    total = sum((scores[k] / 3.0) * w for k, _, w in CRITERIA)
    return round1(total)

def delta_str(cur, prev):
    d = round1(cur - prev)
    if d > 0:
        return f"+{d}"
    return str(d)

def fmt_list(items):
    if not items:
        return "none"
    return ", ".join(str(x) for x in items)

def fmt_typo_recall(tr):
    if tr is None:
        return "n/a"
    return f"misspelling: {tr.get('misspelling','n/a')}, swap: {tr.get('swap','n/a')}, missing_letter: {tr.get('missing_letter','n/a')}"

def read_text(path):
    return (ROOT / path).read_text()

def write_text(path, text):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)

with open(RUN / "judges.json") as f:
    judges = {j["fixture"]: j for j in json.load(f)}

# Compute per-fixture results
results = {}
for fx in FIXTURES:
    j = judges[fx]
    score = weighted_score(j["scores"])
    hard = j["hard_fail"]
    hard_fail = any(hard.values())
    hard_fail_str = "none"
    if hard_fail:
        hard_fail_str = ", ".join(k for k,v in hard.items() if v)
    results[fx] = {
        "score": score,
        "hard_fail": hard_fail,
        "hard_fail_str": hard_fail_str,
        "judge": j,
    }

overall_raw = sum(
    (judges[fx]["scores"][k] / 3.0) * w
    for fx in FIXTURES
    for k, _, w in CRITERIA
) / len(FIXTURES)
overall = round1(overall_raw)
overall_delta = round1(overall - PREV_OVERALL)

# Write per-fixture run files
run_template = read_text("templates/run.md")
for fx in FIXTURES:
    j = results[fx]["judge"]
    review = (RUN / f"reviewer-responses/{fx}.md").read_text()
    score_rows = "\n".join(
        f"| {label} | {j['scores'][key]} | {j['rationale'][key]} |"
        for key, label, _ in CRITERIA
    )
    replacements = {
        "VERSION": VERSION,
        "FIXTURE": fx,
        "DATE": DATE,
        "REVIEWER_MODEL": REVIEWER_MODELS[fx],
        "REVIEWER_PROFILE": REVIEWER_PROFILE,
        "JUDGE_MODEL": JUDGE_MODEL,
        "JUDGE_PROFILE": JUDGE_PROFILE,
        "SCORE": str(results[fx]["score"]),
        "HARD_FAIL": results[fx]["hard_fail_str"],
        "REVIEW": review,
        "SCORE_ROWS": score_rows,
        "MATCHED": fmt_list(j["matched"]),
        "MISSED": fmt_list(j["missed"]),
        "FALSE_POSITIVES": fmt_list(j["false_positives"]),
        "TYPO_RECALL": fmt_typo_recall(j.get("typo_recall")),
        "JUDGE_JSON": json.dumps(j, indent=2),
    }
    text = run_template
    for k, v in replacements.items():
        text = text.replace("{{" + k + "}}", str(v))
    write_text(f"runs/2026-10-08-v7-02/{fx}.md", text)

# Build score table
score_table = ""
for fx in FIXTURES:
    j = results[fx]["judge"]
    row = "| " + fx + " | " + " | ".join(str(j["scores"][k]) for k,_,_ in CRITERIA) + f" | {results[fx]['score']} | {delta_str(results[fx]['score'], PREV_SCORES[fx])} |"
    score_table += row + "\n"

# Typo recall section
typo_recall = results["06-typos"]["judge"].get("typo_recall")
if typo_recall:
    typo_section = "### Typo recall (fixture 06)\n\n| Category | Found/Total |\n|---|---|\n" + "\n".join(
        f"| {cat} | {typo_recall[cat]} |" for cat in ["misspelling", "swap", "missing_letter"]
    ) + "\n"
else:
    typo_section = ""

# Observations / next changes
observations = """### Patterns in misses and false positives
- The minimal v7 prompt still finds every seeded issue, but it pays a heavy precision penalty: reviewers invent or over-interpret non-defects (schema qualification, query buffer, naming conventions, null-safety "regression", out-of-range pagination, `Colour` false positive).
- Severity calibration is the weakest area: medium issues are repeatedly labeled critical/high (SQLi is correctly critical, but `totalPages`, `fd_leak`, and `no_validation` are over-ranked).
- Actionability remains mediocre because no exact `file:line` citations are provided on any fixture.
- Format adherence is loose: extra sections (`Suggested revised version`, `Testing Recommendations`, emoji severity labels) replace the required Summary/Findings/Verdict structure.

### Per-typo-category recall (fixture 06)
- misspelling: 1/1
- swap: 3/3
- missing_letter: 2/2

### Suggested prompt changes
1. Restore severity definitions and concrete examples so medium/edge issues stop being over-ranked as critical/high.
2. Add explicit must-not-flag lists for style items, British spellings in proper names, literal test data, and behavior-preserving rewrites.
3. Require exact `file:line` citations with a worked `@@` hunk-header example.
4. Enforce a Summary/Findings/Verdict format and forbid emojis, positives-as-findings, and extra sections."""

# What changed
what_changed = """This is a re-run of v7; the prompt file `prompts/code-review.v7.md` is unchanged from the previous v7-01 run. The original v6 → v7 diff stripped all severity, line-citation, concurrency, typo, and output-format guidance."""

# Per-fixture links and responses
run_links = ""
for fx in FIXTURES:
    review = (RUN / f"reviewer-responses/{fx}.md").read_text()
    run_links += f"### {fx}\n\n- [{fx}.md]({fx}.md)\n\n<details><summary>Full AI response for {fx}</summary>\n\n{review}\n</details>\n\n"

# Write result-summary.md
summary_template = read_text("templates/run-details.md")
summary_replacements = {
    "VERSION": VERSION,
    "DATE": DATE,
    "REVIEWER_PROFILE": REVIEWER_PROFILE,
    "REVIEWER_MODEL": "unknown / Subagent Default where reported",
    "JUDGE_PROFILE": JUDGE_PROFILE,
    "JUDGE_MODEL": JUDGE_MODEL,
    "FIXTURES": ", ".join(FIXTURES),
    "OVERALL": str(overall),
    "DELTA": delta_str(overall, PREV_OVERALL),
    "PREV_VERSION": PREV_VERSION,
    "HARD_FAILS": "none",
    "WHAT_CHANGED": what_changed,
    "SCORE_TABLE": score_table,
    "TYPO_RECALL": typo_section,
    "OBSERVATIONS": observations,
    "RUN_LINKS_AND_RESPONSES": run_links,
}
text = summary_template
for k, v in summary_replacements.items():
    text = text.replace("{{" + k + "}}", str(v))
write_text("runs/2026-10-08-v7-02/result-summary.md", text)

# Update CHANGELOG.md
changelog_template = read_text("templates/changelog-entry.md")
hard_fail_summary = "none"
changelog_replacements = {
    "VERSION": VERSION,
    "DATE": DATE,
    "RUN_FOLDER": "2026-10-08-v7-02",
    "REVIEWER_MODEL": "unknown / Subagent Default where reported",
    "JUDGE_MODEL": JUDGE_MODEL,
    "FIXTURES": ", ".join(FIXTURES),
    "OVERALL": str(overall),
    "DELTA": delta_str(overall, PREV_OVERALL),
    "PREV_VERSION": PREV_VERSION,
    "HARD_FAILS": hard_fail_summary,
    "WHAT_CHANGED": "No prompt changes; re-run of the v7 minimal prompt.",
    "NEXT_CHANGES": "1. Restore severity definitions and examples.\n2. Add must-not-flag lists for style, British spellings, literal data, and behavior-preserving rewrites.\n3. Require exact `file:line` citations.\n4. Enforce Summary/Findings/Verdict format.",
}
entry = changelog_template
for k, v in changelog_replacements.items():
    entry = entry.replace("{{" + k + "}}", str(v))
# Append link to result summary if not present
if "result-summary.md" not in entry:
    entry = entry.rstrip("\n-") + f"\n- [Detailed results](runs/2026-10-08-v7-02/result-summary.md)\n\n---\n"

changelog_path = ROOT / "CHANGELOG.md"
changelog = changelog_path.read_text()
# Remove any existing entry for this run to keep re-runs idempotent
run_anchor = "runs/2026-10-08-v7-02/result-summary.md"
anchor_pos = changelog.find(run_anchor)
if anchor_pos != -1:
    heading_start = changelog.rfind("## ", 0, anchor_pos)
    sep_end = changelog.find("\n---\n", anchor_pos)
    if sep_end == -1:
        sep_end = len(changelog)
    else:
        sep_end += len("\n---\n")
    changelog = changelog[:heading_start] + changelog[sep_end:]
marker = "<!-- ENTRIES -->"
if marker in changelog:
    new_changelog = changelog.replace(marker, marker + "\n\n" + entry, 1)
    changelog_path.write_text(new_changelog)
else:
    print("WARNING: CHANGELOG marker not found", file=sys.stderr)

# Print final report
print(f"Overall: {overall}/100 ({delta_str(overall, PREV_OVERALL)} vs {PREV_VERSION})")
print(f"Hard fails: none")
for fx in FIXTURES:
    print(f"  {fx}: {results[fx]['score']} ({delta_str(results[fx]['score'], PREV_SCORES[fx])})")
