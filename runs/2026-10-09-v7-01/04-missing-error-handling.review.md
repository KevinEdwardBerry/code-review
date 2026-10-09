## Summary
Adds a small helper that POSTs a payload to a URL; the only demonstrated defect is that it silently ignores HTTP-level delivery failures.

## Findings
[Medium] src/webhook.ts:2 — HTTP error responses are silently treated as successful delivery
`  await fetch(url, {`
`fetch` resolves without throwing on non-2xx responses (4xx/5xx), so `deliverWebhook` reports success to callers even when the webhook was rejected, making failures invisible. Check `res.ok`/`res.status` and throw or return an error so callers can handle failed deliveries.

## Verdict
Approve with nits
