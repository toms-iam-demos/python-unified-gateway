"""Durable, bounded operator audit metadata. Never store request/response content."""
from __future__ import annotations
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Query
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from gateway.routers.workflows import operator

log = logging.getLogger(__name__)
MAX_BYTES = 64 * 1024 * 1024
SCHEMA = '''CREATE TABLE IF NOT EXISTS security_audit (
 sequence INTEGER PRIMARY KEY AUTOINCREMENT,
 time TEXT NOT NULL, request_id TEXT NOT NULL, phase TEXT NOT NULL,
 method TEXT NOT NULL, route TEXT NOT NULL, actor TEXT,
 status INTEGER, resources TEXT NOT NULL
)'''


def connect():
    path = Path(os.environ['PUG_AUDIT_DB_PATH'])
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        pass
    else:
        os.close(fd)
    db = sqlite3.connect(str(path), timeout=2)
    try:
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        page_size = db.execute('PRAGMA page_size').fetchone()[0]
        db.execute(f'PRAGMA max_page_count={MAX_BYTES // page_size}')
        db.execute(SCHEMA)
        db.commit()
        return db
    except BaseException:
        db.close()
        raise


def append(event):
    db = connect()
    try:
        with db:
            db.execute('INSERT INTO security_audit(time,request_id,phase,method,route,actor,status,resources) VALUES(?,?,?,?,?,?,?,?)',
                (datetime.now(timezone.utc).isoformat(), event['request_id'], event['phase'], event['method'],
                 event['route'], event.get('actor'), event.get('status'), json.dumps(event.get('resources', {}), sort_keys=True)))
    finally:
        db.close()


def metadata(scope, request_id, phase, status=None):
    # Only matched route templates and UUID references; never raw paths or query strings.
    route = getattr(scope.get('route'), 'path', '/docusign/*')
    resources = {}
    for k in ('accountId', 'agreementId', 'workflow_id', 'instance_id'):
        try:
            resources[k] = str(UUID(scope.get('path_params', {}).get(k, '')))
        except (ValueError, TypeError, AttributeError):
            pass
    method = scope.get('method', '')
    return {'request_id': request_id, 'phase': phase, 'method': method if method in ('GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS') else 'OTHER',
            'route': route, 'actor': scope.get('state', {}).get('audit_actor'), 'status': status, 'resources': resources}


class SecurityAuditMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not (scope.get('path', '') == '/docusign' or scope.get('path', '').startswith('/docusign/')):
            return await self.app(scope, receive, send)
        request_id = str(uuid4())
        response_ready = False
        failed = False

        async def unavailable():
            log.error('security_audit_unavailable request_id=%s', request_id)
            await JSONResponse({'detail': {'code':'security_audit_unavailable', 'message':'Operator API unavailable because audit recording failed.'}},
                               status_code=503, headers={'Cache-Control':'no-store','X-PUG-Request-ID':request_id})(scope, receive, send)
        try:
            await run_in_threadpool(append, metadata(scope, request_id, 'received'))
        except (OSError, sqlite3.Error, KeyError):
            return await unavailable()

        async def audited_send(message):
            nonlocal response_ready, failed
            if failed:
                return
            if message['type'] == 'http.response.start':
                try:
                    await run_in_threadpool(append, metadata(scope, request_id, 'response_ready', message['status']))
                except (OSError, sqlite3.Error, KeyError):
                    failed = True
                    return await unavailable()
                response_ready = True
                message = dict(message)
                message['headers'] = list(message.get('headers', [])) + [(b'x-pug-request-id', request_id.encode())]
            await send(message)
        try:
            await self.app(scope, receive, audited_send)
        except Exception:
            if not response_ready and not failed:
                try:
                    await run_in_threadpool(append, metadata(scope, request_id, 'exception', 500))
                except (OSError, sqlite3.Error, KeyError):
                    log.error('security_audit_unavailable request_id=%s', request_id)
            raise


router = APIRouter(prefix='/docusign/security', tags=['PUG security'], dependencies=[Depends(operator)])


@router.get('/audit')
def recent_audit(limit: int = Query(25, ge=1, le=100)):
    """Recent operator-API metadata. response_ready means before response transmission, not confirmed receipt. Edge-rejected requests are outside this log."""
    db = connect()
    try:
        db.row_factory = sqlite3.Row
        rows = db.execute('SELECT * FROM security_audit ORDER BY sequence DESC LIMIT ?', (limit,)).fetchall()
        data = []
        for row in rows:
            entry = dict(row)
            entry['resources'] = json.loads(entry['resources'])
            data.append(entry)
        return JSONResponse({'events': data, 'identity_note':'A shared login identifies the credential, not an individual person.'}, headers={'Cache-Control':'no-store'})
    finally:
        db.close()
