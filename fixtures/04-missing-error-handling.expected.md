# Expected: 04-missing-error-handling

## Must find
- `fd_leak` (medium): `writeBackup` never closes `fd` (`fs.closeSync`), leaking the descriptor (also leaks if `writeSync` throws). Fix: try/finally or `fs.writeFileSync`.
- `fetch_no_status` (medium): `fetchRemoteConfig` does not check `res.ok`, so error responses are parsed as config. Fix: check `res.ok` and throw.
- `no_validation` (medium/low): `loadConfig` returns unvalidated `JSON.parse` output typed as `AppConfig`; missing/invalid file or malformed JSON throws with no context, and fields are not validated.

## Acceptable extras
- nit: sync fs calls block the event loop.

## Must not flag
- The `AppConfig` interface itself.

## Hard fail
- None of the above found sets `missed_critical`.
