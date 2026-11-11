"""Load an operator-supplied private reference catalog, without provider I/O."""
from __future__ import annotations

import json
from pathlib import Path
import re

METHODS = {'get', 'post', 'put', 'patch', 'delete', 'head', 'options'}
PLACEHOLDER = re.compile(r'\{([A-Za-z_][A-Za-z_0-9]*)\}')
MAX_BYTES = 10 * 1024 * 1024


def load_observed_spec(filename):
    """Fail clearly when an explicitly configured catalog is invalid.

    The file remains outside source control. Neither URLs nor environment values
    in this document configure a transport, token, or execution allowlist.
    """
    with Path(filename).open('rb') as source:
        data = source.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('Observed API catalog exceeds the 10 MiB limit')
    spec = json.loads(data)
    if not isinstance(spec, dict) or not str(spec.get('openapi', '')).startswith('3.'):
        raise ValueError('Observed API catalog must be OpenAPI 3')
    paths = spec.get('paths')
    if not isinstance(paths, dict) or not paths:
        raise ValueError('Observed API catalog requires paths')
    ids, templates = set(), set()
    for path, item in paths.items():
        if (not path.startswith('/') or path.startswith('//') or
                any(c in path for c in ('?', '#', '%', '\\', '\n', '\r')) or
                any(part in ('.', '..') for part in path.split('/'))):
            raise ValueError('Observed API catalog requires plain relative path templates')
        names = PLACEHOLDER.findall(path)
        stripped = PLACEHOLDER.sub('{}', path)
        if '{' in stripped.replace('{}', '') or '}' in stripped.replace('{}', ''):
            raise ValueError('Invalid path parameter name')
        if stripped in templates or len(names) != len(set(names)):
            raise ValueError('Ambiguous observed path template')
        templates.add(stripped)
        if not isinstance(item, dict) or not any(m in METHODS for m in item):
            raise ValueError('Observed path requires an HTTP operation')
        for method, op in item.items():
            if method not in METHODS:
                continue
            if not isinstance(op, dict) or not isinstance(op.get('operationId'), str) or not op['operationId']:
                raise ValueError('Observed operation requires operationId')
            if op['operationId'] in ids:
                raise ValueError('Duplicate observed operationId')
            ids.add(op['operationId'])
            # Inline parameters make incomplete contracts reviewable. Do not
            # resolve remote parameter references or retrieve any schema URL.
            params = item.get('parameters', []) + op.get('parameters', [])
            if any(not isinstance(p, dict) or '$ref' in p for p in params):
                raise ValueError('Observed parameters must be inline')
            actual = {p['name'] for p in params if p.get('in') == 'path' and p.get('required') is True}
            if actual != set(names):
                raise ValueError('Observed path parameters must be declared and required')
            op['x-pug-source-kind'] = 'observed-client'
            # Source assertions never enable execution. Registration overwrites
            # the execution extension with PUG's server policy result.
    return spec
