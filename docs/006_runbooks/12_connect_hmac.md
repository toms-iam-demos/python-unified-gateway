# Connect HMAC verification

PUG verifies the original request bytes before parsing, persistence or broadcast,
implementing the ingress boundary in ADR-0010. The SHA-256 HMAC uses the configured
key as UTF-8 text and compares decoded base64 signatures in constant time.

The choice to reject failed verification outright, rather than persist it flagged, is
recorded separately in [ADR-0012](../007_adr/0012-connect-webhook-verification-failures-rejected.md) —
including the tradeoff this creates against ADR-0010's own auditability invariant, since a
rejected bodies are absent from the ledger. Logs retain rejection reasons; when enabled,
the explorer also shows volatile request-status and failed-span metadata.

## Configuration

Set `DOCUSIGN_CONNECT_HMAC_SECRET` to the matching docusign Connect key in the
receiver host's private environment configuration. Do not commit the key, paste
it into chat, or include it in command-line arguments. The local Compose service
`ds-gw` loads `.env`; verify the deployed service's configuration separately.

No key or a blank key returns HTTP 503. A missing, malformed or incorrect
signature returns HTTP 401. Rejected requests are neither persisted nor broadcast.
Logs record only a rejection reason (WARNING for invalid signatures, ERROR for missing
configuration). Valid requests retain existing persistence
behavior, with `verify_status=verified` and `verify_reason=hmac-sha256`.
Verification does not guarantee successful persistence; inspect `persisted` in
the response. Existing fail-open persistence behavior is outside this change.

The verifier checks every numbered `X-DocuSign-Signature-N` header. During rotation,
keep both keys active in docusign, switch the receiver to the new key and verify
delivery before retiring the old provider key. One receiver key is configured.

## Local verification

Run from the repository root with a Python 3.12 development environment:

```sh
.venv/bin/python -m pip install -r requirements-test.txt
.venv/bin/python -m unittest discover -s tests -p 'test_connect_hmac.py' -v
```

Tests use synthetic bytes and a test key. Most persistence calls and all broadcasts
are mocked; dedicated tests use temporary SQLite databases. No production database,
provider account or remote webhook is touched. They cover acceptance,
missing/wrong/malformed signatures, exact-body integrity, missing configuration,
rotation, verification metadata, rejection-log redaction, duplicate legacy rows and
the existing fail-open persistence policy.

## Existing ledger limits

Duplicate deliveries do not add rows or upgrade historical verification metadata.
The helper may report a generated ID even when its insert was ignored. Check stored
rows directly; a trace ID or HTTP 200 does not establish successful new persistence.

## Rollout

Follow the [Hetzner release procedure](11_hetzner_api_ingress.md) using the actual
server checkout and Compose overrides. `/health` does not check HMAC configuration.

Provision the secret before deploying the verifier. Rebuild and recreate the
container to load both code and changed Compose environment configuration; a
plain restart does not reload Compose environment values. The local command is:

```sh
docker compose up -d --build --force-recreate ds-gw
```

Trigger a selected Connect event using a demo envelope. Confirm successful
delivery and the ledger's verification metadata. Exercise negative cases on an
isolated receiver before rollout. Never treat HTTP 200 alone as verification proof.
Do not roll back to an unverified receiver as a workaround for a missing key.

Reference: [docusign signature validation](https://developers.docusign.com/platform/webhooks/connect/validate/).
