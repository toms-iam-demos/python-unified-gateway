#!/usr/bin/env bash
set -euo pipefail
if [[ $# -gt 1 || (${1:-} != "" && ${1:-} != --browser) ]]; then
  echo "Usage: $0 [--browser]" >&2
  exit 2
fi
cd "$(dirname "$0")"
d() { docker --context colima-pug-rehearsal "$@"; }
gateway=sha256:35690f60beb4d0cc8db6e0895c948c9fb601e4e6421e59cdd5e97d607dfc8928
traefik=traefik@sha256:f79c88ed5252ae1e31c757a9796d751461ddb502437b8d8526db9e12605a82eb
for image in "$gateway" "$traefik"; do
  test "$(d image inspect -f '{{.Os}}/{{.Architecture}}' "$image")" = linux/amd64
done
name="pug-ingress-$$"
net=
edge=
app=
config=$(mktemp "$PWD/.traefik.XXXXXXXX.yml")
cleanup() {
  status=$?
  if [ "$status" -ne 0 ] && [ -n "$edge" ]; then d logs "$edge" >&2 || true; fi
  if [ -n "$edge" ]; then d rm -f "$edge" >/dev/null || true; fi
  if [ -n "$app" ]; then d rm -f "$app" >/dev/null || true; fi
  if [ -n "$net" ]; then d network rm "$net" >/dev/null || true; fi
  rm -f "$config"
}
trap cleanup EXIT
user=$(htpasswd -nbB operator synthetic-password)
sed "s|SYNTHETIC_USER_HASH|$user|" > "$config" <<'EOF'
http:
  routers:
    operator:
      rule: PathPrefix(`/webhooks/monitor`) || PathPrefix(`/events`) || Path(`/static/monitor.js`)
      middlewares: [operator]
      service: gateway
    signed-webhook:
      rule: Path(`/webhooks/docusign`) && Method(`POST`)
      service: gateway
    health:
      rule: Path(`/health`)
      service: gateway
  middlewares:
    operator:
      basicAuth:
        users: ['SYNTHETIC_USER_HASH']
        removeHeader: true
  services:
    gateway:
      loadBalancer:
        servers:
          - url: http://gateway:8001
EOF
net=$(d network create --internal "$name")
app=$(d run -d --pull never --platform linux/amd64 --network "$net" --network-alias gateway --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 -e GATEWAY_DB_PATH=/tmp/events.db -e DOCUSIGN_CONNECT_HMAC_SECRET=synthetic-only "$gateway")
edge=$(d run -d --pull never --platform linux/amd64 --network "$net" --network-alias edge --read-only --mount "type=bind,src=$config,dst=/fixture.yml,readonly" "$traefik" --entrypoints.web.address=:8080 --providers.file.filename=/fixture.yml --providers.file.watch=false --global.checknewversion=false --global.sendanonymoususage=false)
d exec "$edge" traefik version
if [[ ${1:-} == --browser ]]; then
  for attempt in $(seq 1 25); do
    if d exec "$app" python -c 'import urllib.request; urllib.request.urlopen("http://edge:8080/health", timeout=2)' 2>/dev/null; then
      node ../rehearse.cjs "$app" --traefik
      exit
    fi
    sleep 1
  done
  echo "Traefik did not route gateway health" >&2
  exit 1
fi
d exec -i "$app" python - < check.py
