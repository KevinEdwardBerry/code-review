# Code Review: `src/pagination.js`

**Verdict: Request changes** — both functions contain correctness bugs.

## Critical issues

### 1. Off-by-one error in `getPage` (line ~7)
The docstring says pages are 1-based, but the math is 0-based:

```js
const start = page * pageSize;   // BUG
const start = (page - 1) * pageSize;  // correct for 1-based
```

As written, `getPage(items, 1, 10)` skips the first 10 items and returns items 10–19. Page 1 would silently drop data — the worst kind of pagination bug since nothing crashes.

### 2. `totalPages` drops the partial last page (line ~15)

```js
return Math.floor(items.length / pageSize);  // BUG
return Math.ceil(items.length / pageSize);   // correct
```

With 25 items and pageSize 10, this returns 2 instead of 3, so the last 5 items are unreachable. Combined with bug 1, data loss in both directions.

## Additional concerns

- **No input validation**: `pageSize <= 0` yields `Infinity`/`NaN` from `totalPages` and odd slices from `getPage`. `page < 1` produces negative indices (`slice` silently wraps to end-of-array — very surprising behavior). Consider throwing on `page < 1`, `pageSize < 1`, or non-integer inputs.
- **Out-of-range `page`**: returns `[]` silently, which may be acceptable, but worth documenting.
- **Naming**: `totalPages` takes `items` (the array) rather than a count — fine, but naming the param `items` while `getPage` also takes `items` is consistent, so OK. Just flagging that a `count`-based variant is often more reusable.
- **Mutability/copy**: `slice` returns a shallow copy — good, but the JSDoc should specify return type (`Array`, `number`) and `@param`/`@returns` tags for consistency with typical doc style.

## Suggested fix

```js
function getPage(items, page, pageSize) {
  if (pageSize < 1) throw new RangeError('pageSize must be >= 1');
  if (page < 1) throw new RangeError('page must be >= 1');
  const start = (page - 1) * pageSize;
  return items.slice(start, start + pageSize);
}

function totalPages(items, pageSize) {
  if (pageSize < 1) throw new RangeError('pageSize must be >= 1');
  return Math.ceil(items.length / pageSize);
}
```

**Tests to add before merging**: page 1 boundary, last partial page, empty array, `pageSize` > length, and invalid inputs. These are exactly the cases that would have caught both bugs.
