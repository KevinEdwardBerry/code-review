---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 01-sql-injection
date: 2026-10-07
reviewer_profile: subagent_explore
reviewer_model: subagent_explore default model
judge_profile: subagent_explore
judge_model: subagent_explore default model (same as reviewer; could not set a different one)
weighted_score: 88.3
hard_fail: false
---

# 01-sql-injection / v1


## Models
- Reviewer: subagent_explore (subagent_explore default model)
- Judge: subagent_explore (subagent_explore default model (same as reviewer; could not set a different one))

## AI response
### Summary
Adds `find_user_by_name` which queries SQLite for a user by name. The function is vulnerable to SQL injection and leaks the connection if the query raises.

### Findings
- **[critical] src/users.py:12 - SQL injection via string-concatenated query**
- Problem: `name` is interpolated directly into the SQL string. Input like `' OR '1'='1` (or `'; DROP TABLE users;--`) lets an attacker bypass matching, exfiltrate arbitrary rows, or execute destructive statements.
- Fix: Use a parameterized query:
  ```python
  cur.execute("SELECT id, name, email FROM users WHERE name = ?", (name,))
  ```

- **[medium] src/users.py:11-16 - Connection leaked if execute/fetchone raises**
- Problem: `conn.close()` only runs on the happy path. If `cur.execute` or `fetchone` throws, the connection (and its lock on `app.db`) is left open, which can degrade to database-lock errors under repeated failures.
- Fix: Use a context manager or try/finally:
  ```python
  conn = get_db()
  try:
      cur = conn.cursor()
      cur.execute("SELECT id, name, email FROM users WHERE name = ?", (name,))
      return cur.fetchone()
  finally:
      conn.close()
  ```
  (Or `contextlib.closing` / `with conn:`.)

- **[low] src/users.py:14-15 - Cursor not explicitly closed**
- Problem: The cursor object is dropped without `cur.close()`. Usually harmless in CPython due to refcounting, but closing the connection first means it's benign — worth tidying once the try/finally fix is applied.

### Verdict
request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | Found the critical SQL injection and the acceptable-extra connection leak; all seeded issues covered. |
| precision | 2 | No false positives; the extra cursor-not-closed nit is trivial noise, so minor deduction. |
| severity_calibration | 2 | sqli correctly critical; connection leak rated medium where expected treats it as low/nit. |
| actionability | 3 | Concrete fixes and correct file:line references. |
| reasoning | 3 | Correct, articulates impact. |
| format | 3 | Follows Summary / Findings / Verdict. |
| tone | 3 | Constructive, concise. |

- Matched: sqli
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{"fixture":"01-sql-injection","scores":{"recall":3,"precision":2,"severity_calibration":2,"actionability":3,"reasoning":3,"format":3,"tone":3},"rationale":{"recall":"Found the critical SQL injection (sqli) at src/users.py and the acceptable-extra connection leak; all seeded issues covered.","precision":"No false positives and nothing must-not-flag was flagged; the extra cursor-not-closed nit is trivial noise, so minor deduction.","severity_calibration":"sqli correctly rated critical; the connection leak is rated medium where expected treats it as low/nit — one level off.","actionability":"Each finding has a concrete fix (parameterized query, try/finally) and correct file:line references consistent with the diff.","reasoning":"Explanations are correct and articulate impact (auth bypass, data exfiltration/destruction, DB lock on leaked connection).","format":"Follows Summary / Findings / Verdict structure with findings ordered by severity and a clear verdict.","tone":"Constructive, concise, no filler."},"matched":["sqli"],"missed":[],"false_positives":[],"typo_recall":null,"hard_fail":{"missed_critical":false,"fabricated":false,"missed_behavioral_typo":false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
