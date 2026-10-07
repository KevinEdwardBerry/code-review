---
prompt_version: v1
prompt_file: prompts/code-review.v1.md
fixture: 03-race-condition
date: 2026-10-07
reviewer_model: subagent_explore default model
judge_model: subagent_explore default model (same as reviewer; could not set a different one)
weighted_score: 95.0
hard_fail: false
---

# 03-race-condition / v1

## AI response
### Summary
Adds a mutex-protected per-path request counter. The write path is locked, but both read paths bypass the mutex or expose the shared map, so the type is still unsafe for concurrent use — the very thing the mutex is meant to fix.

### Findings
- **high src/counter.go:21 — `Count` reads the map without locking**
- Problem: `return s.counts[path]` runs while another goroutine may be holding the lock and writing in `Inc`. Concurrent map read/write is a data race and can panic with "concurrent map read and map write" in Go. This will fail `-race` and crash in normal use.
- Fix: acquire the lock (preferably `sync.RWMutex` with `s.mu.RLock()`/`RUnlock()`) before reading:
  ```go
  func (s *RequestStats) Count(path string) int {
      s.mu.RLock()
      defer s.mu.RUnlock()
      return s.counts[path]
  }
  ```

- **high src/counter.go:26 — `Snapshot` returns the internal map**
- Problem: Callers get a live reference to `s.counts`, so they can read/mutate it concurrently with `Inc` — same race/panic risk — and can corrupt internal state without the lock. It also silently sees later mutations.
- Fix: copy under the lock:
  ```go
  func (s *RequestStats) Snapshot() map[string]int {
      s.mu.RLock()
      defer s.mu.RUnlock()
      out := make(map[string]int, len(s.counts))
      for k, v := range s.counts {
          out[k] = v
      }
      return out
  }
  ```

- **nit src/counter.go:15-19 — unlock via `defer`**
- Manual `Lock`/`Unlock` works here but `defer s.mu.Unlock()` is more idiomatic and panic-safe if the body grows.

### Verdict
request changes

## Judge scores (AI)
| Criterion | Score (0-3) | Rationale |
|---|---|---|
| recall | 3 | Found both must-find issues. |
| precision | 3 | No false positives; defer nit is an acceptable extra. |
| severity_calibration | 3 | Matches expected. |
| actionability | 2 | Correct fixes, but cited line numbers are off (Count ~28, Snapshot ~33). |
| reasoning | 3 | Correct. |
| format | 3 | Follows format. |
| tone | 3 | Constructive, concise. |

- Matched: unlocked_read, snapshot_leak
- Missed: none
- False positives: none
- Typo recall: n/a

<details><summary>Judge JSON</summary>

```json
{"fixture": "03-race-condition", "scores": {"recall": 3, "precision": 3, "severity_calibration": 3, "actionability": 2, "reasoning": 3, "format": 3, "tone": 3}, "rationale": {"recall": "Found both must-find issues: unlocked_read (Count reads map without lock) and snapshot_leak (Snapshot returns internal map).", "precision": "No false positives; the defer-Unlock nit is an explicitly acceptable extra and Inc locking was not flagged.", "severity_calibration": "Both races marked high (expected high / high-medium), the defer note marked nit — matches expected.", "actionability": "Concrete fixes with correct code for both findings. However cited line numbers are off: Count's read is at file line ~28 (review says :21, which is Inc's Lock) and Snapshot's return is ~line 33 (review says :26). Code is real but line refs are inaccurate.", "reasoning": "Correctly explains Go concurrent map read/write panic risk, -race failure, and the aliasing/mutation hazard of returning the internal map.", "format": "Follows Summary / Findings / Verdict exactly, ordered by severity (high, high, nit), verdict 'request changes'.", "tone": "Constructive, concise, no filler."}, "matched": ["unlocked_read", "snapshot_leak"], "missed": [], "false_positives": [], "typo_recall": null, "hard_fail": {"missed_critical": false, "fabricated": false, "missed_behavioral_typo": false}}
```
</details>

## Human override
<!-- Fill in changed scores and a reason. Leave blank to accept the AI scores. -->

## Notes
