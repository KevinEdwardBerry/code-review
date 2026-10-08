## Code Review: `src/pagination.js`

### 🔴 Critical Bugs

**1. Off-by-one error in `getPage` (line ~8)**

```js
const start = page * pageSize;
```

The docstring says the page number is **1-based**, but the math treats it as 0-based. With `page = 1`, `start = pageSize`, so page 1 skips the first `pageSize` items entirely, and page 0 (or the last page) behaves incorrectly.

**Fix:**
```js
const start = (page - 1) * pageSize;
```

**2. `totalPages` truncates instead of rounding up (line ~16)**

```js
return Math.floor(items.length / pageSize);
```

With 25 items and `pageSize = 10`, this returns `2` instead of `3` — the final 5 items are unreachable. Page counts must round up:

**Fix:**
```js
return Math.ceil(items.length / pageSize);
```

### 🟡 Missing Input Validation

- **`pageSize <= 0`**: `Math.floor(n / 0)` → `Infinity` in `totalPages`, and `page * 0` in `getPage` silently returns an empty slice. Should throw or guard.
- **`page < 1`**: negative/0 page numbers produce negative `start`, and `slice` with a negative index reads from the end of the array — silently wrong results.
- **`items` not an array**: `.slice` / `.length` would throw `TypeError` on null/undefined — a friendlier guard may be warranted depending on conventions.

### 🟢 Minor Notes

- No test coverage is added alongside the new module — both bugs above would be caught by a trivial test (`getPage(items, 1, 10)` should return the first 10 items).
- `module.exports` (CommonJS) — fine if consistent with the rest of the codebase, but can't be verified since files weren't read.

### Verdict

**Request changes.** Both functions have correctness bugs in their core logic; `getPage` contradicts its own documented 1-based contract, and `totalPages` under-counts. Neither should merge as-is.
