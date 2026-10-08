# Code Review: `src/counter.cs`

## Summary

Adds a `RequestStats` class that tracks per-path request counts using a `Dictionary<string, int>`, with `Inc`, `Count`, and `Snapshot` methods. The logic is correct for single-threaded use, but there are several issues worth flagging — one significant (mutable state leak / thread safety) and several minor.

## Issues

### 1. `Snapshot()` exposes internal mutable state (High)

```csharp
public Dictionary<string, int> Snapshot()
{
    return counts;
}
```

This returns a direct reference to the internal dictionary. Callers can:
- Mutate the counts (e.g., `stats.Snapshot()["/foo"] = 0`), corrupting internal state.
- Hold a live view that changes under them — typically not what "snapshot" implies (a snapshot should be a point-in-time copy).
- Enumerate while another part of the code calls `Inc`, causing `InvalidOperationException`.

**Recommendation:** Return a copy or a read-only view:

```csharp
public Dictionary<string, int> Snapshot() => new Dictionary<string, int>(counts);
// or
public IReadOnlyDictionary<string, int> Snapshot() => new Dictionary<string, int>(counts);
```

Also consider whether returning `IReadOnlyDictionary<string, int>` better communicates intent.

### 2. Not thread-safe (High, if used in a request-handling context)

The class name (`RequestStats`) and comment ("records one request") strongly suggest this will be called from concurrent request handlers. `Dictionary<K,V>` is not thread-safe: concurrent `Inc` calls can lose updates (read-modify-write race on `counts[path]++`), and mixed reads/writes can corrupt internal structure or throw.

**Recommendations:**
- Use `ConcurrentDictionary<string, int>` with `counts.AddOrUpdate(path, 1, (_, c) => c + 1)`, or
- Guard all access with a `lock`, or
- Document explicitly that the class is not thread-safe and callers must synchronize.

Even with `ConcurrentDictionary`, `Snapshot()` should copy (e.g., `new Dictionary<string,int>(counts)` — a snapshot of a `ConcurrentDictionary` enumeration is safe).

### 3. File/class naming conventions (Medium)

- File is named `counter.cs` but declares `RequestStats`. C# convention is one file per public class, named after the class (`RequestStats.cs`).
- Missing a `namespace` declaration. Putting types in the global namespace in a shared source file is a smell and can cause collisions.
- Path/file casing: `.cs` lowercase is fine, but ensure it fits repo conventions.

### 4. Performance micro-issues (Low)

```csharp
if (counts.ContainsKey(path))
    counts[path]++;
else
    counts[path] = 1;
```

- Double lookup: `ContainsKey` + indexer. Could use `TryGetValue` to do one lookup:
  ```csharp
  counts.TryGetValue(path, out var c);
  counts[path] = c + 1;
  ```
- Same for `Count`: `counts.TryGetValue(path, out var c) ? c : 0` avoids two hash lookups. (On modern .NET you can also use `CollectionsMarshal.GetValueRefOrAddDefault` for a single lookup.)

### 5. Null/empty path handling (Low)

- `Inc(null)` throws `ArgumentNullException` from the dictionary — acceptable, but undocumented. `Count(null)` also throws; an alternative is to return 0 for null. Decide and document, or add explicit `ArgumentNullException.ThrowIfNull(path)`.
- No validation of empty string — probably fine, but worth a thought.

### 6. `counts` field could be `readonly` (Low)

```csharp
private readonly Dictionary<string, int> counts = new();
```
Target-typed `new()` and `readonly` make intent clearer and prevent accidental reassignment.

### 7. Comments (Nit)

`// Inc records one request...` — C# convention is XML doc comments (`/// <summary>...`) on public APIs so IntelliSense/tooling picks them up.

## Suggested revised version

```csharp
using System.Collections.Concurrent;
using System.Collections.Generic;

namespace MyApp.Stats
{
    /// <summary>Tracks request counts per path. Thread-safe.</summary>
    public class RequestStats
    {
        private readonly ConcurrentDictionary<string, int> counts = new();

        /// <summary>Records one request for the given path.</summary>
        public void Inc(string path) =>
            counts.AddOrUpdate(path, 1, (_, c) => c + 1);

        /// <summary>Returns the number of requests recorded for the given path.</summary>
        public int Count(string path) =>
            counts.TryGetValue(path, out var c) ? c : 0;

        /// <summary>Returns a point-in-time copy of the current counts.</summary>
        public IReadOnlyDictionary<string, int> Snapshot() =>
            new Dictionary<string, int>(counts);
    }
}
```

## Verdict

Logic is correct for a single-threaded scenario, but I’d request changes before merge: fix the mutable-state leak in `Snapshot()`, address (or document) thread safety given the apparent request-tracking use case, add a namespace, and rename the file to match the class.
