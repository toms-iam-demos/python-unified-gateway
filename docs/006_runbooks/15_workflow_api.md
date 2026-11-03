# Workflow Builder read-only API

This increment adds four operator-authenticated sandbox reads to PUG. It does not
start, complete, cancel, or purge workflows. Provider responses are projected;
launch URLs, default input values, participant maps and submitted input values
are not returned. Names and workflow identifiers are still operator information.

## Walkthrough at api.tifirmo.io

Open https://api.tifirmo.io/docs and find **docusign workflows (read-only)**.
Choose **Authorize**, enter the existing PUG operator username/password, then
use **Try it out → Execute** on the following operations in order. Do not enter
a docusign access token or the signed public launch URL in Swagger.

| Step | Route | Proof and next action |
| --- | --- | --- |
| 1 | `GET /docusign/workflows` | Lists the workflows visible to the configured account/user. Find the hiring-freeze workflow and copy its `id`. A 200 with no rows proves the read succeeded, not that this workflow was found. |
| 2 | `GET /docusign/workflows/{workflow_id}/requirements` | Shows trigger input names, types and HTTP method. This is the API trigger contract, not necessarily the entire interactive form. It does not trigger anything. |
| 3 | `GET /docusign/workflows/{workflow_id}/instances` | Lists the provider's returned runs, states and timestamps. Copy a real run `id`. Empty results are valid; do not invent a run or start one for this test. |
| 4 | `GET /docusign/workflows/{workflow_id}/instances/{instance_id}` | Shows that run's status, step progress and input names. Compare ID/state with step 3. Submitted values remain private. |

The supplied launch link contains workflow definition ID
`a9636563-65dd-499c-98c3-9db6b33e6bd5`; confirm it against step 1 rather than
assuming all public launch identifiers equal API discovery identifiers.
Do not assume the runtime redirect's `workflowId` parameter is an API instance ID.

A successful integration report records release SHA, date, HTTP outcome and
resource IDs, not access tokens, signed URLs, field values or full provider bodies.
Record each route separately as passed, failed or blocked. Local mock tests do
not prove tenant access or consent. These reads do not write to the inbound ledger.

## Server configuration

Routes are disabled unless `GATEWAY_WORKFLOWS_ENABLED=1`. Set:

- `DS_AUTH_SERVER=account-d.docusign.com` (sandbox only in this POC)
- `DS_CLIENT_ID`, `DS_IMPERSONATED_USER_GUID`, `DS_PRIVATE_KEY_PATH`: the existing PUG JWT identity
- `DS_WORKFLOW_ACCOUNT_ID`: the explicitly selected sandbox account UUID
- `PUG_OPERATOR_HTPASSWD_FILE`: a read-only mounted bcrypt htpasswd file

On the current deployment, reuse `/opt/traefik/secrets/monitor_htpasswd` as an
additional read-only file mount. Do not copy its contents into source or image.
The existing Traefik `/docusign` authentication remains in place and forwards
Basic authorization to the application. The application verifies the same login
itself, including on loopback. All configured operators have the same read scope.
This does not introduce per-department authorization.

Workflow authentication has a separate short-lived token cache and requests
`signature impersonation aow_manage`. Existing signing routes are not changed.
The integration's impersonated sandbox user must grant those scopes. If a consent
link uses `https://developers.docusign.com/platform/auth/consent`, that exact
redirect must first be registered in the integration's Apps and Keys settings.
An integration key identifies the app; the user granting consent must also match
the configured impersonated user.

## Expected failures

- **401:** operator login absent/incorrect; no provider call is made.
- **422:** an input ID is not a UUID; no provider call is made.
- **503 / docusign_consent_required:** grant the requested scopes for the configured user.
- **503 / configuration error:** disabled/missing sandbox account, key or operator file configuration.
- **403:** provider denied access. Check user/account permissions and enabled features.
- **404:** resource unavailable; do not conclude that it was deleted solely from this response.
- **429:** rate limited; an integer provider Retry-After is forwarded when present.
- **502/504:** provider authentication, transport, unexpected response or timeout failure.

No automatic trigger retries or provider mutations exist in this increment. The
current official specification exposes no pagination parameters for these list
operations; PUG does not invent them or claim exhaustive historical coverage.

## Verification and rollout

Run `python -m unittest discover -s tests -v` in an isolated environment installed
from `requirements-test.txt`. Tests cover correct and incorrect operator access,
four OpenAPI GET operations, field projection, provider error redaction, consent
failure, token caching, fixed sandbox URLs, timeouts and existing gateway behavior.

Deploy an immutable source revision with the existing data/key mounts and HMAC
configuration preserved. Add only the read-only operator credential-file mount
and the new account/enablement settings. Verify readiness, public 401 protection,
Swagger's four operations and each live provider result. Keep the prior compose
and image for rollback. Rolling back code must not restore an old ledger database.

## Sources

- [Official Workflow Builder schema](https://github.com/docusign/OpenAPI-Specifications/blob/master/workflowbuilder.rest.swagger-1.0.0.json)
- [Workflow API lifecycle operations](https://www.docusign.com/blog/developers/new-maestro-api-endpoints-more-control-more-automation-less-effort)
- [Workflow Builder scope guidance](https://www.docusign.com/blog/developers/common-api-tasks-list-all-your-maestro-workflows-using-the-maestro-api)
