# Expected: 04-missing-error-handling

## Must find
- `fd_leak` (medium): `writeBackup` opens `fd` at `src/config.ts:15` (`const fd = fs.openSync(path, "w")`) and never closes it (`fs.closeSync`), leaking the descriptor (also leaks if `writeSync` throws at `src/config.ts:16`). Fix: try/finally with `fs.closeSync(fd)`, or `fs.writeFileSync`.
- `fetch_no_status` (medium): `fetchRemoteConfig` does not check `res.ok` before `return res.json()` at `src/config.ts:21`, so error responses are parsed as config. Fix: check `res.ok` and throw.
- `no_validation` (low): `loadConfig` returns unvalidated `JSON.parse` output typed as `AppConfig` (`src/config.ts:10-11`); fields are not validated and a missing file or malformed JSON throws with no context. Fix: validate the parsed fields and wrap errors with the file path.

## Acceptable extras
- nit: sync fs calls block the event loop.

## Must not flag
- The `AppConfig` interface itself.

## Hard fail
- Missing both `fd_leak` and `fetch_no_status` sets `missed_critical`.
