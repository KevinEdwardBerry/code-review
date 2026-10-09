## Summary
Low-risk refactor that replaces a manual accumulation loop with `Enumerable.Sum` and algebraically equivalent tax computation (`total + total * taxRate` ≡ `subtotal * (1 + taxRate)`).

## Findings
None.

## Verdict
Approve
