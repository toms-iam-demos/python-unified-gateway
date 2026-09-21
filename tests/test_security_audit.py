import json
import sqlite3
import bcrypt
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from gateway import security_audit as audit
from gateway.routers.workflows import operator

@pytest.fixture
def configured(tmp_path,monkeypatch):
    db=tmp_path/'audit.sqlite3'
    monkeypatch.setenv('PUG_AUDIT_DB_PATH',str(db))
    ht=tmp_path/'users';ht.write_text('reader:'+bcrypt.hashpw(b'test-password',bcrypt.gensalt(rounds=4)).decode()+'\n')
    monkeypatch.setenv('PUG_OPERATOR_HTPASSWD_FILE',str(ht))
    return db

def make_app():
    a=FastAPI()
    @a.get('/docusign/test/{agreementId}',dependencies=[Depends(operator)])
    def read(agreementId:str):return {'private':'RESPONSE_SECRET'}
    a.include_router(audit.router)
    a.add_middleware(audit.SecurityAuditMiddleware)
    return a

def rows(db):
    with sqlite3.connect(db) as c:
        c.row_factory=sqlite3.Row
        return [dict(x) for x in c.execute('SELECT * FROM security_audit ORDER BY sequence')]

def test_durable_identity_and_no_sensitive_values(configured):
    c=TestClient(make_app())
    identifier='3376cedc-d0e0-45e9-8e15-7198bc269862'
    r=c.get('/docusign/test/'+identifier+'?q=QUERY_SECRET',auth=('reader','test-password'),headers={'x-user':'FORGED','x-request-id':'FORGED_ID'})
    assert r.status_code==200
    events=rows(configured)
    assert len(events)==2 and events[1]['actor']=='reader'
    assert events[1]['route']=='/docusign/test/{agreementId}'
    assert events[1]['status']==200 and events[1]['phase']=='response_ready'
    assert json.loads(events[1]['resources'])=={'agreementId':identifier}
    assert events[1]['request_id']==r.headers['x-pug-request-id']
    text=json.dumps(events)
    for value in ('QUERY_SECRET','RESPONSE_SECRET','test-password','FORGED'):
        assert value not in text
    # A fresh application and connection can read prior-process audit rows.
    fresh=TestClient(make_app()).get('/docusign/security/audit',auth=('reader','test-password'))
    assert fresh.status_code==200 and any(e['request_id']==events[1]['request_id'] for e in fresh.json()['events'])
    assert configured.stat().st_mode & 0o777==0o600

def test_unauthenticated_user_not_attributed(configured):
    r=TestClient(make_app()).get('/docusign/test/PRIVATE_PATH',auth=('UNTRUSTED_USER','wrong'))
    assert r.status_code==401
    events=rows(configured)
    assert events[-1]['actor'] is None and events[-1]['status']==401
    assert 'UNTRUSTED_USER' not in json.dumps(events) and 'PRIVATE_PATH' not in json.dumps(events)

def test_fail_closed_before_handler(configured,monkeypatch):
    def fail(event):raise sqlite3.OperationalError('PRIVATE_PATH')
    monkeypatch.setattr(audit,'append',fail)
    a=FastAPI();called=[]
    @a.get('/docusign/test')
    def read():called.append(True);return {'secret':True}
    a.add_middleware(audit.SecurityAuditMiddleware)
    r=TestClient(a).get('/docusign/test')
    assert r.status_code==503 and not called and 'PRIVATE_PATH' not in r.text

def test_completion_failure_withholds_response(configured,monkeypatch):
    original=audit.append
    def fail(event):
        if event['phase']=='response_ready':raise sqlite3.OperationalError('disk full')
        original(event)
    monkeypatch.setattr(audit,'append',fail)
    r=TestClient(make_app()).get('/docusign/test/id',auth=('reader','test-password'))
    assert r.status_code==503 and 'RESPONSE_SECRET' not in r.text
    assert len(rows(configured))==1

def test_audit_read_is_protected_and_bounded(configured):
    c=TestClient(make_app())
    assert c.get('/docusign/security/audit').status_code==401
    assert c.get('/docusign/security/audit?limit=101',auth=('reader','test-password')).status_code==422
    assert c.get('/docusign/security/audit?limit=2',auth=('reader','test-password')).headers['cache-control']=='no-store'

def test_non_operator_routes_do_not_depend_on_audit(monkeypatch):
    monkeypatch.delenv('PUG_AUDIT_DB_PATH',raising=False)
    a=FastAPI()
    @a.post('/webhooks/example')
    def hook():return {'ok':True}
    a.add_middleware(audit.SecurityAuditMiddleware)
    assert TestClient(a).post('/webhooks/example').status_code==200
