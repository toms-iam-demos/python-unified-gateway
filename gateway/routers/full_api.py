"""Pinned, operator-authenticated sandbox API surface; no arbitrary URL proxying.

Provider operations are registered individually from the committed specifications.
Registration is not evidence of provider entitlement or successful execution.
"""
from __future__ import annotations

import copy
import json
import os
import re
import threading
import time
from pathlib import Path
from urllib.parse import quote

import jwt
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from gateway.routers.workflows import operator
from gateway.workflow_client import configuration

SPEC_DIR = Path(__file__).resolve().parents[1] / 'api_specs'
METHODS = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}
PRODUCTS = {
    'esignature': ('https://demo.docusign.net/restapi', 'signature impersonation'),
    'agreement-manager': ('https://api-d.docusign.com', 'signature impersonation adm_store_unified_repo_read'),
}
# Deliberately code-reviewed, not environment/user configurable. New spec entries
# are denied automatically. A GET verb alone does not establish safe semantics.
ALLOWED_READS = frozenset({
    ('esignature', '/v2.1/accounts/{accountId}/templates'),
    ('esignature', '/v2.1/accounts/{accountId}/envelopes'),
    ('esignature', '/v2.1/accounts/{accountId}/identity_verification'),
    ('agreement-manager', '/v1/accounts/{accountId}/agreements'),
    ('agreement-manager', '/v1/accounts/{accountId}/agreements/{agreementId}'),
    ('agreement-manager', '/v1/accounts/{accountId}/agreement-types'),
})


def is_allowed(product, path, method):
    return method.lower() == 'get' and (product, path) in ALLOWED_READS


def enforce_policy(product, path, method):
    if not is_allowed(product, path, method):
        raise HTTPException(403, {'code': 'operation_locked',
            'message': 'Reference only. This operation is disabled by PUG server policy.'},
            headers={'Cache-Control': 'no-store'})


router = APIRouter(dependencies=[Depends(operator)])
_cache = {}
_lock = threading.Lock()


