## Code Review: `src/counter.cs`

### 🔴 Correctness / API design issues

1. **`Snapshot()` returns the internal mutable dictionary** (line ~26)
   - Callers can mutate, clear, or corrupt internal state: `stats.Snapshot()["/admin"] = 999;`
   - Fix: return a copy (`new Dictionary<string,int>(counts)`) or expose `IReadOnlyDictionary<string,int>`.

2. **Not thread-safe**
   - A request-stats counter is almost certainly incremented from concurrent request threads. `Dictionary` is not safe for concurrent read/write — `Inc` can lose updates or corrupt internal buckets.
   - Fix: use `ConcurrentDictionary<string,int>` with `AddOrUpdate`/`GetOrAdd`, or guard all access with a `lock`.

3. **`Inc(null)` throws `ArgumentNullException`**
   - `Dictionary` does not accept null keys. Either validate (`ArgumentNullException.ThrowIfNull(path)`) explicitly or document the contract.

### 🟡 Minor / style

4. **Double lookup** — `ContainsKey` + indexer performs two hash lookups. Prefer `TryGetValue`:
   ```csharp
   counts.TryGetValue(path, out int n);
   counts[path] = n + 1;
   ```
   (Or `CollectionsMarshal.GetValueRefOrAddDefault` for a single lookup.)

5. **File/class name mismatch** — file is `counter.cs` but declares `public class RequestStats`. Convention is `RequestStats.cs`; some tooling/builds expect this.

6. **No namespace** — the class lands in the global namespace; wrap it in the project's namespace.

7. **Field could be `readonly`** — `counts` is never reassigned: `private readonly Dictionary<string,int> counts = new();`

8. **`Count` duplicates lookup logic** — could be `counts.TryGetValue(path, out var n) ? n : 0`.

### Suggested rewrite

```csharp
using System.Collections.Concurrent;
using System.Collections.Generic;

public sealed class RequestStats
{
    private readonly ConcurrentDictionary<string, int> counts = new();

    public void Inc(string path)
    {
        ArgumentNullException.ThrowIfNull(path);
        counts.AddOrUpdate(path, 1, (_, n) => n + 1);
    }

    public int Count(string path) => counts.TryGetValue(path, out var n) ? n : 0;

    public IReadOnlyDictionary<string, int> Snapshot() =>
        new Dictionary<string, int>(counts);
}
```

**Verdict:** Works for single-threaded use, but the mutable `Snapshot()` leak and lack of thread safety should be fixed before merge, given this is clearly intended to count HTTP requests.
