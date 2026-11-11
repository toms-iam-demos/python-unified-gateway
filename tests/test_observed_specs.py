"""Use synthetic paths only; private route inventories are not published."""
import copy
import importlib.util
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from gateway.observed_specs import load_observed_spec
from gateway.routers import full_api
from gateway.routers.workflows import operator


def fixture_spec():
    def op(name, params=()):
        return {'operationId':name, 'summary':'Synthetic reference operation',
            'parameters':[{'name':p,'in':'path','required':True,'schema':{'type':'string'}} for p in params],
            'responses':{'default':{'description':'Unknown'}},
            'x-pug-executable':True, 'servers':[{'url':'https://example.invalid'}]}
    return {'openapi':'3.0.3', 'info':{'title':'Synthetic test','version':'1'}, 'paths':{
        '/reference/{itemId}':{'get':op('read_item',['itemId'])},
        '/reference/filters':{'get':op('read_filters')},
        '/reference':{'post':op('create_item')},
    }}


def save(tmp_path, spec):
    p=tmp_path/'private.json';p.write_text(json.dumps(spec));return p


def load_module(monkeypatch, filename):
    monkeypatch.setenv('GATEWAY_OBSERVED_API_SPEC_PATH',str(filename))
    descriptor=importlib.util.spec_from_file_location('isolated_full_api',Path(full_api.__file__))
    module=importlib.util.module_from_spec(descriptor);descriptor.loader.exec_module(module)
    return module


def test_private_catalog_is_registered_but_cannot_enable_execution(monkeypatch,tmp_path):
    api=load_module(monkeypatch,save(tmp_path,fixture_spec()))
    a=FastAPI();api.install(a)
    schema=a.openapi();assert len(api.OPERATIONS)==427
    for path,item in schema['paths'].items():
        if not path.startswith('/docusign/observed/'):continue
        for op in item.values():
            assert op['x-pug-executable'] is False
            assert op['x-pug-source-kind']=='observed-client'
            assert 'official specification' not in op['description']
            assert 'servers' not in op
            assert op['security']==[{'PUGOperator':[]}]
    assert TestClient(a).get('/docusign/observed/reference/filters').status_code==401
    a.dependency_overrides[operator]=lambda:None
    def forbidden(*a,**kw):raise AssertionError('Private reference reached credentials/network')
    monkeypatch.setattr(api,'configuration',forbidden)
    monkeypatch.setattr(api,'token',forbidden)
    monkeypatch.setattr(api.requests,'request',forbidden)
    monkeypatch.setattr(api.requests,'post',forbidden)
    c=TestClient(a)
    for method,path in [('GET','/reference/filters'),('GET','/reference/example'),('POST','/reference')]:
        response=c.request(method,'/docusign/observed'+path,content=b'{}')
        assert response.status_code==403
        assert response.json()['detail']['code']=='operation_locked'
    from starlette.routing import Match
    scope={'type':'http','method':'GET','path':'/docusign/observed/reference/filters','root_path':''}
    route=next(r for r in api.router.routes if r.matches(scope)[0] == Match.FULL)
    assert route.path.endswith('/filters')


def test_missing_private_file_is_not_silently_ignored(tmp_path):
    with pytest.raises(FileNotFoundError):load_observed_spec(tmp_path/'missing.json')


@pytest.mark.parametrize('failure',['query','origin','traversal','missing_parameter','duplicate_id','ambiguous_path','remote_parameter'])
def test_invalid_reference_catalog_is_rejected(tmp_path,failure):
    spec=fixture_spec();paths=spec['paths']
    if failure in {'query','origin','traversal'}:
        bad={'query':'/reference?x=1','origin':'//example.invalid/reference','traversal':'/../reference'}[failure]
        paths[bad]=paths.pop('/reference')
    elif failure=='missing_parameter':paths['/reference/{itemId}']['get']['parameters']=[]
    elif failure=='duplicate_id':paths['/reference']['post']['operationId']='read_filters'
    elif failure=='ambiguous_path':paths['/reference/{otherId}']={'get':copy.deepcopy(paths['/reference/{itemId}']['get'])}
    else:paths['/reference/{itemId}']['get']['parameters']=[{'$ref':'https://example.invalid/parameter'}]
    with pytest.raises(ValueError):load_observed_spec(save(tmp_path,spec))
