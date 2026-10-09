## Summary
New pagination helpers contain two off-by-one/correctness bugs: `getPage` ignores its documented 1-based contract, and `totalPages` rounds down, dropping the last partial page.

## Findings

[High] src/pagination.js:7 — `getPage` computes a 0-based offset despite the documented 1-based page number
> `  7 | +  const start = page * pageSize;`
The JSDoc states the page is 1-based, but `start = page * pageSize` means `getPage(items, 1, size)` returns items starting at index `size`, skipping the first page entirely. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `totalPages` floors the division, undercounting pages
> ` 16 | +  return Math.floor(items.length / pageSize);`
With `items.length = 10` and `pageSize = 3`, this returns 3 instead of 4, losing access to the last item(s). Fix: use `Math.ceil(items.length / pageSize)`.

## Verdict
Request changes