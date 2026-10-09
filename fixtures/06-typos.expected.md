# Expected: 06-typos

Typos are of three kinds: `misspelling`, `swap` (transposed letters), `missing_letter`. None of them changes behavior, so all are Low or Medium at most; no finding here may be High or Critical.

## Must find (public API / user-facing)
- `t1_adress_api` (low/medium, missing_letter): the exported function `getAdress` (`src/accounts.ts:36`) should be `getAddress`. Costly to rename later, so flag now.
- `t2_lenght` (low, swap): the user-facing error message at `src/accounts.ts:23` uses "lenght" instead of "length".
- `t3_charaters` (low, missing_letter): the same message at `src/accounts.ts:23` uses "charaters" instead of "characters". May be reported in one finding together with `t2_lenght`.
- `t6_teh_text` (low, swap): the exported string constant `TEXT` (`src/accounts.ts:40`) uses "teh" instead of "the". String literals are in scope unless explicitly documented as acceptable.

## Must find (cosmetic)
- `t4_retires` (nit/low, swap): the local variable `retires` (`src/accounts.ts:19`) should be `retries`.
- `t5_recieve` (nit/low, misspelling): the comment at `src/accounts.ts:16` ("We recieve the raw form input") should be "receive".

## Typo categories for recall
- misspelling: t5 (1)
- swap: t2, t4, t6 (3)
- missing_letter: t1, t3 (2)

## Must not flag (false positives)
- `Colour` in `LABEL` (`src/accounts.ts:42`): valid British spelling in a proper name.

## Ranking expectation
`t1_adress_api` should rank above the user-facing message typos (`t2`, `t3`), which should rank above the public string typo (`t6`), which should rank above the cosmetic identifier/comment typos (`t4`, `t5`). Low-impact cosmetic typos (`t4`, `t5`) may be grouped into one finding.

## Hard fail
- None: this version has no behavior-changing typo.
