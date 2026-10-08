"""Stateful, loopback-only procurement simulator. No network client exists here."""
from app.security import RequestSizeLimit
import json
import os
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from starlette.middleware.trustedhost import TrustedHostMiddleware

ROOT = Path(__file__).resolve().parent
DB = Path(os.environ.get('PUG_DEMO_DB', str(ROOT.parent / 'data' / 'demo.db')))
TOKEN = secrets.token_urlsafe(32)
app = FastAPI(title='PUG • Getty procurement simulator', version='1.0.0', description='Local synthetic records only. No docusign, Oracle, payment or email calls. Demo reviewer roles are walkthrough personas, not enterprise identity controls.')
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', 'testserver'])
app.add_middleware(RequestSizeLimit)
app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')

@contextmanager
def db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=10)
    c.row_factory = sqlite3.Row
    try:
        c.execute('BEGIN IMMEDIATE')
        c.executescript('CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, cohort TEXT, kind TEXT, version INTEGER, amount INTEGER, ceiling INTEGER, accepted INTEGER DEFAULT 0, status TEXT); CREATE TABLE IF NOT EXISTS plans(id TEXT PRIMARY KEY, record_id TEXT, version INTEGER, operation TEXT, target INTEGER, state TEXT, receipt TEXT); CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, record_id TEXT, event TEXT);')
        c.execute('BEGIN IMMEDIATE') if not c.in_transaction else None
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()

def log(c, rid, event):
    c.execute('INSERT INTO audit(time,record_id,event) VALUES(?,?,?)', (datetime.now(timezone.utc).isoformat(), rid, event))

def row(c, table, key):
    # Table names are internal constants, never caller input.
    r = c.execute(f'SELECT * FROM {table} WHERE id=?', (key,)).fetchone()
    if not r: raise HTTPException(404, 'Object not found')
    return dict(r)

@app.middleware('http')
async def local_boundary(request: Request, call_next):
    if request.url.path.startswith('/api/'):
        origin = request.headers.get('origin')
        if (origin and origin != str(request.base_url).rstrip('/')) or request.headers.get('sec-fetch-site') == 'cross-site':
            return JSONResponse({'detail': 'Foreign origin rejected'}, status_code=403)
        if not secrets.compare_digest(request.headers.get('x-demo-token', ''), TOKEN):
            return JSONResponse({'detail': 'Open the local site to obtain the session token. Remote access is unsupported.'}, status_code=403)
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'" if request.url.path != '/docs' else "frame-ancestors 'none'"
    return response

@app.get('/', response_class=HTMLResponse)
def home():
    return (ROOT / 'static' / 'index.html').read_text().replace('__TOKEN__', TOKEN)

@app.get('/health')
def health(): return {'status': 'ok', 'mode': 'local_simulation', 'external_calls': 0}

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

class Seed(StrictModel):
    count: int = Field(default=3, ge=3, le=10000)

@app.post('/api/seed')
def seed(body: Seed):
    with db() as c:
        if c.execute('SELECT count(*) FROM records').fetchone()[0]: raise HTTPException(409, 'Reset this cohort before seeding another.')
        cohort = 'GETTY-DEMO-' + uuid.uuid4().hex[:8]
        kinds = [('fabrication',15000000,18000000),('digitization',6000000,24000000),('conservation',4800000,4800000)]
        for i in range(body.count):
            kind, amount, ceiling = kinds[i % 3]
            c.execute('INSERT INTO records VALUES(?,?,?,?,?,?,?,?)', (f'PO-DEMO-{4101+i}',cohort,kind,1,amount,ceiling,0,'ready'))
        log(c,cohort,f'Seeded {body.count} fictional purchasing records; zero external calls')
    return {'cohort':cohort, 'count':body.count}

@app.get('/api/state')
def state():
    with db() as c:
        total = c.execute('SELECT count(*) FROM records').fetchone()[0]
        sums = c.execute('SELECT coalesce(sum(amount),0),coalesce(sum(accepted),0) FROM records').fetchone()
        counts = dict(c.execute('SELECT state,count(*) FROM plans GROUP BY state').fetchall())
        return {'count':total,'committed_cents':sums[0], 'accepted_cents':sums[1], 'plan_counts':counts,'external_calls':0,'records':[dict(r) for r in c.execute('SELECT * FROM records ORDER BY id LIMIT 100')], 'audit':[dict(r) for r in c.execute('SELECT * FROM audit ORDER BY seq DESC LIMIT 25')], 'plans':[dict(r) for r in c.execute('SELECT * FROM plans ORDER BY rowid DESC LIMIT 100')], 'cohort':c.execute('SELECT cohort FROM records LIMIT 1').fetchone()[0] if total else None}

class Plan(StrictModel):
    record_id: str
    accepted_images: int = Field(default=9800, ge=0, le=10000)
    amendment_dollars: int = Field(default=6500, ge=1, le=30000)

