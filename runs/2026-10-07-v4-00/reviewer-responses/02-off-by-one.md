### Summary
Adds `getPage` and `totalPages` pagination helpers, but both contain off-by-one/truncation bugs: `getPage` treats `page` as 0-based despite documenting 1-based input, and `totalPages` floors instead of ceiling, dropping the last partial page.

### Findings
- **high src/pagination.js:6 - `getPage` uses 0-based offset despite 1-based contract**
  - Problem: The docstring says `page` is 1-based, but `start = page * pageSize` skips the first `pageSize` items on page 1 and returns the wrong slice for every page (page 1 returns items `pageSize..2*pageSize`, etc.).
  - Fix: Use `const start = (page - 1) * pageSize;`.
  - Code snippet:
    ```js
    const start = page * pageSize;
    ```

- **high src/pagination.js:15 - `totalPages` drops the last partial page**
  - Problem: `Math.floor(items.length / pageSize)` undercounts whenever `items.length` is not an exact multiple of `pageSize` (e.g. 25 items, pageSize 10 → 2 instead of 3), making the final page unreachable.
  - Fix: Use `Math.ceil(items.length / pageSize)`.
  - Code snippet:
    ```js
    return Math.floor(items.length / pageSize);
    ```

- **medium src/pagination.js:6-7 - invalid `page`/`pageSize` inputs produce silent wrong results**
  - Problem: `page <= 0` yields a negative `start`, so `items.slice` returns trailing items rather than an error or empty page; `pageSize <= 0` yields `NaN` (`totalPages`) or empty/incorrect slices. With 1-based semantics, page 0 should not silently return data.
  - Fix: Validate inputs, e.g. `if (page < 1) throw/return []` and `if (pageSize < 1) throw/return 0`, or clamp to valid ranges per intended contract.
  - Code snippet:
    ```js
    const start = page * pageSize;
    const end = start + pageSize;
    ```

### Verdict
request changes
