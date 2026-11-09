import base64
import hashlib
import hmac
import json
import platform
import sqlite3
import time
import urllib.error
import urllib.request

assert platform.machine() == "x86_64"
auth = "Basic " + base64.b64encode(b"operator:synthetic-password").decode()
body = b'{"event":"synthetic-ingress-check"}'
signature = base64.b64encode(hmac.digest(b"synthetic-only", body, "sha256")).decode()

def request(path, *, authorization=None, payload=None, signature=None):
    headers = {}
    if authorization:
        headers["Authorization"] = authorization
    if signature:
        headers["X-DocuSign-Signature-1"] = signature
    req = urllib.request.Request("http://edge:8080" + path, payload, headers)
    try:
        response = urllib.request.urlopen(req, timeout=3)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()

for attempt in range(25):
    try:
        if request("/health")[0] == 200:
            break
    except OSError:
        pass
    time.sleep(1)
else:
    raise SystemExit("Traefik did not route gateway health")
for path in (
    "/webhooks/monitor/ui", "/webhooks/monitor", "/static/monitor.js",
    "/events/ui", "/events/ui/snapshot", "/events/ui/assets/app.js",
):
    status, headers, _ = request(path)
    assert status == 401 and headers["WWW-Authenticate"].startswith("Basic"), path
    assert request(path, authorization="Basic " + base64.b64encode(b"operator:wrong").decode())[0] == 401, path
    status, _, content = request(path, authorization=auth)
    assert status == 200 and content, path
print("PASS Traefik Basic Auth: anonymous and incorrect credentials denied; valid operator opens pages, feeds and scripts")
path = "/webhooks/docusign"
assert request(path, payload=body, signature="invalid")[0] == 401
status, _, result = request(path, payload=body, signature=signature)
assert status == 200 and json.loads(result)["persisted"] is True
with sqlite3.connect("file:/tmp/events.db?mode=ro", uri=True) as db:
    rows = db.execute("SELECT event_id, source, path, verify_status, body_raw FROM events").fetchall()
assert len(rows) == 1
event_id, source, stored_path, verification, payload = rows[0]
assert (source, stored_path, verification, payload) == ("docusign", path, "verified", body)
_, _, monitor = request("/webhooks/monitor", authorization=auth)
assert json.loads(monitor)["events"][0]["persistence"]["event_id"] == event_id
# The initial auth checks can prime an empty snapshot. Refresh is rate-limited.
for attempt in range(10):
    status, _, snapshot = request("/events/ui/snapshot?refresh=true", authorization=auth)
    assert status == 200
    if event_id.encode() in snapshot:
        break
    time.sleep(0.5)
else:
    raise AssertionError("Verified receipt did not appear in the refreshed snapshot")
print("PASS webhook bypasses operator auth, rejects invalid HMAC, accepts valid HMAC and matches one SQLite receipt in both operator feeds")
