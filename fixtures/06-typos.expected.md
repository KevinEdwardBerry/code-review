# Expected: 06-typos

Typos are of three kinds: `misspelling`, `swap` (transposed letters), `missing_letter`.

## Must find (public API / user-facing)
- `t1_adress_api` (medium, missing_letter): the exported function `getAdress` should be `getAddress`. Costly to rename later, so flag now.
- `t2_lenght` (low/medium, swap): the user-facing error message uses "lenght" instead of "length".
- `t3_charaters` (low/medium, missing_letter): the user-facing error message uses "charaters" instead of "characters".
- `t6_teh_text` (low, swap): the exported string constant `TEXT` uses "teh" instead of "the". String literals are in scope unless explicitly documented as acceptable.

## Must find (cosmetic)
- `t4_retires` (nit, swap): the local variable `retires` should be `retries`.
- `t5_recieve` (nit, misspelling): comment "We recieve the raw form input" should be "receive".

## Typo categories for recall
- misspelling: t5 (1)
- swap: t2, t4, t6 (3)
- missing_letter: t1, t3 (2)

## Must not flag (false positives)
- `Colour` in `LABEL`: valid British spelling in a proper name.

## Ranking expectation
`t1_adress_api` should rank above the user-facing message typos (`t2`, `t3`), which should rank above the public string typo (`t6`), which should rank above the cosmetic identifier/comment typos (`t4`, `t5`).

## Hard fail
- None: this version has no behavior-changing typo.
