# Code Review: `src/pagination.js`

## Summary
The diff adds two pagination helpers: `getPage` and `totalPages`. Both contain correctness bugs related to indexing and edge cases.

## Findings

### 🔴 Critical: Off-by-one error in `getPage`
The JSDoc states the page number is **1-based**, but the implementation treats it as 0-based:

```js
const start = page * pageSize;
```

For `page = 1, pageSize = 10`, this yields `start = 10`, skipping the entire first page. For a 1-based API it must be:

```js
const start = (page - 1) * pageSize;
```

This is the kind of bug that will silently drop the first `pageSize` items — easy to miss without a test asserting `getPage(items, 1, n)` returns the first `n` items.

### 🔴 Critical: `totalPages` undercounts when there’s a remainder

```js
return Math.floor(items.length / pageSize);
```

`Math.floor` truncates the partial last page. E.g., `items.length = 25, pageSize = 10` returns `2`, but there are `3` pages (the last with 5 items). Should be:

```js
return Math.ceil(items.length / pageSize);
```

### 🟡 No input validation
Both functions will produce confusing results rather than errors on invalid input:
- `getPage(items, 0, n)` or negative `page` → `slice` with negative indices returns items from the **end** of the array (silently wrong).
- `pageSize <= 0` → `totalPages` returns `Infinity` or `NaN`; `getPage` returns an empty array or the whole array depending on the sign.
- `items` not an array → `slice`/`length` throw or misbehave.

Recommend validating: `page >= 1`, `pageSize >= 1` (integer), and `Array.isArray(items)`, throwing `RangeError`/`TypeError` as appropriate.

### 🟡 Out-of-range pages silently return `[]`
`getPage(items, 999, 10)` returns `[]` rather than signaling the page doesn’t exist. This may be intended (lenient slicing) but should be documented, or clamped/validated against `totalPages`.

### 🟢 Minor: consistency/documentation
- Document units and types in JSDoc (`@param {Array} items`, `@param {number} page`, etc.) — especially since the 1-based contract is the source of the bug.
- Consider returning `0` pages for empty `items` (current code does this correctly once `Math.ceil` is used — `Math.ceil(0/x) = 0`, good).

## Suggested Fix

```js
function getPage(items, page, pageSize) {
  if (!Number.isInteger(page) || page < 1) throw new RangeError('page must be a positive integer');
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError('pageSize must be a positive integer');
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

function totalPages(items, pageSize) {
  if (!Number.isInteger(pageSize) || pageSize < 1) throw new RangeError('pageSize must be a positive integer');
  return Math.ceil(items.length / pageSize);
}
```

## Testing Recommendations
Add tests covering: first page, last partial page, `items.length % pageSize === 0`, empty array, page beyond range, `page = 0`, `pageSize = 0`.

## Verdict
**Request changes** — two functional bugs (off-by-one, floor vs. ceil) will cause incorrect pagination in any consumer of this module.
