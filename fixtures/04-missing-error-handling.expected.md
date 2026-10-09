# Expected: 04-missing-error-handling

## Must find
- `unchecked_http_status` (medium): `deliverWebhook` awaits `fetch` but ignores the returned `Response` (`src/webhook.ts:2-6`). Fetch resolves normally for HTTP 4xx/5xx responses, so the function reports success even when the webhook endpoint rejects the request. Fix: check `response.ok` and throw an error containing the status.

## Must not flag
- Missing handling for network failures: `fetch` rejects for transport errors, and this function correctly lets that rejection propagate to its caller.
