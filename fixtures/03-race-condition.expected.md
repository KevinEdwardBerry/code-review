# Expected: 03-race-condition

## Must find
- `unlocked_read` (high): `Count` reads `s.counts` without taking `s.mu`; concurrent read/write of a Go map can panic ("concurrent map read and map write"). Fix: lock (or RWMutex) in `Count`.
- `snapshot_leak` (high/medium): `Snapshot` returns the internal map, exposing it to unsynchronized access by callers. Fix: copy under lock.

## Acceptable extras
- nit: use `defer s.mu.Unlock()`; consider `sync.RWMutex`.

## Must not flag
- `Inc` locking logic (it is correct).

## Hard fail
- Missing both `unlocked_read` and `snapshot_leak` sets `missed_critical`.
