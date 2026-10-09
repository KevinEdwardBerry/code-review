# Expected: 02-off-by-one

## Must find
- `page_offset` (high): `getPage` documents a 1-based page (`src/pagination.js:4`) but computes `const start = page * pageSize;` at `src/pagination.js:7`; page 1 skips the first page of items. Fix: `(page - 1) * pageSize`.
- `total_pages_floor` (medium): `totalPages` uses `Math.floor` at `src/pagination.js:16` (`return Math.floor(items.length / pageSize);`), dropping the final partial page. Fix: `Math.ceil`.

## Acceptable extras
- low/nit: no validation for page < 1 or pageSize <= 0 (division by zero gives Infinity).

## Must not flag
- Use of `module.exports`, or the style of the JSDoc comments.

## Hard fail
- Missing `page_offset` sets `missed_critical` (high).
