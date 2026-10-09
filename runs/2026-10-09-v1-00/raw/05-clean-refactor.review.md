## Code Review

**Verdict: Approve — behavior is equivalent, no blocking issues.**

### Correctness
- `items.Sum(item => item.Price * item.Quantity)` is semantically identical to the `foreach` accumulation. `Enumerable.Sum` with `decimal` selector accumulates in `decimal` without loss of precision.
- `subtotal * (1 + taxRate)` is algebraically identical to `total + total * taxRate`. The literal `1` is an `int`, but it implicitly converts to `decimal` in the expression, so there's no type error.
- `Sum` returns `0m` for an empty sequence, matching the old `total = 0m` initialization — no behavioral change for empty lists.
- Null `items` threw `NullReferenceException` before (foreach) and throws `ArgumentNullException` now (LINQ guards it) — slightly different exception type, but unlikely to matter.

### Minor suggestions (non-blocking)
1. **`1m` literal for clarity** — `subtotal * (1m + taxRate)` makes the decimal intent explicit and avoids relying on implicit int→decimal conversion. Cosmetic, but consistent with the old `0m` style.
2. **Overflow behavior** — same as before (`decimal` accumulates without checked context in both versions), so no change, just noting `Sum` uses `checked` internally; if individual line items can be extreme, `item.Price * item.Quantity` could throw `OverflowException`. That's a pre-existing characteristic worth being aware of.
3. Consider whether `List<Item>` could be `IEnumerable<Item>` or `IReadOnlyList<Item>` — LINQ removes the last reason to require a concrete `List`.

No changes required to merge.
