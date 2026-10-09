## Summary
New pagination helpers contain two correctness bugs: a 1-based off-by-one in `getPage` and use of `Math.floor` instead of `Math.ceil` in `totalPages`.

## Findings
[High] src/pagination.js:7 — `getPage` skips the first `pageSize` items on page 1
> `  const start = page * pageSize;`
The docstring states `page` is 1-based, so `page=1` yields `start = pageSize` instead of `0`, skipping the first page's items. Fix: `const start = (page - 1) * pageSize;`

[High] src/pagination.js:16 — `totalPages` undercounts when items don't divide evenly
> `  return Math.floor(items.length / pageSize);`
With 11 items and pageSize 10, this returns 1, so the last item is unreachable. Fix: `Math.ceil(items.length / pageSize);`

## Verdict
Request changes
