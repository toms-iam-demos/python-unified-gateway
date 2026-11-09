#!/usr/bin/env bash
set -eu
d() { docker --context "${PUG_REHEARSAL_CONTEXT:-colima-pug-rehearsal}" "$@"; }
image=sha256:35690f60beb4d0cc8db6e0895c948c9fb601e4e6421e59cdd5e97d607dfc8928
test "$(d image inspect -f '{{.Id}} {{.Os}}/{{.Architecture}}' "$image")" = "$image linux/amd64"
container=$(d run -d --pull never --platform linux/amd64 --network none --read-only --tmpfs /tmp -e PYTHONDONTWRITEBYTECODE=1 -e GATEWAY_DB_PATH=/tmp/events.db -e DOCUSIGN_CONNECT_HMAC_SECRET=synthetic-only "$image")
trap 'd rm -f "$container" >/dev/null' EXIT
for attempt in $(seq 1 20); do
  if d exec "$container" python -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8001/health",timeout=2)' 2>/dev/null; then break; fi
  sleep 1
done
d exec "$container" python -c 'import platform,sys; assert platform.machine()=="x86_64"; assert sys.version_info[:3]==(3,12,12); print("PASS exact AMD64 image and Python 3.12.12")'

node "$(dirname "$0")/rehearse.cjs" "$container"
