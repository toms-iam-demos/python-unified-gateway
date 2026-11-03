# Live host and gateway security hardening

Date: 2026-11-02 (America/Los_Angeles; operational changes continued on 2026-11-03 UTC).

The maintainer requested hardening of the existing service. They separately approved enabling the host firewall for ports 22/80/443 and retaining SSH keys while disabling SSH passwords. The latter changes used an automatic three-minute rollback; an independent key-authenticated connection and HTTPS checks passed before rollback was cancelled.

## Activated

- Upgraded the HTTPS proxy from unsupported 3.0.4 to the verified official 3.7.17 image, pinned by digest. Validated an isolated candidate with copied certificates before replacing the proxy. Retained the old container and configuration privately for recovery.
- Proxy now has a read-only filesystem, no added Linux capabilities, no privilege escalation, bounded memory/processes and rotating logs. Its administration listener stays loopback-only, and its API is not exposed through public routing.
- Preserved one-year host-only HSTS. Added MIME-sniffing and framing protections, no-referrer policy, private no-store caching and restricted camera/microphone/geolocation permissions. Removed server fingerprint headers and retained application-specific CSP policies.
- Required TLS 1.2 or newer with strict SNI. Verified TLS 1.2/1.3 success and TLS 1.0/1.1 rejection.
- Added per-client operator throttling before authentication, after the response-header middleware. Sustained requests are limited to ten per second with a 200-request burst to accommodate protected assets. A bounded probe returned 401 for unauthenticated requests followed by 429. Provider webhook routers are excluded from this operator throttle.
- Enabled default-deny host ingress with SSH/HTTP/HTTPS allowed. Fresh SSH key authentication passed; password and keyboard-interactive SSH authentication are disabled. IPv4/IPv6 web listeners are retained. Docker's own forwarding rules remain in place; UFW does not replace review of published container ports.
- Scanned actual installed Python versions, built dependency-only patches, and verified isolated startup against state copies with networking disabled. Applied patched packages to the gateway, catalog, visitors, Stripe, synthetic API, browser worker and static presentation services. Post-patch scans reported no known Python-package vulnerabilities in all seven inventories. Scans do not cover every OS/Node/browser component or prove absence of exploitable flaws.
- Restricted verified root-owned secret/state directories to owner-only access while preserving owners, contents and application access.
- Kept existing runtime state, provider permissions, operator verifiers and network aliases. Retained rollback containers and consistent SQLite snapshots. The core gateway now has a read-only root, dropped capabilities, no-new-privileges, resource limits and automatic restart. All patched application services have bounded rotating Docker logs. The non-root browser worker retains its existing browser-compatible seccomp policy and writable browser environment.
- Recovered approximately 3 GB by compressing old archived journals. Every archive was decompressed and its SHA-256 compared before removing its original. Private archives, existing backups and application databases remain preserved. Future journal growth is capped at 512 MB / 30 days with a 1 GB free-space reserve.

## Regression and live evidence

The gateway's 65 tests passed with patched dependencies. Updated read-only route introspection for lazy included routers and current model fields, preserving effective prefixes, dependencies and required parameters. Thirteen native-workflow readiness cases cover the expected HTTPS origin, workflow path, account, title, visible native control and absence of a login prompt; other accounts, lookalike origins, login pages and missing observations fail closed. The native browser remained signed in after restart, but an old raw-HTML marker gave a false-negative readiness result. Added the tested native-view fallback without changing the worker credential or provider authorization. A fresh container hostname also preserves the worker's existing stale-profile-lock recovery behavior. The queue counts remained unchanged and no jobs were replayed.

Live checks passed for home/health, persistence readiness, retained anonymous 401s, webhook GET 405, unknown-route 404 and protected response headers. Direct checks from outside the server found only ports 22/80/443 reachable; application/admin ports 8001/8080/8891/8896 were not reachable. Provider HTTPS connectivity passed from inside the patched worker. Its authenticated native view and idle queue were verified. No payments, signatures or provider mutations were performed as security tests.

## Remaining gates and limits

The host reports installed kernel/system updates awaiting reboot. Reboot is not implied by the application restarts: it remains pending the maintainer's explicit timing decision because another agent is still running checks. Docker and socket-activated SSH are configured to return on boot. MFA has not been enrolled; operator Basic authentication remains password-based. This is a verified hardening baseline, not a penetration-test certification or production-security sign-off. A short rate-limit probe is not a load test or proof against distributed attacks.

Deployment definitions under `deploy/` preserve these settings. Attach `api-hsts@file` first and `api-operator-rate@file` before operator authentication; preserve visitor scope routing and provider webhook routing. Do not replace the non-root browser sandbox with an unsandboxed browser to simplify deployment. Full source/profile migration and identity-provider enrollment remain separate from the security patches.
