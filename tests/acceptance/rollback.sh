#!/usr/bin/env bash
set -euo pipefail
context=${PUG_REHEARSAL_CONTEXT:?Set the dedicated local rehearsal context}
old=${PUG_ROLLBACK_IMAGE:?Set the known-good local AMD64 image ID}
new=${PUG_GATEWAY_IMAGE:?Set the candidate local AMD64 image ID}
d() { docker --context "$context" "$@"; }
verify_image() {
  [[ $1 =~ ^sha256:[0-9a-f]{64}$ ]] &&
    test "$(d image inspect -f '{{.Id}} {{.Architecture}}' "$1" 2>/dev/null)" = "$1 amd64"
}
verify_image "$old"
verify_image "$new"
test "$old" != "$new"
export COMPOSE_REMOVE_ORPHANS=false COMPOSE_IGNORE_ORPHANS=true
dir=$(mktemp -d)
cd "$dir"
project="pug-swap-test-$$"
export project old new
cleanup() {
  local result=$?
  if [[ -f initial.json ]]; then
    d compose -f initial.json down -v || result=1
    for resource in ps network volume; do
      case "$resource" in
        ps) remaining=$(d ps -aq --filter "label=com.docker.compose.project=$project") || result=1 ;;
        *) remaining=$(d "$resource" ls -q --filter "label=com.docker.compose.project=$project") || result=1 ;;
      esac
      [[ -z $remaining ]] || result=1
    done
  fi
  rm -rf -- "$dir"
  exit "$result"
}
trap cleanup EXIT
python3 - <<'PY'
import json, os
from pathlib import Path
project,old,new=[os.environ[k] for k in ('project','old','new')]
base={'name':project,'networks':{'default':{'internal':True}},'volumes':{'data':{}}}
gateway={'pull_policy':'never','platform':'linux/amd64','user':'root','read_only':True,
         'cap_drop':['ALL'],'security_opt':['no-new-privileges:true'],
         'tmpfs':['/tmp:rw,noexec,nosuid,size=64m'],'volumes':['data:/app/data'],
         'environment':{'PYTHONDONTWRITEBYTECODE':'1','GATEWAY_DB_PATH':'/app/data/gateway.db',
                        'PUG_AUDIT_DB_PATH':'/app/data/security-audit.sqlite3',
                        'PUG_AUDIT_ENABLED':'1','DOCUSIGN_CONNECT_HMAC_SECRET':'synthetic-only'}}
for name,image in (('rollback',old),('cutover',new)):
    doc={**base,'services':{'ds-gw':{**gateway,'image':image}}}
    Path(name+'.json').write_text(json.dumps(doc))
    if name=='rollback':
        doc['services']['historical']={'image':old,'pull_policy':'never','platform':'linux/amd64','command':['python','-c','import time; time.sleep(900)']}
        Path('initial.json').write_text(json.dumps(doc))
PY
d compose version
for file in initial cutover rollback; do d compose -f "$file.json" config -q; done
d compose -f initial.json up -d --no-build --pull never
orphan=$(d compose -f initial.json ps -q historical)
test -n "$orphan"
verify() {
  local expected=$1
  app=$(d compose -f initial.json ps -q ds-gw)
  test "$(d inspect -f '{{.Image}}' "$app")" = "$expected" || return 1
  test "$(d inspect -f '{{.State.Running}}' "$orphan")" = true || return 1
  test "$(d compose -f initial.json ps -q historical)" = "$orphan" || return 1
  for attempt in {1..20}; do
    if d exec "$app" python -c 'import urllib.request; assert urllib.request.urlopen("http://127.0.0.1:8001/health",timeout=2).status==200' 2>/dev/null; then return; fi
    sleep 1
  done
  return 1
}
recreate() {
  d compose -f "$1.json" up -d --no-deps --no-build --pull never --force-recreate ds-gw
}
restore() {
  if ! recreate rollback || ! verify "$1"; then
    echo 'Rollback verification failed' >&2
    return 43
  fi
  return 42
}
cutover() {
  if ! verify_image "$1"; then
    echo 'Candidate image unavailable or invalid' >&2
    return 41
  fi
  if ! recreate cutover || ! verify "$2"; then
    restore "$3"
    return $?
  fi
}
verify "$old"
original=$app
result=0
cutover sha256:0000000000000000000000000000000000000000000000000000000000000000 "$new" "$old" || result=$?
test "$result" -eq 41
verify "$old"
test "$app" = "$original"
echo 'PASS missing image rejected before replacement'
cutover "$new" "$new" "$old"
test "$app" != "$original"
cutover_app=$app
d exec -i "$app" python - <<'PY'
import base64, hmac, json, urllib.request
body=b'{"event":"synthetic-cutover-rollback"}'
sig=base64.b64encode(hmac.digest(b'synthetic-only',body,'sha256')).decode()
request=urllib.request.Request('http://127.0.0.1:8001/webhooks/docusign',body,{'X-DocuSign-Signature-1':sig})
with urllib.request.urlopen(request,timeout=5) as r:
    assert r.status==200 and json.load(r)['persisted']
PY
# Force the same post-start check used by a normal cutover to fail.
result=0
cutover "$new" "$old" "$old" || result=$?
test "$result" -eq 42
test "$app" != "$cutover_app"
d exec -i "$app" python - <<'PY'
import sqlite3
with sqlite3.connect('file:/app/data/gateway.db?mode=ro',uri=True) as db:
    assert db.execute('select verify_status,body_raw from events').fetchall()==[('verified',b'{"event":"synthetic-cutover-rollback"}')]
PY
result=0
cutover "$new" "$old" "$new" || result=$?
test "$result" -eq 43
verify "$old"
echo 'PASS injected rollback verification failure reported explicitly (43)'
echo 'PASS exact image cutover and rollback; gateway health and synthetic receipt preserved; historical container ID and running state unchanged'
