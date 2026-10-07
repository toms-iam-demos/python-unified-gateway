import json
import pytest
from fastapi.testclient import TestClient
from app import main

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main,'DB',tmp_path/'test.db')
    with TestClient(main.app, headers={'x-demo-token':main.TOKEN}) as c:
        yield c

def prepare(c, kind=0):
    c.post('/api/seed',json={'count':3})
    rid=c.get('/api/state').json()['records'][kind]['id']
    p=c.post('/api/plans',json={'record_id':rid}).json()
    return rid,p['id']

def test_boundaries(client):
    assert client.get('/api/state',headers={'x-demo-token':''}).status_code==403
    assert client.post('/api/seed',json={'count':3},headers={'origin':'https://evil.example'}).status_code==403
    assert client.get('/',headers={'host':'evil.example'}).status_code==400
    assert client.post('/api/seed',json={'count':10001}).status_code==422

def test_fabrication_reference_only_and_replay(client):
    rid,pid=prepare(client)
    assert client.post(f'/api/plans/{pid}/execute',json={}).status_code==409
    client.post(f'/api/plans/{pid}/approve')
    a=client.post(f'/api/plans/{pid}/execute',json={}).json()
    assert a['state']=='verified'
    b=client.post(f'/api/plans/{pid}/execute',json={}).json()
    assert b['duplicate_suppressed']
    r=client.get('/api/state').json()['records'][0]
    assert r['amount']==15000000 and r['version']==2

def test_acceptance_arithmetic(client):
    rid,pid=prepare(client,1)
    client.post(f'/api/plans/{pid}/approve')
    client.post(f'/api/plans/{pid}/execute',json={})
    r=client.get('/api/state').json()['records'][1]
    assert r['accepted']==2352000
    assert 2400000-r['accepted']==48000
    assert r['amount']==6000000

def test_lost_response_restart_recovery(client):
    rid,pid=prepare(client,2)
    client.post(f'/api/plans/{pid}/approve')
    assert client.post(f'/api/plans/{pid}/execute',json={'fault':'lost_response'}).json()['state']=='unknown'
    # Fresh client exercises persisted state, without in-memory command state.
    with TestClient(main.app,headers={'x-demo-token':main.TOKEN}) as c:
        assert c.post(f'/api/plans/{pid}/execute',json={}).json()['duplicate_suppressed']
        assert c.post(f'/api/plans/{pid}/recover').json()['state']=='verified'
        r=c.get('/api/state').json()['records'][2]
        assert r['amount']==5450000 and r['version']==2

def test_conflict_and_replan(client):
    rid,pid=prepare(client,2)
    client.post(f'/api/plans/{pid}/approve')
    assert client.post(f'/api/plans/{pid}/execute',json={'fault':'version_conflict'}).json()['state']=='blocked'
    assert client.get('/api/state').json()['records'][2]['amount']==4800000
    assert client.post('/api/plans',json={'record_id':rid}).status_code==200

def test_invalid_quantities_and_reset_scope(client):
    prepare(client)
    assert client.post('/api/plans',json={'record_id':'PO-DEMO-4102','accepted_images':10001}).status_code==422
    cohort=client.get('/api/state').json()['cohort']
    with main.db() as c:
        c.execute("INSERT INTO records VALUES('FOREIGN','other','fabrication',1,100,100,0,'ready')")
    assert client.post('/api/reset',json={'cohort':cohort,'confirmation':'yes'}).status_code==400
    assert client.post('/api/reset',json={'cohort':cohort,'confirmation':'RESET '+cohort}).json()['removed']==3
    assert client.get('/api/state').json()['records'][0]['id']=='FOREIGN'

def test_bulk_10000_export(client):
    assert client.post('/api/seed',json={'count':10000}).json()['count']==10000
    state=client.get('/api/state').json()
    assert len(state['records'])==100 and state['count']==10000 and state['external_calls']==0
    assert len(client.get('/api/export').json()['records'])==10000
