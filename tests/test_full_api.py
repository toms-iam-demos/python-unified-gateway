from fastapi import FastAPI
from fastapi.testclient import TestClient
from gateway.routers import full_api as api
from gateway.routers.workflows import operator
ACCOUNT='3376cedc-d0e0-45e9-8e15-7198bc269862'
def app(auth=True):
    a=FastAPI();api.install(a)
    if auth:a.dependency_overrides[operator]=lambda:None
    return a

def test_exact_operation_coverage_and_refs():
    schema=app().openapi()
    ops=[(p,m,o) for p,v in schema['paths'].items() for m,o in v.items() if m in api.METHODS]
    assert len(ops)==424
    assert len({o['operationId'] for p,m,o in ops})==424
    def check(x):
        if isinstance(x,dict):
            if '$ref' in x:
                ref=x['$ref'];assert ref.startswith('#/')
                cur=schema
                for part in ref[2:].split('/'):cur=cur[part.replace('~1','/').replace('~0','~')]
            for v in x.values():check(v)
        elif isinstance(x,list):
            for v in x:check(v)
    check(schema)
    for p,m,o in ops:
        assert o['security']==[{'PUGOperator':[]}]
        assert 'not individually live-tested' in o['description']

def test_all_routes_require_authentication():
    c=TestClient(app(False))
    for op in api.OPERATIONS:
        import re
        p=re.sub(r'\{[^}]+\}', 'example',op['path'])
        r=c.request(op['method'],p)
        assert r.status_code==401,(op,r.status_code)

def test_wrong_account_cannot_reach_provider(monkeypatch):
    monkeypatch.setattr(api,'configuration',lambda:{'DS_WORKFLOW_ACCOUNT_ID':ACCOUNT})
    monkeypatch.setattr(api,'token',lambda p: (_ for _ in ()).throw(AssertionError('Provider called')))
    r=TestClient(app()).get('/docusign/esignature/v2.1/accounts/other/templates')
    assert r.status_code==403

class Upstream:
    status_code=200
    headers={'content-type':'application/json','set-cookie':'secret','x-docusign-tracetoken':'trace'}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_content(self,*args):yield b'{"ok":true}'

def test_forward_method_body_queries_and_secret_isolation(monkeypatch):
    monkeypatch.setattr(api,'configuration',lambda:{'DS_WORKFLOW_ACCOUNT_ID':ACCOUNT})
    monkeypatch.setattr(api,'token',lambda p:'provider-token')
    calls=[]
    monkeypatch.setattr(api.requests,'request',lambda *a,**kw: calls.append((a,kw)) or Upstream())
    c=TestClient(app())
    for method,path,body in [('GET','templates',b'')]:
        r=c.request(method,f'/docusign/esignature/v2.1/accounts/{ACCOUNT}/{path}?count=1&count=2',content=body,headers={'Authorization':'Basic operator-secret','content-type':'application/json'})
        assert r.status_code==200
        a,kw=calls[-1];assert a[0]==method
        assert a[1].startswith('https://demo.docusign.net/restapi/v2.1/accounts/'+ACCOUNT)
        assert kw['headers']['Authorization']=='Bearer provider-token'
        assert kw['params']==[('count','1'),('count','2')]
        assert kw['data']==body and kw['allow_redirects'] is False
        assert 'set-cookie' not in r.headers and r.headers['cache-control']=='no-store'

def test_redirects_blocked_and_unknown_routes_absent(monkeypatch):
    monkeypatch.setattr(api,'configuration',lambda:{'DS_WORKFLOW_ACCOUNT_ID':ACCOUNT})
    monkeypatch.setattr(api,'token',lambda p:'t')
    class Redirect(Upstream):status_code=302
    monkeypatch.setattr(api.requests,'request',lambda *a,**kw:Redirect())
    c=TestClient(app())
    assert c.get(f'/docusign/esignature/v2.1/accounts/{ACCOUNT}/templates').status_code==502
    assert c.get('/docusign/esignature/arbitrary').status_code==404

