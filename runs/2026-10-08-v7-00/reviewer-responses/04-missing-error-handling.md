## Code Review: `src/config.ts` config helpers

### Issues

**1. `writeBackup` leaks the file descriptor (high severity)**
```ts
const fd = fs.openSync(path, "w");
fs.writeSync(fd, data);
```
`fd` is never closed with `fs.closeSync(fd)`. Repeated calls exhaust the process's fd limit. Also, `fs.writeSync` on a string may perform a partial write — there's no loop or byte-count check. This whole function is better expressed as `fs.writeFileSync(path, data)`, which is atomic-equivalent, closes properly, and handles partial writes. If `openSync` is intentionally used (e.g., to control flags/mode), wrap it:
```ts
const fd = fs.openSync(path, "w");
try {
  fs.writeSync(fd, data, null, "utf8");
} finally {
  fs.closeSync(fd);
}
```

**2. `loadConfig` performs no validation of `cfg` (medium)**
`JSON.parse` returns `any` and it's cast implicitly to `AppConfig`. A malformed file (missing `port`, `port` as a string, etc.) propagates silently and fails far from the cause. Validate the shape before returning:
```ts
const cfg = JSON.parse(raw);
if (typeof cfg.port !== "number" || typeof cfg.dbUrl !== "string") {
  throw new Error(`Invalid config at ${path}`);
}
```
Or use a schema validator (zod, ajv). Also consider whether `JSON.parse`/`readFileSync` errors should be wrapped with the path for context — a bare `ENOENT` stack doesn't tell the caller which file failed.

**3. `fetchRemoteConfig` has the same validation gap, plus no HTTP error handling (medium)**
```ts
const res = await fetch(url);
return res.json();
```
- `res.ok` is never checked — a 404/500 body will be parsed as config, likely producing a silently wrong `AppConfig` or a confusing JSON error. Should be:
```ts
if (!res.ok) throw new Error(`fetch ${url} failed: ${res.status}`);
```
- No timeout/AbortSignal — a hung remote endpoint leaves this awaiting forever. Consider `AbortSignal.timeout(...)`.
- `res.json()` returns `any`; same runtime-validation concern as #2.

**4. Inconsistent sync/async API surface (minor)**
`loadConfig` is synchronous but `fetchRemoteConfig` is async, and the file writes are sync. Fine for startup code, but if `writeBackup` is called on a hot path, blocking I/O + the fd leak compounds. Worth documenting intent.

**5. Security note (minor)**
`writeBackup` writes with default permissions and `path`/`url` are unchecked. If `path` can come from user input, this is a path-traversal/write-anywhere risk; if `url` is user-controlled, `fetchRemoteConfig` is an SSRF vector. Likely internal-only, but flag it if either is reachable from request data.

### Recommendations (priority order)
1. Replace `writeBackup` with `fs.writeFileSync`, or close the fd in a `finally`.
2. Check `res.ok` and add a timeout in `fetchRemoteConfig`.
3. Validate the parsed shape in both loaders before returning `AppConfig` — ideally share one `validateConfig(raw: unknown): AppConfig` helper so the two paths can't drift.

### What looks fine
- Typing the interface and returning `Promise<AppConfig>` is reasonable.
- `readFileSync`/`openSync` at startup is acceptable for a config module.
