## Summary
Low-risk addition of account creation helpers; the only demonstrated defects are spelling errors in an exported function name, a user-facing error message, a public string constant, and comments/local identifiers.

## Findings
[Low] src/accounts.ts:36 — Misspelled exported function name `getAdress`
`export function getAdress(account: Account): string {`
Callers must use the misspelled name `getAdress`; renaming later becomes a breaking change.
Fix: rename to `getAddress` (keep an alias if the name is already consumed).

[Low] src/accounts.ts:23 — Misspellings in user-facing error message ("lenght", "charaters")
`    throw new Error("Username lenght must be at least 3 charaters.")`
Users see a misspelled validation message.
Fix: `"Username length must be at least 3 characters."`

[Low] src/accounts.ts:40 — Misspelling in exported public string constant ("teh")
`export const TEXT = "teh quick brown fox"`
The exported constant contains a typo.
Fix: `"the quick brown fox"` (unless intentionally testing typo data).

[Low] src/accounts.ts — Grouped cosmetic typos in comment and local identifier ("recieve", "retires")
` * We recieve the raw form input and normalize it.` (src/accounts.ts:16)
`  const retires = opts.maxRetries ?? DEFAULTS.maxRetries` (src/accounts.ts:19)
Comment and local variable misspellings reduce readability; no functional impact.
Fix: "receive" and `retries` (also update the use at src/accounts.ts:32).

## Verdict
Approve with nits
