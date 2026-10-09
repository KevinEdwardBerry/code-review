## Summary
New pagination helpers contain two off-by-one math errors that return wrong results on every call.

## Findings

[High] src/pagination.js:7 — off-by-one start index ignores the documented 1-based page numbering
`  7 | +  const start = page * pageSize;`
For page 1 this yields `start = pageSize`, skipping the first `pageSize` items and returning the wrong slice for every page. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `Math.floor` drops the final partial page
`  16 | +  return Math.floor(items.length / pageSize);`
For `items.length = 10, pageSize = 4` this returns 2 instead of 3, so callers can never reach the last 2 items. Fix: `return Math.ceil(items.length / pageSize);`

## Verdict
Request changes
