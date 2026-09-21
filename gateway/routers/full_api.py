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
    'agreement-manager': ('https://api-d.docusign.com', 'signature impersonation adm_store_unified_repo_read adm_store_unified_repo_write models_read document_uploader_read document_uploader_write public_dms_document_read'),
}
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
        'Executing POST, PUT, PATCH or DELETE can change provider state, send messages, or remove data.\n\n' + op.get('description', ''))
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
    for param in op.get('parameters', []):
        if param.get('in') == 'path' and param.get('name') == 'accountId':
            param.setdefault('schema', {})['default'] = os.getenv('DS_WORKFLOW_ACCOUNT_ID', '')
    op.pop('servers', None)
    return op


def handler(product, path, method, operation):
    async def forward(request: Request):
        from starlette.concurrency import run_in_threadpool
        cfg = configuration()
        resolved = path
        for name, value in request.path_params.items():
            if name == 'accountId' and value != cfg['DS_WORKFLOW_ACCOUNT_ID']:
                raise HTTPException(403, 'Only the configured sandbox account is allowed.')
            if not value or value in ('.', '..') or any(c in value for c in '/\\%?#'):
                raise HTTPException(422, 'Invalid path identifier.')
            resolved = resolved.replace('{' + name + '}', quote(value, safe=''))
        # Bound uploads before buffering; streamed bodies without Content-Length are bounded too.
        limit = 35 * 1024 * 1024
        chunks = []; size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > limit: raise HTTPException(413, 'Request exceeds the 35 MiB gateway limit.')
            chunks.append(chunk)
        body = b''.join(chunks)
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
            OPERATIONS.append({'product':product,'method':method.upper(),'path':local_path,'operation_id':op['operationId'],'verification':'not_live_tested'})


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
