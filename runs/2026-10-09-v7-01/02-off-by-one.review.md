## Summary
The new pagination helpers contain two arithmetic bugs: `getPage` treats the page number as 0-based despite the documented 1-based contract, and `totalPages` truncates instead of rounding up, losing the last partial page.

## Findings
[High] src/pagination.js:7 — Off-by-one makes page 1 skip the first `pageSize` items
> `  7 | +  const start = page * pageSize;`
The docstring states `page` is 1-based, but with `page = 1`, `start = pageSize`, so the first `pageSize` items are never returned and the last page goes out of range. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `Math.floor` drops the final partial page
> ` 16 | +  return Math.floor(items.length / pageSize);`
For 10 items with `pageSize = 3`, this returns 3 instead of 4, so the last page of items is unreachable. Fix: `return Math.ceil(items.length / pageSize);`

## Verdict
Request changes
