## Summary
The new `RequestStats` counter is used from multiple threads by `HandleAllAsync` but wraps a plain `Dictionary` with no synchronization, so all reads and writes are racy.

## Findings
[High] src/counter.cs:12 — unsynchronized read/write of shared `counts` during concurrent `Inc`
`        if (counts.TryGetValue(path, out var count))`
`Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))))` invokes `Inc` on multiple threads over a non-thread-safe `Dictionary`. Races cause lost increments and can corrupt the dictionary's internal buckets (leading to exceptions or hangs). Fix: use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or guard all accesses with a `lock`.

[High] src/counter.cs:20 — unsynchronized read of `counts` in `Count`
`        return counts.TryGetValue(path, out var count) ? count : 0;`
`Total` can be called while `HandleAllAsync` is mutating the dictionary; a `TryGetValue` concurrent with a write/resize is undefined and may throw or return stale/corrupted results. Fix: same as above (`ConcurrentDictionary` or lock on every access).

[Medium] src/counter.cs:25 — `Snapshot` returns the live mutable dictionary
`        return counts;`
Callers receive the internal `Dictionary`, so they can observe or mutate it concurrently with `Inc`, reintroducing races and breaking encapsulation. Fix: return a copy (`new Dictionary<string,int>(counts)` under the lock / `ConcurrentDictionary.ToArray()`-based snapshot).

## Verdict
Request changes