def test_encoded_path_escape_cannot_reach_provider(monkeypatch):
    monkeypatch.setattr(api,'configuration',lambda:{'DS_WORKFLOW_ACCOUNT_ID':ACCOUNT})
    monkeypatch.setattr(api,'token',lambda p: (_ for _ in ()).throw(AssertionError('Provider called')))
    c=TestClient(app())
    for value in ['%252e%252e','%253fquery','%255cescape']:
        assert c.get(f'/docusign/agreement-manager/v1/accounts/{ACCOUNT}/agreements/{value}').status_code==422

def test_agreement_manager_uses_separate_host(monkeypatch):
    monkeypatch.setattr(api,'configuration',lambda:{'DS_WORKFLOW_ACCOUNT_ID':ACCOUNT})
    seen=[]
    monkeypatch.setattr(api,'token',lambda p:seen.append(p) or 'token')
    calls=[]
    monkeypatch.setattr(api.requests,'request',lambda *a,**kw:calls.append((a,kw)) or Upstream())
    r=TestClient(app()).get(f'/docusign/agreement-manager/v1/accounts/{ACCOUNT}/agreements')
    assert r.status_code==200
    assert seen==['agreement-manager']
    assert calls[0][0][1]==f'https://api-d.docusign.com/v1/accounts/{ACCOUNT}/agreements'

def test_every_locked_operation_stops_before_configuration_or_network(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Locked operation reached credentials or network')
    monkeypatch.setattr(api,'configuration',forbidden)
    monkeypatch.setattr(api,'token',forbidden)
    monkeypatch.setattr(api.requests,'request',forbidden)
    monkeypatch.setattr(api.requests,'post',forbidden)
    import re
    c=TestClient(app())
    blocked=0
    for op in api.OPERATIONS:
        if op['executable']:continue
        p=re.sub(r'\{[^}]+\}', 'example',op['path'])
        r=c.request(op['method'],p,content=b'{"status":"sent"}')
        assert r.status_code==403,(op,r.status_code)
        assert r.json()['detail']['code']=='operation_locked'
        blocked+=1
    assert blocked==417
    assert sum(op['executable'] for op in api.OPERATIONS)==7
    assert all(op['method']=='GET' for op in api.OPERATIONS if op['executable'])

def test_read_routes_reject_method_overrides_unknown_queries_and_bodies(monkeypatch):
    monkeypatch.setattr(api,'configuration',lambda:{'DS_WORKFLOW_ACCOUNT_ID':ACCOUNT})
    def forbidden(*args,**kwargs):raise AssertionError('Invalid input reached provider')
    monkeypatch.setattr(api,'token',forbidden)
    c=TestClient(app());path=f'/docusign/esignature/v2.1/accounts/{ACCOUNT}/templates'
    for header in ['X-HTTP-Method-Override','X-Method-Override','X-HTTP-Method']:
        assert c.get(path,headers={header:'DELETE'}).status_code==400
    for query in ['_method=DELETE','method=DELETE','url=https://example.com']:
        assert c.get(path+'?'+query).status_code==422
    assert c.request('GET',path,content=b'{"status":"sent"}').status_code==400

def test_swagger_marks_locked_operations_and_no_write_scopes():
    schema=app().openapi()
    for p,v in schema['paths'].items():
        for method,op in v.items():
            if method not in api.METHODS:continue
            if not op['x-pug-executable']:
                assert op['summary'].startswith('[LOCKED]')
                assert '403' in op['responses']
    scopes=api.PRODUCTS['agreement-manager'][1].split()
    assert not any('write' in scope for scope in scopes)
    assert 'public_dms_document_read' not in scopes

def test_jwt_diagnostic_requires_operator_login(monkeypatch):
    from gateway.app import create_app
    c=TestClient(create_app())
    assert c.get('/docusign/jwt-test').status_code==401
    doc=c.get('/docs').text
    assert '"supportedSubmitMethods": ["get"]' in doc
    assert '"persistAuthorization": false' in doc
