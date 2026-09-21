# Operator audit and identity migration

## Current policy

The provider API remains limited to six reviewed reads. The other 418 operations are locked in code. Audit access adds one local read route, not another provider capability. Writes require reviewed implementation and deployment, not a runtime flag or confirmation header.

Enable `PUG_AUDIT_ENABLED=1` and set `PUG_AUDIT_DB_PATH=/app/data/security-audit.sqlite3`. The file is separate from the webhook ledger and lives on the persistent data mount, with mode 0600 on creation. SQLite uses WAL and synchronous FULL. Its main database is capped at 64 MiB; journal/checkpoint overhead is additional. Records are not automatically pruned. Arrange archive/retention and capacity monitoring before larger use; the current release has no off-host archival or tamper-resistant storage.

Every request reaching the application's `/docusign` namespace records a received event. Before response headers are transmitted, it records response_ready with the verified operator username, matched route template, method, status, a server-created request ID and selected valid UUID resource references. Passwords, tokens, unverified usernames, raw paths, query values, headers and agreement contents are excluded. Shared credentials identify the credential rather than the person. response_ready is not proof that the client received the entire response. An unmatched received event can indicate interruption, crash or later logging failure.

If the initial audit write fails, operator execution stops with 503 before dispatch. If response_ready cannot be recorded, the application withholds the response and returns 503; a provider read may already have run. `/health` and signed webhook ingestion do not depend on this operator-audit database. Gateway error logs report only an audit request ID. Docker diagnostic logs are configured separately with rotation; the audit database is not rotated or deleted by that setting.

GET `/docusign/security/audit?limit=25` requires the operator login and returns up to 100 recent events, with no-store headers. Reading the audit is itself audited. Requests rejected at Traefik never reach this application log: edge authentication logging remains a separate operational requirement. This is not a complete user/session history or a compliance certification.

## Individual login and MFA: proposed next stage, not enabled

For a small POC without an enterprise directory, Cloudflare Access can integrate personal Google accounts without Workspace. Enable Google 2-Step Verification and a passkey/security key for the chosen personal identity. Use an explicit Access MFA requirement; do not assume that merely selecting Google login proves MFA to PUG.

Confirm the Cloudflare account/domain setup before touching DNS or login policies. Then:

1. Configure a named-user allowlist and MFA on operator pages/APIs.
2. Validate Access token signature, issuer, audience and expiry at the gateway or a trusted validating proxy; do not trust an arbitrary identity header.
3. Prevent direct-origin bypass. Keep a tested recovery path during the transition, then remove Basic auth as an alternate way around MFA.
4. Keep signed webhook ingestion separate from browser login. Machine clients need their own narrowly authorized identities rather than a shared human account.
5. Test allowed user, denied user, missing MFA, expired token, forged headers, origin bypass and session expiry before cutover.

MFA enrollment and account setup require the owner's interaction. None of this identity migration is active in the audit release.

## Security review at each change

Record data accessed, authenticated identity, operation permission, side effects, secret handling, resource limits, failure behavior, tests, and rollback. Keep provider scope and route permissions minimal. Preserve the read-only default while building identity, audit capacity monitoring, external archival and rate limiting. Do not represent those planned controls as already implemented.

Sources: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html ; https://developers.cloudflare.com/cloudflare-one/integrations/identity-providers/google/ ; https://developers.cloudflare.com/cloudflare-one/access-controls/access-settings/independent-mfa/
