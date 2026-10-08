# Verification and scope

Packaged September 23, 2026 as an independently runnable example within PUG.

- Synthetic inputs only; no provider credentials, persistence, outbound delivery or payment actions.
- Local loopback binding and trusted-host protection remain enabled.
- Nine tests cover reconciliation invariants, malformed values, API limits and host restrictions.
- macOS clean-environment installation and API/static-page smoke checks performed for packaging.
- CI is configured for Linux with Python 3.10 and 3.12; remote results must be checked separately.
- Windows instructions provided; Windows execution not yet verified.
- Branding sources and limitations are recorded in README.md.
- Live Maestro integration, funding eligibility and card matching are not implemented.
