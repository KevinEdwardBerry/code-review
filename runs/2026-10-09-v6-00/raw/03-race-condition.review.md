## Summary
A new request-statistics counter that performs unsynchronized concurrent access to a shared `Dictionary`, making it unsafe under the demonstrated parallel workload.

## Findings
- **[High] src/counter.cs:35 — Concurrent unsynchronized mutation of shared `Dictionary`**
  `await Task.WhenAll(paths.Select(p => Task.Run(() => stats.Inc(p))));`
  `HandleAllAsync` invokes `stats.Inc` on multiple threads simultaneously, but `counts` is a plain `Dictionary<string,int>` mutated without synchronization. `Dictionary` is not thread-safe for concurrent writes; this can corrupt internal state, lose increments, or throw. Fix: use `ConcurrentDictionary<string,int>` with `AddOrUpdate`, or guard `Inc` with a `lock`.

- **[Medium] src/counter.cs:20 — Unsynchronized read of `counts` during concurrent writes**
  `return counts.TryGetValue(path, out var count) ? count : 0;`
  `Total` calls `Count`, which reads the dictionary with no synchronization; reading a `Dictionary` while another thread writes is undefined and may throw or return stale/corrupt results. Fix: same as above — `ConcurrentDictionary` or a shared lock.

- **[Medium] src/counter.cs:25 — `Snapshot` exposes the live mutable dictionary**
  `return counts;`
  Returns the internal dictionary by reference, so callers can mutate internal state and can iterate it while `Inc` writes, which can throw `InvalidOperationException`. Fix: return a copy (e.g., `new Dictionary<string,int>(counts)` under the lock) or an immutable/read-only snapshot.

## Verdict
Request changes