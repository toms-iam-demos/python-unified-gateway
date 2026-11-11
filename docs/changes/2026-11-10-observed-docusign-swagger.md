# Private reference catalogs in Swagger

PUG can now include an operator-supplied OpenAPI 3 reference catalog alongside
its pinned public specifications. Set `GATEWAY_OBSERVED_API_SPEC_PATH` to the
absolute path of a private JSON file and keep
`GATEWAY_FULL_DOCUSIGN_API_ENABLED=1`. An unset path preserves the existing
424-operation catalog. An explicitly configured missing or invalid file fails
startup instead of silently dropping the reference routes.

The file is operator-managed runtime data. For containers, mount it read-only
and set the path to its location inside the container. Do not commit private
route inventories, account records, captured bundles, or credentials to this
public repository. Only the generic loader, synthetic tests and instructions
are published here.

Every operation is registered below `/docusign/observed` and tagged as observed
client evidence. Historical verification metadata can appear in the supplied
specification. Discovery, a historical successful response and current execution
permission remain separate facts. Static routes precede identifier placeholders.

All observed operations require operator authentication and return
`403 operation_locked` before reading provider configuration, creating tokens
or calling the network. Provider server URLs and execution claims in the file
cannot configure a transport or enable execution. Existing policy still permits
only the six explicitly allowlisted public-spec reads.

The loader bounds file size, validates OpenAPI version, rejects malformed or
ambiguous paths and duplicate operation IDs, and requires inline declared path
parameters. It does not infer payloads, discover routes, fetch remote schemas,
request credentials or contact providers. The catalog author must clearly label
unknown base URLs, schemas, parameter constraints and authentication requirements.

Local validation covers the existing gateway suite plus synthetic catalog
registration, operator authentication, locked GET/POST behavior before all
credential/network access, static-route precedence and invalid input rejection.
The private catalog receives additional local verification separately. CI tests
use synthetic paths and require no private input or provider access.

This change does not deploy PUG. The deployment host was unreachable from the
authoring session (`ssh`: Operation not permitted). To remove the added surface,
unset `GATEWAY_OBSERVED_API_SPEC_PATH` and restart/redeploy the gateway, or revert
this source change. No provider records or database schemas are changed.
