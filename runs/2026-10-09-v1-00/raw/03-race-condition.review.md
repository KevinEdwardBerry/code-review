# Code Review: `src/counter.cs`

## Summary
The code compiles and works correctly in single-threaded use, but `RequestHandler.HandleAllAsync` explicitly invokes `stats.Inc` from multiple threads via `Task.Run`/`Task.WhenAll`. That makes the underlying `Dictionary` race-prone — this is the central defect.

## Findings

### 🔴 Critical — `Dictionary<string,int>` is not thread-safe (lines 7–16, 32–36)
`Inc` performs a read-modify-write (`TryGetValue` then indexed set) and `HandleAllAsync` runs it concurrently. Consequences:
- **Lost updates**: two threads can both read count `N` and both write `N+1`.
- **Corruption**: concurrent writes during a dictionary resize can corrupt internal buckets, leading to infinite loops or `IndexOutOfRangeException` on later reads — a well-documented failure mode for `Dictionary`.
- Even `Count`/`Snapshot` reading while another thread writes is unsafe.

**Fix options:**
- Use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)` or `Interlocked` on the value.
- Or guard all access with a `lock`.
- Better still: since `Task.Run` parallelism here buys nothing for a cheap increment, just iterate sequentially — the simplest correct code.

### 🟠 Major — `Snapshot()` returns the live mutable dictionary (lines 25–28)
Callers get a direct reference to internal state: they can mutate it, and their reads race with concurrent `Inc` calls (enumerating a `Dictionary` during mutation throws `InvalidOperationException`). Return a copy:
```csharp
public Dictionary<string,int> Snapshot()
{
    lock (gate) return new Dictionary<string,int>(counts);
}
```
(or `ToDictionary`/`IReadOnlyDictionary`).

### 🟡 Minor — Parallelism overhead
`Task.Run` per path for an O(1) increment will usually be *slower* than a sequential loop due to thread-pool scheduling. If `paths` is large, consider `Parallel.ForEach` with partitioned local counters merged at the end.

### 🟡 Minor — `Inc` can be simplified
Single-indexer form is equivalent and avoids a double lookup... actually, the current two-step form is fine, but `counts[path] = counts.GetValueOrDefault(path) + 1;` is cleaner. Style only.

### ℹ️ Note — `counts` isn't marked `readonly`
`private readonly Dictionary<...> counts` would prevent accidental reassignment.

## Recommendation
Request changes. At minimum: replace the dictionary with `ConcurrentDictionary` + `AddOrUpdate`, make `Snapshot` return a copy, and seriously consider dropping `Task.Run` entirely unless there's real CPU-bound work to parallelize.
