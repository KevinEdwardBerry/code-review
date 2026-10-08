# Expected: 06-typos

Typos are of three kinds: `misspelling`, `swap` (transposed letters), `missing_letter`.

## Must find (public API / user-facing)
- `t1_adress_api` (medium, missing_letter): the exported function `getAdress` should be `getAddress`. Costly to rename later, so flag now.
- `t2_lenght` (low/medium, swap): the user-facing error message uses "lenght" instead of "length".
- `t3_charaters` (low/medium, missing_letter): the user-facing error message uses "charaters" instead of "characters".

## Must find (cosmetic)
- `t4_retires` (nit, swap): the local variable `retires` should be `retries`.
- `t5_recieve` (nit, misspelling): comment "We recieve the raw form input" should be "receive".

## Typo categories for recall
- misspelling: t5 (1)
- swap: t2, t4 (2)
- missing_letter: t1, t3 (2)

## Must not flag (false positives)
- `teh` in `TEXT`: literal data, not a spelling issue in prose or an API name.
- `Colour` in `LABEL`: valid British spelling in a proper name.

## Ranking expectation
`t1_adress_api` should rank above the user-facing message typos, which should rank above the cosmetic identifier/comment typos.

## Hard fail
- None: this version has no behavior-changing typo.
