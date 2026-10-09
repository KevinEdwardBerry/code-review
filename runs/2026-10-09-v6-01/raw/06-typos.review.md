## Summary
Low-risk addition of an account creation function with several spelling mistakes in user-facing strings, comments, and an exported function name.

## Findings
- [Low] src/accounts.ts:36 — Exported function name misspelled `getAdress`
  `export function getAdress(account: Account): string {` — part of the public API; consumers will be stuck with the typo. Fix: rename to `getAddress`.
- [Low] src/accounts.ts:23 — Misspellings in user-facing error message
  `throw new Error("Username lenght must be at least 3 charaters.")` — "lenght" → "length", "charaters" → "characters". Fix: `"Username length must be at least 3 characters."`
- [Low] src/accounts.ts — Cosmetic typos in comment, local variable, and public string
  `src/accounts.ts:16` `We recieve the raw form input and normalize it.` — "recieve" → "receive".
  `src/accounts.ts:19` `const retires = opts.maxRetries ?? DEFAULTS.maxRetries` — "retires" → "retries" (also used at line 32).
  `src/accounts.ts:40` `export const TEXT = "teh quick brown fox"` — "teh" → "the" (public string literal; "Colour" at line 42 is a valid variant and not flagged).

## Verdict
Approve with nits