@app.post('/api/plans')
def plan(body: Plan):
    with db() as c:
        r = row(c,'records',body.record_id)
        if c.execute("SELECT 1 FROM plans WHERE record_id=? AND state IN ('prepared','approved','unknown')",(r['id'],)).fetchone(): raise HTTPException(409,'Resolve the existing plan first')
        if r['status'] == 'verified': raise HTTPException(409,'This fixture is complete; replay its existing command or reset the cohort')
        operation = {'fabrication':'register_contract_reference','digitization':'record_service_acceptance','conservation':'implement_approved_change'}[r['kind']]
        target = r['amount'] if r['kind']=='fabrication' else body.accepted_images*240 if r['kind']=='digitization' else r['amount']+body.amendment_dollars*100
        pid = 'CMD-' + uuid.uuid4().hex[:12]
        c.execute('INSERT INTO plans VALUES(?,?,?,?,?,?,?)',(pid,r['id'],r['version'],operation,target,'prepared',None))
        log(c,r['id'],f'Prepared {pid}: {operation}; expected version {r["version"]}')
        return row(c,'plans',pid)

@app.post('/api/plans/{pid}/approve')
def approve(pid: str):
    with db() as c:
        p = row(c,'plans',pid)
        if p['state'] != 'prepared': raise HTTPException(409,'Only a prepared plan can be approved')
        r = row(c,'records',p['record_id'])
        if r['version'] != p['version']: raise HTTPException(409,'Stale plan; destination version changed')
        c.execute("UPDATE plans SET state='approved' WHERE id=?",(pid,))
        log(c,r['id'],'Demo reviewer approved '+pid+' (simulated persona, not authenticated segregation of duties)')
        return row(c,'plans',pid)

class Execute(StrictModel):
    fault: str = Field(default='none', pattern='^(none|lost_response|version_conflict)$')

@app.post('/api/plans/{pid}/execute')
def execute(pid: str, body: Execute):
    with db() as c:
        p = row(c,'plans',pid)
        if p['state'] in ('verified','unknown'): return {**p,'duplicate_suppressed':True}
        if p['state'] != 'approved': raise HTTPException(409,'Approval is required')
        r = row(c,'records',p['record_id'])
        if body.fault=='version_conflict':
            c.execute('UPDATE records SET version=version+1 WHERE id=?',(r['id'],))
            r['version'] += 1
        if r['version'] != p['version']:
            c.execute("UPDATE plans SET state='blocked' WHERE id=?",(pid,))
            log(c,r['id'],'Version conflict; no commercial value changed; rebuild and review')
            return {'state':'blocked','reason':'version_conflict'}
        amount = p['target'] if r['kind']=='conservation' else r['amount']
        accepted = p['target'] if r['kind']=='digitization' else r['accepted']
        receipt = json.dumps({'command_id':pid,'record_id':r['id'],'version':r['version']+1,'amount':amount,'accepted':accepted})
        state = 'unknown' if body.fault=='lost_response' else 'verified'
        c.execute('UPDATE records SET amount=?,accepted=?,version=version+1,status=? WHERE id=?',(amount,accepted,state,r['id']))
        saved = row(c,'records',r['id'])
        if (saved['amount'], saved['accepted'], saved['version']) != (amount, accepted, r['version']+1):
            raise HTTPException(409,'Destination read-back mismatch')
        c.execute('UPDATE plans SET state=?,receipt=? WHERE id=?',(state,receipt,pid))
        log(c,r['id'],f'{pid}: destination applied once; '+('response lost, reconciliation required' if state=='unknown' else 'read-back verified'))
        return row(c,'plans',pid)

@app.post('/api/plans/{pid}/recover')
def recover(pid: str):
    with db() as c:
        p = row(c,'plans',pid)
        if p['state'] != 'unknown': raise HTTPException(409,'Only an unknown outcome needs recovery')
        receipt = json.loads(p['receipt']); r = row(c,'records',p['record_id'])
        if any(r[k] != receipt[k] for k in ['version','amount','accepted']): raise HTTPException(409,'Read-back mismatch; manual review required')
        c.execute("UPDATE plans SET state='verified' WHERE id=?",(pid,))
        c.execute("UPDATE records SET status='verified' WHERE id=?",(r['id'],))
        log(c,r['id'],'Reconciled '+pid+' from existing receipt; no second write')
        return row(c,'plans',pid)

class Reset(StrictModel):
    cohort: str
    confirmation: str

@app.post('/api/reset')
def reset(body: Reset):
    if not body.cohort.startswith('GETTY-DEMO-'):
        raise HTTPException(400, 'Only owned GETTY-DEMO cohorts can be reset')
    if body.confirmation != 'RESET '+body.cohort: raise HTTPException(400,'Exact cohort confirmation required')
    with db() as c:
        ids = [r[0] for r in c.execute('SELECT id FROM records WHERE cohort=?',(body.cohort,))]
        if not ids: raise HTTPException(404,'Cohort not found')
        c.execute('DELETE FROM plans WHERE record_id IN (SELECT id FROM records WHERE cohort=?)',(body.cohort,))
        c.execute('DELETE FROM records WHERE cohort=?',(body.cohort,))
        log(c,body.cohort,f'Reset {len(ids)} local owned records; audit summary retained')
        return {'removed':len(ids)}

@app.get('/api/export')
def export():
    with db() as c:
        return {'mode':'synthetic_local','external_calls':0,'records':[dict(r) for r in c.execute('SELECT * FROM records')], 'plans':[dict(r) for r in c.execute('SELECT * FROM plans')], 'audit':[dict(r) for r in c.execute('SELECT * FROM audit')]}
