# Full docusign sandbox API surface

PUG registers 414 eSignature v2.1 operations and 10 Agreement Manager v1 operations from pinned official definitions. This is a provider-shaped sandbox API surface, alongside the curated workflow routes. Registration and mocked gateway tests do not establish that every operation is licensed, consented, or live-tested.

Set `GATEWAY_FULL_DOCUSIGN_API_ENABLED=1` to include them in `/docs` and `/openapi.json`. Every operation requires the existing PUG operator Basic login. Provider credentials remain server-side. Paths:

- `/docusign/esignature` followed by the official eSignature path, including `/v2.1`.
- `/docusign/agreement-manager` followed by the official Agreement Manager path, including `/v1`.

All `accountId` path parameters must equal `DS_WORKFLOW_ACCOUNT_ID`. The fixed eSignature sandbox host is `demo.docusign.net/restapi`; Agreement Manager uses `api-d.docusign.com`. No caller-supplied hosts, redirects, cookies, or authorization headers are forwarded. Provider response bodies are intentionally available to the authenticated operator and may contain personal data, documents, or short-lived access links. Responses use `Cache-Control: no-store`.

## Consent

eSignature uses `signature impersonation`. Agreement Manager requests `signature impersonation adm_store_unified_repo_read adm_store_unified_repo_write models_read document_uploader_read document_uploader_write public_dms_document_read`. A missing grant produces a 503 with code `docusign_consent_required`. Token caches are separated by product and identity. A provider 401 clears the cache for a subsequent request; no write is retried automatically.

## Try the verified reads

Use the configured account ID shown in Swagger. For envelopes supply `from_date` and a small `count`.

- GET `/docusign/esignature/v2.1/accounts/{accountId}/templates`
- GET `/docusign/esignature/v2.1/accounts/{accountId}/envelopes`
- GET `/docusign/esignature/v2.1/accounts/{accountId}/identity_verification`

Read-only provider probes on 2026-09-20 returned 200 for all three. Identity verification returned six enabled workflows. This verifies workflow availability, not a completed identity check. Agreement Manager consent was still missing at that probe.

## Writes and coverage

Swagger exposes POST, PUT, PATCH, and DELETE faithfully. Executing one may send envelopes, create accounts, change configuration, or delete records. No such provider writes were performed while generating or testing this surface. Before proving each write, select a disposable fixture and its cleanup operation. Some operations require special entitlements or administrator roles. Account-less operations remain governed by the impersonated user's provider permissions.

Requests are limited to 35 MiB and responses to 50 MiB. Binary and multipart content pass through unchanged within those limits. Larger files need the provider's chunked-upload flow or a future streaming implementation. Connection failures/timeouts during writes are ambiguous; inspect provider state before retrying. Error responses from the provider retain their status and body. The gateway does not enforce every provider JSON constraint locally; the upstream API validates payloads.

The separate ID Evidence API is not included in the eSignature specification and is not claimed as implemented here.

## Source and regeneration

Pinned files in `gateway/api_specs/` come from:

- https://github.com/docusign/OpenAPI-Specifications/blob/master/esignature.rest.swagger-v2.1.json
- https://github.com/docusign/OpenAPI-Specifications/blob/master/agreementmanager.rest.swagger-1.0.0.json

The eSignature Swagger 2 schemas are translated into the application's OpenAPI schema; all model and reusable-component references are namespaced. Update these files intentionally and rerun `tests/test_full_api.py` before release. Tests assert exact operation counts, reference resolution, authentication across every operation, account restrictions, redirect prevention, encoded identifier rejection, host selection, and method/body/query forwarding without leaking operator credentials.
