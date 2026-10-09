## Summary
The change adds a request counter that is shared across concurrent tasks without synchronization, producing race conditions and exposing mutable internal state.

## Findings

[High] src/counter.cs:13 — Unsynchronized write to shared `Dictionary` under concurrent `Inc` calls
> `counts[path] = count + 1;`
`HandleAllAsync` invokes `stats.Inc` concurrently via `Task.Run`/`Task.WhenAll`. `Dictionary` is not thread-safe; concurrent check-then-set on lines 12–15 loses increments and can corrupt internal state, permanently under-counting requests.
Fix: guard all access with a `lock`, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd`.

[Medium] src/counter.cs:20 — Unsynchronized read of shared `Dictionary`
> `return counts.TryGetValue(path, out var count) ? count : 0;`
`Count` reads the dictionary while other tasks may be writing it via `Inc`; concurrent read-during-write on `Dictionary` is not guaranteed safe and can return torn or stale results.
Fix: protect reads with the same lock used for writes, or use `ConcurrentDictionary` (`TryGetValue` is then safe).

[Medium] src/counter.cs:25 — `Snapshot` returns the live mutable dictionary
> `return counts;`
Callers receive the internal dictionary: they can mutate it unsafely and enumerate it while writes occur, causing `InvalidOperationException` or corrupted counts.
Fix: return a copy under the lock (e.g., `new Dictionary<string,int>(counts)` inside `lock`, or `ToDictionary` on a `ConcurrentDictionary`).

## Verdict
Request changes
