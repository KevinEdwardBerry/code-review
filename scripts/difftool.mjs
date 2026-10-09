#!/usr/bin/env node
// Diff helpers for the review harness.
//
//   node scripts/difftool.mjs annotate <diff>                 print diff with new-file line numbers
//   node scripts/difftool.mjs check <diff> <review.md>        verify file:line citations + quoted excerpts (JSON)
//   node scripts/difftool.mjs expected <diff> <expected.md>   verify file:line refs inside an expected file (JSON)
import { readFileSync } from "node:fs";

const HUNK = /^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@/;
const CITE = /([\w./\\-]+\.\w+):(\d+)(?:-(\d+))?/g;
const CITE_FULL = /^([\w./\\-]+\.\w+):(\d+)(?:-(\d+))?$/;
const TICKS = /``(.+?)``|`([^`\n]+)`/g;
const SEV = /^\s*(?:[-*]\s*)?\[(?:Critical|High|Medium|Low)\]/i;

const lines = (t) => t.replace(/\r?\n$/, "").split(/\r?\n/);
const norm = (s) => s.replace(/\s+/g, " ").trim();

function parse(text) {
  const files = {}, out = [];
  let path = null, n = null;
  for (const raw of lines(text)) {
    let m;
    if (raw.startsWith("+++ ")) {
      const p = raw.slice(4).trim();
      path = p === "/dev/null" ? null : p.replace(/^b\//, "");
      files[path] ??= new Map();
      n = null;
      out.push(raw);
    } else if ((m = HUNK.exec(raw))) {
      n = Number(m[1]);
      out.push(raw);
    } else if (n !== null && path !== null && (raw[0] === "+" || raw[0] === " ")) {
      files[path].set(n, raw.slice(1));
      out.push(`${String(n).padStart(4)} | ${raw}`);
      n++;
    } else {
      out.push(n !== null ? `     | ${raw}` : raw);
    }
  }
  return { files, annotated: out };
}

function blocks(review) {
  const out = [];
  let cur = [];
  for (const line of lines(review)) {
    if (SEV.test(line) || line.startsWith("## ")) {
      if (cur.length) out.push(cur);
      cur = SEV.test(line) ? [line] : [];
    } else cur.push(line);
  }
  if (cur.length) out.push(cur);
  return out.map((b) => b.join("\n"));
}

function quotesOf(block) {
  const qs = [];
  let fenced = false;
  for (const line of lines(block)) {
    if (line.trim().startsWith("```")) { fenced = !fenced; continue; }
    if (fenced) qs.push(norm(line));
    else for (const m of line.matchAll(TICKS)) qs.push(norm(m[1] ?? m[2]));
  }
  return qs.filter((q) => q.length >= 8 && !CITE_FULL.test(q));
}

function check(files, review, quotesToo = true) {
  const problems = [];
  let n = 0;
  for (const block of blocks(review)) {
    const quotes = quotesToo ? quotesOf(block) : [];
    for (const m of block.matchAll(CITE)) {
      const [cite, path] = m;
      const a = Number(m[2]), b = Number(m[3] ?? m[2]);
      if (!(path in files)) { problems.push({ cite, reason: "file not in diff" }); continue; }
      n++;
      const fileLines = files[path];
      const range = Array.from({ length: Math.max(b - a + 1, 0) }, (_, i) => a + i);
      if (range.some((i) => !fileLines.has(i))) {
        problems.push({ cite, reason: "line not in diff's new-file lines" });
        continue;
      }
      const target = norm(range.map((i) => fileLines.get(i)).join(" "));
      if (quotes.length && !quotes.some((q) => q.includes(target) || target.includes(q)))
        problems.push({ cite, reason: "no quoted excerpt in this finding matches the cited line", actual_line: target });
    }
  }
  return { citations_checked: n, problems, ok: problems.length === 0 };
}

const [cmd, diffPath, otherPath] = process.argv.slice(2);
if (!["annotate", "check", "expected"].includes(cmd) || !diffPath) {
  console.error(readFileSync(new URL(import.meta.url), "utf8").split("\n").slice(1, 5).map((l) => l.slice(3)).join("\n"));
  process.exit(2);
}
const { files, annotated } = parse(readFileSync(diffPath, "utf8"));
if (cmd === "annotate") console.log(annotated.join("\n"));
else {
  const res = check(files, readFileSync(otherPath, "utf8"), cmd === "check");
  console.log(JSON.stringify(res, null, 2));
  process.exit(res.ok ? 0 : 1);
}
