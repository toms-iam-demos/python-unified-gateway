# Full docusign sandbox API surface

PUG registers 414 eSignature v2.1 operations and 10 Agreement Manager v1 operations from pinned official definitions. This is a provider-shaped sandbox API surface, alongside the curated workflow routes. Registration and mocked gateway tests do not establish that every operation is licensed, consented, or live-tested.

**Execution policy:** only six explicitly reviewed GET operations can execute. All 418 other operations return `403 operation_locked` before accessing credentials or contacting docusign, including every DELETE/POST/PUT/PATCH and unreviewed GET. No configuration switch, query argument, or confirmation header can unlock them. Enabling a future operation requires a reviewed code change and deployment.

Set `GATEWAY_FULL_DOCUSIGN_API_ENABLED=1` to include them in `/docs` and `/openapi.json`. Every operation requires the existing PUG operator Basic login. Provider credentials remain server-side. Paths:

- `/docusign/esignature` followed by the official eSignature path, including `/v2.1`.
- `/docusign/agreement-manager` followed by the official Agreement Manager path, including `/v1`.

All `accountId` path parameters must equal `DS_WORKFLOW_ACCOUNT_ID`. The fixed eSignature sandbox host is `demo.docusign.net/restapi`; Agreement Manager uses `api-d.docusign.com`. No caller-supplied hosts, redirects, cookies, or authorization headers are forwarded. Provider response bodies are intentionally available to the authenticated operator and may contain personal data, documents, or short-lived access links. Responses use `Cache-Control: no-store`.

## Consent

eSignature uses `signature impersonation`. Agreement Manager requests `signature impersonation adm_store_unified_repo_read`. A missing grant produces a 503 with code `docusign_consent_required`. Token caches are separated by product and identity. A provider 401 clears the cache for a subsequent request; no write is retried automatically.

## Try the verified reads

Use the configured account ID shown in Swagger. For envelopes supply `from_date` and a small `count`.

- GET `/docusign/esignature/v2.1/accounts/{accountId}/templates`
- GET `/docusign/esignature/v2.1/accounts/{accountId}/envelopes`
- GET `/docusign/esignature/v2.1/accounts/{accountId}/identity_verification`

Read-only provider probes on 2026-09-20 returned 200 for all three. Identity verification returned six enabled workflows. This verifies workflow availability, not a completed identity check. Agreement Manager consent was still missing at that probe.

## Writes and coverage

Swagger retains every operation for reference, but marks disabled operations `[LOCKED]`. Write Execute buttons are removed, and credentials are not persisted by Swagger. Server enforcement also covers direct HTTP callers and authenticated operators; hiding buttons is not the security boundary.

Enabled operations: eSignature templates list, envelopes list, identity-verification workflow list; Agreement Manager agreements list/detail, and agreement types list. Agreement Manager is still subject to consent and entitlement. All other reads are locked, including upload-job status: its response can contain presigned upload URLs that confer write access outside PUG.

Method-override headers, unrecognized query parameters, encoded path escape characters, and GET bodies are rejected. Responses are bounded to 50 MiB. Authenticated read responses can still contain sensitive agreement metadata; operator credentials must remain private. The existing JWT diagnostic now also checks operator login inside the application. Signed webhook ingestion remains a separate route protected by HMAC; the read-only outbound API policy does not disable incoming webhooks.

The eSignature `signature` scope is broad; its read-only restriction is enforced by PUG code, not a provider read-only scope. Agreement Manager tokens request only the required agreement-read scope alongside JWT impersonation/signature. The optional forward-compatibility models_read scope is deliberately omitted: the three enabled endpoints do not require it. Read-only probes confirmed agreement list (one sample), agreement types (63 types), and one existing agreement detail all return 200 with this minimum scope set. Broader consent, if granted elsewhere, is not requested by this adapter. The code does not revoke consent already recorded at docusign. No live provider writes are used to verify this policy; exhaustive local tests prevent token/config/network access for every locked operation, and deployed negative probes verify the guard directly.

The separate ID Evidence API is not included in the eSignature specification and is not claimed as implemented here.

## Source and regeneration

Pinned files in `gateway/api_specs/` come from:

- https://github.com/docusign/OpenAPI-Specifications/blob/master/esignature.rest.swagger-v2.1.json
- https://github.com/docusign/OpenAPI-Specifications/blob/master/agreementmanager.rest.swagger-1.0.0.json

The eSignature Swagger 2 schemas are translated into the application's OpenAPI schema; all model and reusable-component references are namespaced. Update these files intentionally and rerun `tests/test_full_api.py` before release. Tests assert exact operation counts, reference resolution, authentication across every operation, account restrictions, redirect prevention, encoded identifier rejection, host selection, and method/body/query forwarding without leaking operator credentials.
