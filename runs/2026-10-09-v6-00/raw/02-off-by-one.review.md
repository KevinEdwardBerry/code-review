## Summary
New pagination helpers contain two off-by-one/counting errors that return wrong items and undercount pages.

## Findings

[High] src/pagination.js:7 — `getPage` skips the first page for a documented 1-based page number
> `const start = page * pageSize;`
For a 1-based `page`, `getPage(items, 1, 10)` computes `start = 10`, dropping the first 10 items; page N returns items belonging to page N+1. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `totalPages` drops the final partial page
> `return Math.floor(items.length / pageSize);`
`Math.floor` undercounts when `items.length` isn't a multiple of `pageSize` (e.g., 25 items / 10 per page returns 2 instead of 3), making the last items unreachable. Fix: use `Math.ceil(items.length / pageSize)`.

## Verdict
Request changes