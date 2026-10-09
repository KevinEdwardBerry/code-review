## Summary
The change adds a request counter that mutates a plain `Dictionary` from parallel tasks, making it thread-unsafe.

## Findings
[High] src/counter.cs:13 — Unsynchronized write to shared dictionary
`            counts[path] = count + 1;`
`Inc` is invoked via `Task.Run` inside `Task.WhenAll` (line 35), so multiple threads concurrently mutate `counts`. `Dictionary<TKey,TValue>` is not thread-safe; concurrent writes can lose increments and corrupt internal state, potentially throwing on later reads/writes. Fix: guard `Inc`/`Count`/`Snapshot` with a lock, or use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd`.

[Medium] src/counter.cs:15 — Second unsynchronized write path
`            counts[path] = 1;`
Same race as above for the first-increment path; must be under the same lock or use `ConcurrentDictionary`.

[Medium] src/counter.cs:20 — Unsynchronized read of shared dictionary
`        return counts.TryGetValue(path, out var count) ? count : 0;`
`Count` can read `counts` while another thread is writing it, which is undefined behavior for `Dictionary` (torn reads/exceptions possible). Fix: take the same lock, or use `ConcurrentDictionary`.

[Medium] src/counter.cs:25 — Snapshot returns the live dictionary and reads it unsynchronized
`        return counts;`
This exposes the mutable internal dictionary to callers and returns it while other threads may be mutating it. Fix: return a copy under the lock (e.g., `new Dictionary<string,int>(counts)`) or use `ConcurrentDictionary` and return a snapshot copy.

## Verdict
Request changes
