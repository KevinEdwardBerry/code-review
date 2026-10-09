# Expected: 03-race-condition

## Must find
- `race_in_inc` (high): `Inc` does a check-then-act on a plain `Dictionary`: `TryGetValue` at `src/counter.cs:12`, then `counts[path] = count + 1;` at `src/counter.cs:13` (or `counts[path] = 1;` at `src/counter.cs:15`). Concurrent callers can lose increments or corrupt the dictionary. Fix: take a `lock` around the whole operation, or use `ConcurrentDictionary.AddOrUpdate`. The concurrent call site at `src/counter.cs:35` is acceptable supporting evidence and may be cited as part of this finding or as its own finding.
- `unlocked_read` (medium): `Count` reads `counts` without synchronization at `src/counter.cs:20` (`return counts.TryGetValue(path, out var count) ? count : 0;`) while `Inc` can write concurrently. Fix: read under the same `lock`, or use `ConcurrentDictionary`.
- `snapshot_leak` (medium): `Snapshot` returns the internal dictionary directly at `src/counter.cs:25` (`return counts;`), exposing it to unsynchronized enumeration and mutation by callers. Fix: return a copy made under the lock.

## Context
- `RequestHandler.HandleAllAsync` calls `Inc` concurrently via `Task.Run`/`Task.WhenAll` (`src/counter.cs:35`), so `RequestStats` is shared across threads. This is the evidence that makes the races demonstrable.
- Each unsynchronized access (`Inc`, `Count`, `Snapshot`) must be reviewed as its own path and anchored to its own line.

## Acceptable extras
- nit: consider using `ConcurrentDictionary<string, int>` instead of `Dictionary<string, int>` with manual locking.

## Must not flag
- The use of Dictionary or the method names.
- The `RequestHandler` class itself or its use of `Task.Run`, except as the evidence for the race.

## Hard fail
- Missing `race_in_inc` sets `missed_critical` (high).
- Missing both `unlocked_read` and `snapshot_leak` sets `missed_critical`.
