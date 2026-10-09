## Summary
The new `RequestStats` uses a plain `Dictionary` mutated from `Task.Run` calls in `HandleAllAsync`, creating unsynchronized read/write paths and exposing the live dictionary via `Snapshot`.

## Findings
[High] src/counter.cs:12 — Unsynchronized check-then-act increment on shared `Dictionary`
> `        if (counts.TryGetValue(path, out var count))`
`Task.Run(() => stats.Inc(p))` at line 35 invokes `Inc` concurrently; the non-atomic TryGetValue-then-set can lose increments and concurrent dictionary writes can corrupt internal state (exceptions / torn data). Fix: guard with a `lock`, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd` + `Increment`.

[Medium] src/counter.cs:20 — Unsynchronized read of `counts` while writers mutate it
> `        return counts.TryGetValue(path, out var count) ? count : 0;`
`Count` may run concurrently with `Inc` writes; `Dictionary` reads during mutation can throw or return stale/torn results. Fix: take the same lock (or use `ConcurrentDictionary`).

[Medium] src/counter.cs:25 — `Snapshot` returns the live mutable dictionary and iterates without synchronization
> `        return counts;`
Callers get direct mutable access to shared state and any enumeration races with concurrent `Inc` writes. Fix: return a copy under the lock (e.g., `new Dictionary<string,int>(counts)` inside the lock, or `ToDictionary` on a `ConcurrentDictionary`).

## Verdict
Request changes
