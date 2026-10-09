# Code Review: `src/config.ts`

Thanks for the addition — a few issues here that I'd want addressed before merge, ranging from correctness bugs to missing validation.

## 🔴 Bugs / Correctness

**1. `writeBackup` leaks the file descriptor**
```ts
const fd = fs.openSync(path, "w")
fs.writeSync(fd, data)
```
The file descriptor is never closed via `fs.closeSync(fd)`. Under repeated calls this leaks FDs and on some platforms can produce incomplete writes or `EMFILE` errors. If you want the simpler API, `fs.writeFileSync(path, data)` does the same thing in one call without the leak. If you keep `openSync`, wrap in `try/finally` with `fs.closeSync(fd)`.

**2. `loadConfig` returns untyped, unvalidated data**
```ts
const cfg = JSON.parse(raw)
return cfg
```
`JSON.parse` returns `any`, so this silently satisfies the `AppConfig` return type while providing no guarantee the file actually contains `port`/`dbUrl` — a missing or mistyped field becomes a runtime failure far downstream. Either validate explicitly, or use a schema validator (zod, valibot, etc.). If you don't want a dependency, a manual check like `typeof cfg.port === "number"` before returning goes a long way.

**3. `fetchRemoteConfig` ignores HTTP errors and lacks validation**
```ts
const res = await fetch(url)
return res.json()
```
- No check of `res.ok` — a 404/500 HTML error page will be passed to `res.json()` and produce a confusing `SyntaxError` instead of a meaningful message.
- `res.json()` also returns `any`, so same unvalidated-shape problem as `loadConfig`.
- Consider a timeout (`AbortSignal.timeout(...)`) — a hung remote will otherwise block indefinitely.
- `res.json()` returns `Promise<any>` and you're returning it directly into `Promise<AppConfig>`; fine, but see the type-safety note below.

## 🟡 Minor / Consistency

**4. Sync vs async mixing**
`loadConfig` and `writeBackup` are synchronous while `fetchRemoteConfig` is async. If `loadConfig` is called at startup that's defensible, but `writeBackup` doing synchronous I/O on a hot path will block the event loop. Worth a comment or making it async (`fs.promises.writeFile`).

**5. Style inconsistency**
The file mixes `;` and no-`;` line endings (`port: number;` vs `import ... "fs"`). Pick whichever matches the project convention.

**6. Unhandled errors**
`JSON.parse` on malformed config throws a bare `SyntaxError`; consider wrapping with context like `Failed to load config at ${path}: ...` — debugging "Unexpected token" with no filename is painful.

## Suggested shape

```ts
export function loadConfig(path: string): AppConfig {
  const raw = fs.readFileSync(path, "utf8")
  const cfg: unknown = JSON.parse(raw)
  if (typeof cfg !== "object" || cfg === null
      || typeof (cfg as AppConfig).port !== "number"
      || typeof (cfg as AppConfig).dbUrl !== "string") {
    throw new Error(`Invalid config at ${path}`)
  }
  return cfg as AppConfig
}
```

**Verdict:** Request changes — the FD leak and the two unchecked `any` → `AppConfig` casts are the must-fixes.
