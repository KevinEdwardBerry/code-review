# Expected: 03-race-condition

## Must find
- `unlocked_read` (high): `Count` reads `counts` without synchronization; concurrent read/write of the dictionary can cause data corruption or exceptions. Fix: use `lock` statement or `ReaderWriterLockSlim` in `Count`.
- `snapshot_leak` (high/medium): `Snapshot` returns the internal dictionary directly, exposing it to unsynchronized access by callers. Fix: copy the dictionary under lock.
- `race_in_inc` (high): `Inc` checks `ContainsKey` and then accesses/modifies the dictionary without atomicity; between the check and the increment, another thread could modify the same key. Fix: use `lock` statement around the entire operation.

## Context
- `RequestHandler.HandleAllAsync` calls `Inc` concurrently via `Task.Run`/`Task.WhenAll`, so `RequestStats` is shared across threads. This is the evidence that makes the races demonstrable.

## Acceptable extras
- nit: consider using `ConcurrentDictionary<string, int>` instead of `Dictionary<string, int>` with manual locking.

## Must not flag
- The use of Dictionary or the method names.
- The `RequestHandler` class itself or its use of `Task.Run`.

## Hard fail
- Missing `unlocked_read` and `snapshot_leak` sets `missed_critical`.
