### Summary
The change adds a `RequestStats` class that counts requests per path using a plain `Dictionary<string, int>` with a check-then-act pattern. It is not thread-safe despite clearly being intended for concurrent request tracking, and `Snapshot()` leaks the mutable internal state.

### Findings
- **critical** src/counter.cs:13-21 - Race condition in `Inc` corrupts the dictionary and loses counts
  - Problem: `counts.ContainsKey(path)` followed by `counts[path]++` / `counts[path] = 1` is a non-atomic check-then-act. Concurrent calls can both miss the key and overwrite each other (lost updates), and concurrent writes/reads on a `Dictionary<K,V>` can corrupt internal buckets, throw `NullReferenceException`/`IndexOutOfRangeException`, or hang readers — a real corrupting race for a per-request counter.
  - Fix: Guard all access with a `lock` (or `ReaderWriterLockSlim`), or use `ConcurrentDictionary<string,int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`.
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path))
    {
        counts[path]++;
    }
    else
    {
        counts[path] = 1;
    }
    ```

- **high** src/counter.cs:27-30 - `Snapshot()` returns the live internal dictionary
  - Problem: Returning `counts` directly exposes mutable internal state: callers can mutate counts, and any caller that enumerates the returned dictionary while `Inc` runs will hit `InvalidOperationException` ("collection was modified") or observe torn data. It also defeats any future locking since readers bypass the lock.
  - Fix: Return a copy under the lock, e.g. `lock (gate) return new Dictionary<string,int>(counts);` (or an `IReadOnlyDictionary` snapshot).
  - Code snippet:
    ```csharp
    public Dictionary<string, int> Snapshot()
    {
        return counts;
    }
    ```

- **medium** src/counter.cs:24-25 - `Count` performs an unsynchronized read
  - Problem: Even if `Inc` were fixed, `Count` reads `counts` without synchronization; concurrent `Dictionary` read+write is undefined and can throw or return garbage. It also does two lookups (`ContainsKey` + indexer) — correct but wasteful.
  - Fix: Read under the same lock and use `TryGetValue`: `lock (gate) { return counts.TryGetValue(path, out var c) ? c : 0; }`
  - Code snippet:
    ```csharp
    return counts.ContainsKey(path) ? counts[path] : 0;
    ```

- **low** src/counter.cs:13 - `Inc` does two dictionary lookups per call
  - Problem: The `ContainsKey` + indexer/setter pattern performs two hash lookups; a single `TryGetValue` (under the lock) is simpler and faster.
  - Fix: `if (counts.TryGetValue(path, out var c)) counts[path] = c + 1; else counts[path] = 1;` — or use `CollectionsMarshal.GetValueRefOrAddDefault` for a single lookup.
  - Code snippet:
    ```csharp
    if (counts.ContainsKey(path)) { counts[path]++; }
    ```

### Verdict
request changes