def token(product):
    cfg = configuration()
    scopes = PRODUCTS[product][1]
    key = (product, tuple(cfg.items()), scopes)
    with _lock:
        cached = _cache.get(key)
        if cached and cached[1] > time.monotonic():
            return cached[0]
        now = int(time.time())
        try:
            assertion = jwt.encode({'iss': cfg['DS_CLIENT_ID'], 'sub': cfg['DS_IMPERSONATED_USER_GUID'],
                'aud': 'account-d.docusign.com', 'iat': now, 'exp': now + 300, 'scope': scopes},
                Path(cfg['DS_PRIVATE_KEY_PATH']).read_text(), algorithm='RS256')
            r = requests.post('https://account-d.docusign.com/oauth/token', data={
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer', 'assertion': assertion},
                timeout=(5, 25), allow_redirects=False)
            data = r.json()
        except (OSError, ValueError, requests.RequestException):
            raise HTTPException(502, 'Could not authenticate with the sandbox provider.')
        if r.status_code != 200 or not isinstance(data.get('access_token'), str):
            if data.get('error') == 'consent_required':
                raise HTTPException(503, {'code': 'docusign_consent_required', 'scopes': scopes})
            raise HTTPException(502, 'Sandbox authentication failed.')
        _cache[key] = (data['access_token'], time.monotonic() + max(0, min(float(data.get('expires_in', 3600)), 3600) - 60))
        return data['access_token']


def normalize(value, product):
    """Namespace provider schema refs and translate Swagger 2 file schemas."""
    if isinstance(value, list):
        return [normalize(v, product) for v in value]
    if not isinstance(value, dict):
        return value
    result = {k: normalize(v, product) for k, v in value.items()}
    ref = result.get('$ref', '')
    if ref.startswith('#/definitions/'):
        result['$ref'] = '#/components/schemas/' + product + '_' + ref.split('/')[-1]
    elif ref.startswith('#/components/') and not ref.split('/')[-1].startswith(product + '_'):
        result['$ref'] = ref.rsplit('/', 1)[0] + '/' + product + '_' + ref.split('/')[-1]
    if result.get('type') == 'file':
        result.update(type='string', format='binary')
    return result


def operation_schema(spec, path, method, product):
    op = normalize(copy.deepcopy(spec['paths'][path][method]), product)
    op['operationId'] = product.replace('-', '_') + '_' + op.get('operationId', method + path)
    op['tags'] = ['docusign ' + product + ' · ' + t for t in op.get('tags', ['API'])]
    op.pop('security', None)  # FastAPI adds the operator dependency's scheme.
    op['description'] = ('Sandbox provider operation. Registered from the official specification; not individually live-tested. '
        'Account paths are restricted to the configured PUG sandbox account. '
        'Only explicitly allowlisted reads can execute. All other operations are locked.\n\n' + op.get('description', ''))
    if spec.get('swagger') == '2.0':
        parameters, forms = [], {}
        form_required = []
        for p in spec['paths'][path].get('parameters', []) + op.get('parameters', []):
            p = normalize(copy.deepcopy(p), product)
            if p.get('in') == 'body':
                op['requestBody'] = {'required': p.get('required', False), 'content': {c: {'schema': p.get('schema', {})} for c in op.get('consumes') or ['application/json']}}
            elif p.get('in') == 'formData':
                forms[p['name']] = {k: v for k, v in p.items() if k in ('type','format','items','enum','default','description')}
                if p.get('required'): form_required.append(p['name'])
            else:
                schema = {k: p.pop(k) for k in list(p) if k in ('type','format','items','enum','default','minimum','maximum','pattern','minLength','maxLength')}
                if schema: p['schema'] = schema
                collection = p.pop('collectionFormat', None)
                if collection:
                    p.update(style={'ssv':'spaceDelimited','pipes':'pipeDelimited'}.get(collection,'form'), explode=collection=='multi')
                parameters.append(p)
        op['parameters'] = parameters
        if forms:
            op['requestBody'] = {'content': {c: {'schema': {'type':'object','properties':forms,'required':form_required}} for c in op.get('consumes') or ['multipart/form-data']}}
        for response in op.get('responses', {}).values():
            if 'schema' in response:
                schema = response.pop('schema')
                response['content'] = {c: {'schema':schema} for c in op.get('produces') or ['application/json']}
        op.pop('consumes', None); op.pop('produces', None)
    if spec.get('swagger') != '2.0':
        # OpenAPI path-item parameters are inherited by every operation. Resolve
        # reusable parameters here so Swagger can render the account selector.
        merged = {}
        params = normalize(copy.deepcopy(spec['paths'][path].get('parameters', [])), product) + op.get('parameters', [])
        for param in params:
            if '$ref' in param:
                name = param['$ref'].split('/')[-1].removeprefix(product + '_')
                param = normalize(copy.deepcopy(spec['components']['parameters'][name]), product)
            merged[(param['in'], param['name'])] = param
        op['parameters'] = list(merged.values())
    for param in op.get('parameters', []):
        if param.get('in') == 'path' and param.get('name') == 'accountId':
            param.setdefault('schema', {})['default'] = os.getenv('DS_WORKFLOW_ACCOUNT_ID', '')
    op.pop('servers', None)
    allowed = is_allowed(product, path, method)
    op['x-pug-executable'] = allowed
    op['description'] = ('READ-ONLY: enabled for authenticated operators. ' if allowed else
        'LOCKED: reference only. The server rejects this operation before credentials or provider calls. ') + op['description']
    if not allowed:
        op['summary'] = '[LOCKED] ' + op.get('summary', op['operationId'])
        op.setdefault('responses', {})['403'] = {'description': 'Operation disabled by PUG server policy.'}
    return op


def handler(product, path, method, operation):
    async def forward(request: Request):
        enforce_policy(product, path, method)
        from starlette.concurrency import run_in_threadpool
        if request.method.lower() != method.lower():
            raise HTTPException(405, 'Method mismatch.')
        if any(h.lower() in ('x-http-method-override', 'x-method-override', 'x-http-method') for h in request.headers):
            raise HTTPException(400, 'Method override headers are not supported.')
        allowed_query = {p['name'] for p in operation.get('parameters', []) if p.get('in') == 'query'}
        # Agreement Manager can use reusable parameter definitions.
        for p in operation.get('parameters', []):
            if '$ref' in p:
                param = COMPONENTS.get('parameters', {}).get(p['$ref'].split('/')[-1], {})
                if param.get('in') == 'query': allowed_query.add(param['name'])
        if any(name not in allowed_query for name in request.query_params):
            raise HTTPException(422, 'Unsupported query parameter.')
        cfg = configuration()
        resolved = path
        for name, value in request.path_params.items():
            if name == 'accountId' and value != cfg['DS_WORKFLOW_ACCOUNT_ID']:
                raise HTTPException(403, 'Only the configured sandbox account is allowed.')
            if not value or value in ('.', '..') or any(c in value for c in '/\\%?#'):
                raise HTTPException(422, 'Invalid path identifier.')
            resolved = resolved.replace('{' + name + '}', quote(value, safe=''))
        # No request payloads are accepted on this read-only surface.
        async for chunk in request.stream():
            if chunk:
                raise HTTPException(400, 'Request bodies are not accepted on read-only operations.')
        body = b''
        def call():
            headers = {'Authorization': 'Bearer ' + token(product), 'Accept': request.headers.get('accept', 'application/json')}
            if request.headers.get('content-type'): headers['Content-Type'] = request.headers['content-type']
            try:
                upstream = requests.request(method.upper(), PRODUCTS[product][0] + resolved,
                    params=list(request.query_params.multi_items()), data=body, headers=headers,
                    timeout=(5, 60), allow_redirects=False, stream=True)
                with upstream:
                    parts = []; total = 0
                    for part in upstream.iter_content(65536):
                        total += len(part)
                        if total > 50 * 1024 * 1024: raise HTTPException(502, 'Provider response exceeds the 50 MiB gateway limit.')
                        parts.append(part)
                    if 300 <= upstream.status_code < 400:
                        raise HTTPException(502, 'Provider redirect was not followed.')
                    if upstream.status_code == 401:
                        with _lock: _cache.clear()
                    safe_headers = {'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'}
                    for key in ('content-type','content-disposition','retry-after','x-docusign-tracetoken'):
                        if key in upstream.headers: safe_headers[key] = upstream.headers[key]
                    return Response(b''.join(parts), status_code=upstream.status_code, headers=safe_headers)
            except requests.Timeout:
                raise HTTPException(504, 'Sandbox provider timed out; a write may have succeeded. Check its state before retrying.')
            except requests.RequestException:
                raise HTTPException(502, 'Sandbox provider connection failed; check state before retrying a write.')
        return await run_in_threadpool(call)
    forward.__name__ = operation['operationId']
    return forward


SCHEMAS = {}
COMPONENTS = {}
OPERATIONS = []
for product in PRODUCTS:
    spec = json.loads((SPEC_DIR / (product + '.json')).read_text())
    definitions = spec.get('definitions', spec.get('components', {}).get('schemas', {}))
    SCHEMAS.update({product + '_' + k: normalize(v, product) for k, v in definitions.items()})
    for kind, entries in spec.get('components', {}).items():
        if kind in ('schemas', 'securitySchemes'): continue
        COMPONENTS.setdefault(kind, {}).update({product + '_' + k: normalize(v, product) for k, v in entries.items()})
    for path, item in spec['paths'].items():
        for method in item:
            if method not in METHODS: continue
            op = operation_schema(spec, path, method, product)
            local_path = '/docusign/' + product + path
            router.add_api_route(local_path, handler(product, path, method, op), methods=[method.upper()],
                response_class=Response, openapi_extra=op)
            OPERATIONS.append({'product':product,'method':method.upper(),'path':local_path,'operation_id':op['operationId'],'verification':'not_live_tested','executable':is_allowed(product,path,method)})


def install(app):
    app.include_router(router)
    original = app.openapi
    def openapi():
        schema = original()
        schema.setdefault('components', {}).setdefault('schemas', {}).update(SCHEMAS)
        for kind, entries in COMPONENTS.items():
            schema['components'].setdefault(kind, {}).update(entries)
        return schema
    app.openapi = openapi
