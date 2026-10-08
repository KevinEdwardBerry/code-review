---
prompt_version: v7
prompt_file: prompts/code-review-v7.md
fixture: 06-typos
date: 2026-10-08
reviewer_model: unknown concrete model
reviewer_profile: subagent_explore
judge_model: unknown concrete model
judge_profile: subagent_general
weighted_score: 75.0
hard_fail: none
---

# 06-typos / v7

## Models
- Reviewer: subagent_explore (unknown concrete model)
- Judge: subagent_general (unknown concrete model)

## AI response
## Code Review: `src/accounts.ts`

### 🔴 Critical — Compile/runtime errors

1. **`opts.maxRetires` is a typo** (line ~`const retries = ...`). `DEFAULTS` defines `maxRetries`, so `opts.maxRetires` is a TypeScript compile error: `Property 'maxRetires' does not exist on type 'Partial<{ maxRetries: number; timeoutMs: number; }>'`. Fix: `opts.maxRetries ?? DEFAULTS.maxRetries`.

2. **`usernam.lenght` is a typo** — `lenght` is not a real property; this throws `TypeError` (or fails compile since `string` has no `lenght`). Fix: `usernam.length`.

### 🟠 Significant issues

3. **`adress` field misspelled** throughout: interface `Account.adress`, usage `input.adress`, and public API `getAdress()`. If this ships, it propagates the misspelling into the public contract. Fix to `address`/`getAddress` before release (breaking change later).

4. **Misleading docstring**: "Creates a new account and sends a welcome email" — no email is sent and nothing is persisted; it only normalizes and returns an object. Either implement or correct the comment. Also "recieve" → "receive".

5. **`timeoutMs` option is accepted but never used** — same for `retries`, which is only logged. Either wire them up or remove from the options type to avoid a misleading API.

6. **No email validation/normalization**: `input.email` is stored raw (no trim/lowercase/format check), inconsistent with username handling.

7. **`input.adress` passed through untrimmed** — normalize consistently.

### 🟡 Minor / polish

8. `usernam` variable name missing the final `e` — rename to `normalizedUsername` or `username`.
9. `"Username must be at least 3 charcters long"` — typo: `characters`.
10. `TEXT = "teh quick brown fox"` — `teh` → `the`. Also this constant looks like leftover test data; question whether it belongs in this module.
11. `LABEL = "Acme Colour Labs"` — `Colour` is valid British English, but verify it matches the project's spelling convention (US vs UK).
12. `console.log` in a service layer — prefer an injected/logger dependency; log statements also expose account data.

### Suggested corrected core

```ts
export interface Account {
  username: string;
  email: string;
  address: string;
}

export function createAccount(input: Account, opts: Partial<typeof DEFAULTS> = {}) {
  const retries = opts.maxRetries ?? DEFAULTS.maxRetries;
  const username = input.username.trim().toLowerCase();

  if (username.length < 3) {
    throw new Error("Username must be at least 3 characters long");
  }

  const account: Account = {
    username,
    email: input.email.trim().toLowerCase(),
    address: input.address.trim(),
  };
  return account;
}
```

**Verdict: Request changes** — items 1 and 2 are hard blockers; items 3–6 should be resolved before merge since they affect the public API surface.


## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| Recall | 3 | Found all five expected typo items: t1_maxretires, t2_lenght, t3_adress_api, t4_charcters, and t5_recieve. |
| Precision | 1 | Flagged multiple must-not-flag items (teh in TEXT, usernam abbreviation, and questioned Colour) and included several unseeded non-typo observations. |
| Severity calibration | 3 | Behavior-changing typos t1 and t2 were ranked Critical, above the public API and cosmetic typos. |
| Actionability | 2 | Provided concrete fixes and a corrected code block, but most findings lacked exact file:line references. |
| Reasoning correctness | 2 | Explanations for t1 and t3 were correct; t2s runtime claim was partly wrong because undefined < 3 is silently false rather than a thrown TypeError. |
| Format adherence | 2 | Used severity-ordered sections, but deviated from the Summary/Findings/Verdict structure with emojis and extra sections. |
| Tone and concision | 2 | Constructive but noisy, with a long list of minor and unseeded concerns alongside the expected typos. |

- Matched: t1_maxretires, t2_lenght, t3_adress_api, t4_charcters, t5_recieve
- Missed: none
- False positives: "teh in TEXT literal"; "usernam local abbreviation"; "Colour in LABEL (valid British spelling)"
- Typo recall: {"misspelling": "1/1", "swap": "2/2", "missing_letter": "2/2"}

<details><summary>Judge JSON</summary>

```json
{
  "fixture": "06-typos",
  "scores": {
    "recall": 3,
    "precision": 1,
    "severity_calibration": 3,
    "actionability": 2,
    "reasoning": 2,
    "format": 2,
    "tone": 2
  },
  "rationale": {
    "recall": "Found all five expected typo items: t1_maxretires, t2_lenght, t3_adress_api, t4_charcters, and t5_recieve.",
    "precision": "Flagged multiple must-not-flag items (teh in TEXT, usernam abbreviation, and questioned Colour) and included several unseeded non-typo observations.",
    "severity_calibration": "Behavior-changing typos t1 and t2 were ranked Critical, above the public API and cosmetic typos.",
    "actionability": "Provided concrete fixes and a corrected code block, but most findings lacked exact file:line references.",
    "reasoning": "Explanations for t1 and t3 were correct; t2s runtime claim was partly wrong because undefined < 3 is silently false rather than a thrown TypeError.",
    "format": "Used severity-ordered sections, but deviated from the Summary/Findings/Verdict structure with emojis and extra sections.",
    "tone": "Constructive but noisy, with a long list of minor and unseeded concerns alongside the expected typos."
  },
  "matched": [
    "t1_maxretires",
    "t2_lenght",
    "t3_adress_api",
    "t4_charcters",
    "t5_recieve"
  ],
  "missed": [],
  "false_positives": [
    "teh in TEXT literal",
    "usernam local abbreviation",
    "Colour in LABEL (valid British spelling)"
  ],
  "typo_recall": {
    "misspelling": "1/1",
    "swap": "2/2",
    "missing_letter": "2/2"
  },
  "hard_fail": {
    "missed_critical": false,
    "fabricated": false,
    "missed_behavioral_typo": false
  }
}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
