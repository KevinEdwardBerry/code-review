## Summary
Adds a webhook delivery helper that POSTs a payload via fetch; low risk but it silently ignores non-2xx responses.

## Findings

[Medium] src/webhook.ts:2 — HTTP error responses are not checked, so failed deliveries are reported as success
```
  await fetch(url, {
```
`fetch` only rejects on network failures; a 4xx/5xx response resolves normally, so the caller cannot detect a failed webhook delivery. Fix: capture the response and throw or return a result when `!res.ok` (e.g., `const res = await fetch(...); if (!res.ok) throw new Error(\`Webhook failed: ${res.status}\`)`).

## Verdict
Request changes
