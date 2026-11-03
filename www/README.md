# PUG www

The maintained website for Python Unified Gateway: root homepage, shared navigation, searchable catalog and example landing pages. Python serves validated content and Jinja templates; small JavaScript modules handle filtering and menus. This is the source component, not evidence that a particular build is deployed.

## Run locally

From the repository root:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r www/requirements.lock ./www
WWW_REQUIRE_AUTH=false .venv/bin/python -m uvicorn pug_www.app:app --host 127.0.0.1 --port 8080
```

On Windows, use `.venv\Scripts\python` and set environment variables with your shell's normal syntax. Anonymous mode is an explicit local-preview choice. The default requires a configured operator password file and fails closed when none is available.

## Website structure

| Path | Responsibility |
| --- | --- |
| `/` | Platform homepage |
| `/catalog` | Searchable collection with data-derived categories |
| `/catalog/{id}` | Canonical example landing page |
| `/demos` | Demonstration collection |
| `/demos/data-studio` | Explicitly proposed capability page, not a generator |
| `/build` | Developer capability entry point |
| `/workspaces/{agents,mcp,ham}` | Workspace descriptions, not connected runtimes |
| `/resources` | Guide and implementation entry point |
| `/api/v1/www/catalog` | Validated catalog metadata |
| `/static/www/*` | Versioned website CSS and JavaScript |
| `/brand/{name}` | Authenticated, profile-allowlisted assets |

This component has no provider write operations, run recorder, video storage, artifact upload service, or role-based authorization system. Existing connected demo services remain separate and are linked from approved profiles. Implementing those capabilities requires their own tested work.

## Deployment profile

Public source contains only generic Municipal, Museum and NFP examples. Organization-specific names, logos, media and operational links are supplied through an external JSON profile, following `docs/frontend/public-identity-policy.md`. The profile schema is in `src/pug_www/models.py`; `catalog.json` is a complete minimal example.

| Variable | Purpose |
| --- | --- |
| `WWW_REQUIRE_AUTH` | Defaults to `true`; `false` explicitly enables anonymous browsing |
| `WWW_HTPASSWD_FILE` | Server-held bcrypt htpasswd file, mounted read-only |
| `WWW_PROFILE_FILE` | External profile JSON; omitted uses generic bundled catalog |
| `WWW_ASSET_DIRECTORY` | Private mounted asset directory |
| `WWW_ALLOWED_HOSTS` | Comma-separated hostnames; defaults to loopback names |

A profile supplies `entries` and an optional `assets` map. Each entry can reference an asset key with `logo`; the `product` key supplies the existing PUG masthead logo. Preserve owner-selected workspace identities in the external profile. Files must resolve within the configured asset directory, including after symlink resolution. No arbitrary file paths or remote asset proxy are exposed.

Use HTTPS at the existing ingress and retain operator authentication at both ingress and application. Mount profile, assets and password file read-only. Keep credentials, private keys, runtime databases, videos and provider records outside the image and repository. Run the container with a read-only root filesystem, a bounded temporary directory and resource limits.

Do not replace the current gateway container or assume the repository Compose file matches the server. Route only reviewed website paths to this component; keep existing API, webhook, demo and health routes with their current services. Moving the root path requires a separate, explicit route change. Record the source commit and image digest for each deployment, retain the previous image, and smoke-test authentication, assets, deep links, menus and launch targets.

## Validation

```sh
python -m unittest discover -s www/tests -v
python tools/check_public_identity.py
```

The website workflow runs the package tests on Python 3.12 and 3.14. The existing publication identity workflow reviews tracked content. `src/` layout and package data include templates, CSS, JavaScript and the generic catalog in installed wheels. Do not use this directory as a place for deployment copies or credentials.
