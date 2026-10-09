## Summary
Adds config loading, a backup writer, and a remote config fetcher; low overall risk but the backup writer leaks its file descriptor.

## Findings

[Medium] src/config.ts:15 — File descriptor opened but never closed
> `const fd = fs.openSync(path, "w")`

`fs.writeSync(fd, data)` at src/config.ts:16 uses `fd`, but no `fs.closeSync(fd)` ever runs — neither on success nor if `writeSync` throws. Each call leaks a file descriptor, which can exhaust the process fd limit under repeated use. Fix: wrap in try/finally calling `fs.closeSync(fd)`, or use `fs.writeFileSync(path, data)` which handles this internally.

## Verdict
Request changes