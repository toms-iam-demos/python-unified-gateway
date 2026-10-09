import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import bcrypt
import requests
from fastapi.testclient import TestClient
from gateway.app import create_app
from gateway import workflow_client as provider

W = 'a9636563-65dd-499c-98c3-9db6b33e6bd5'
I = '886a8621-4310-438d-ab1d-4ba3d86ebe98'
A = '3376cedc-d0e0-45e9-8e15-7198bc269862'


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file = Path(self.temp.name) / 'htpasswd'
        self.file.write_text('operator:' + bcrypt.hashpw(b'test-password', bcrypt.gensalt(rounds=4)).decode())
        env = {'GATEWAY_WORKFLOWS_ENABLED': '1', 'PUG_OPERATOR_HTPASSWD_FILE': str(self.file),
               'DS_CLIENT_ID': 'test-client', 'DS_IMPERSONATED_USER_GUID': 'test-user',
               'DS_PRIVATE_KEY_PATH': str(Path(self.temp.name) / 'key'), 'DS_AUTH_SERVER': 'account-d.docusign.com',
               'DS_WORKFLOW_ACCOUNT_ID': A}
        p = patch.dict(os.environ, env); p.start(); self.addCleanup(p.stop)
        self.client = TestClient(create_app()); self.addCleanup(self.client.close)
        self.client.auth = ('operator', 'test-password')
        provider._cache.clear()

    def test_missing_and_wrong_auth_never_call_provider(self):
        with patch.object(provider, 'get_json') as call:
            for auth in [None, ('operator', 'wrong'), ('unknown', 'test-password')]:
                r = self.client.get('/docusign/workflows', auth=auth)
                self.assertEqual(r.status_code, 401)
                self.assertIn('Basic', r.headers['www-authenticate'])
            call.assert_not_called()

    def test_missing_auth_configuration_fails_closed(self):
        self.file.unlink()
        with patch.object(provider, 'get_json') as call:
            self.assertEqual(self.client.get('/docusign/workflows').status_code, 503)
            call.assert_not_called()

    def test_empty_list_and_projection(self):
        with patch.object(provider, 'get_json', return_value={'data': []}):
            r = self.client.get('/docusign/workflows')
            self.assertEqual(r.status_code, 200); self.assertEqual(r.json()['data'], [])
            self.assertEqual(r.headers['cache-control'], 'no-store')
        with patch.object(provider, 'get_json', return_value={'data': [{'id': W, 'name': 'Test', 'secret': 'DO_NOT_RETURN'}]}):
            r = self.client.get('/docusign/workflows')
            self.assertEqual(r.json()['data'][0]['id'], W)
            self.assertNotIn('DO_NOT_RETURN', r.text)

    def test_requirements_exclude_launch_link_and_defaults(self):
        data = {'trigger_id': I, 'trigger_event_type': 'HTTP', 'trigger_http_config': {'method': 'GET', 'url': 'SECRET_LAUNCH'},
                'trigger_input_schema': [{'field_name': 'Email', 'field_data_type': 'String', 'default_value': 'PRIVATE_EMAIL'}]}
        with patch.object(provider, 'get_json', return_value=data) as call:
            r = self.client.get(f'/docusign/workflows/{W}/requirements')
            self.assertEqual(r.status_code, 200)
            call.assert_called_once_with(f'/{W}/trigger-requirements')
            self.assertEqual(r.json()['trigger_method'], 'GET')
            self.assertNotIn('SECRET_LAUNCH', r.text); self.assertNotIn('PRIVATE_EMAIL', r.text)

    def test_instances_and_detail_exclude_values(self):
        data = {'id': I, 'template_id': W, 'workflow_status': 'In Progress', 'total_steps': 2,
                'trigger_inputs': {'Email': 'PRIVATE_EMAIL'}, 'started_by_name': 'PRIVATE_PERSON'}
        with patch.object(provider, 'get_json', return_value={'data': [data]}):
            r = self.client.get(f'/docusign/workflows/{W}/instances')
            self.assertEqual(r.status_code, 200); self.assertNotIn('PRIVATE', r.text)
        with patch.object(provider, 'get_json', return_value=data) as call:
            r = self.client.get(f'/docusign/workflows/{W}/instances/{I}')
            self.assertEqual(r.status_code, 200); self.assertEqual(r.json()['trigger_input_names'], ['Email'])
            self.assertNotIn('PRIVATE', r.text)
            call.assert_called_once_with(f'/{W}/instances/{I}')

    def test_invalid_ids_do_not_reach_provider(self):
        with patch.object(provider, 'get_json') as call:
            self.assertEqual(self.client.get('/docusign/workflows/not-a-uuid/requirements').status_code, 422)
            call.assert_not_called()

    def test_invalid_provider_structure_is_sanitized(self):
        with patch.object(provider, 'get_json', return_value={'data': [{'id': 'PRIVATE_INVALID'}]}):
            r = self.client.get('/docusign/workflows')
            self.assertEqual(r.status_code, 502); self.assertNotIn('PRIVATE_INVALID', r.text)

    def test_openapi_has_exactly_four_read_operations_and_auth(self):
        spec = self.client.get('/openapi.json').json()
        routes = {k: v for k, v in spec['paths'].items() if k.startswith('/docusign/workflows')}
        self.assertEqual(len(routes), 4)
        for path in routes.values():
            self.assertEqual(set(path), {'get'})
            self.assertEqual(path['get']['security'], [{'PUGOperator': []}])
        self.assertEqual(spec['components']['securitySchemes']['PUGOperator']['scheme'], 'basic')

    def test_disabled_by_default(self):
        with patch.dict(os.environ, {'GATEWAY_WORKFLOWS_ENABLED': '0'}):
            with TestClient(create_app()) as c:
                self.assertNotIn('/docusign/workflows', c.get('/openapi.json').json()['paths'])

    def test_transport_sanitizes_errors_and_uses_fixed_destination(self):
        with patch.object(provider, 'access_token', return_value='SECRET_TOKEN'), patch.object(provider.requests, 'get') as get:
            for status, expected in [(401, 502), (403, 403), (404, 404), (429, 429), (500, 502), (302, 502)]:
                get.return_value = Mock(status_code=status, headers={'Retry-After': '30'}, text='PRIVATE_BODY')
                r = self.client.get('/docusign/workflows')
                self.assertEqual(r.status_code, expected)
                self.assertNotIn('PRIVATE_BODY', r.text); self.assertNotIn('SECRET_TOKEN', r.text)
                if status == 429: self.assertEqual(r.headers['retry-after'], '30')
            self.assertEqual(get.call_args.args[0], f'https://api-d.docusign.com/v1/accounts/{A}/workflows')
            self.assertFalse(get.call_args.kwargs['allow_redirects'])
            get.side_effect = requests.Timeout('SECRET')
            self.assertEqual(self.client.get('/docusign/workflows').status_code, 504)
            get.side_effect = requests.ConnectionError('SECRET')
            self.assertEqual(self.client.get('/docusign/workflows').status_code, 502)

    def test_consent_error_has_actionable_safe_response(self):
        Path(os.environ['DS_PRIVATE_KEY_PATH']).write_text('FAKE_PRIVATE_KEY')
        r = Mock(status_code=400); r.json.return_value = {'error': 'consent_required', 'private': 'SECRET'}
        with patch.object(provider.jwt, 'encode', return_value='SECRET_ASSERTION'), patch.object(provider.requests, 'post', return_value=r) as post:
            result = self.client.get('/docusign/workflows')
            self.assertEqual(result.status_code, 503)
            self.assertEqual(result.json()['detail']['code'], 'docusign_consent_required')
            self.assertNotIn('SECRET', result.text)
            self.assertFalse(post.call_args.kwargs['allow_redirects'])

    def test_token_cached_and_sandbox_guard(self):
        Path(os.environ['DS_PRIVATE_KEY_PATH']).write_text('FAKE_PRIVATE_KEY')
        r = Mock(status_code=200); r.json.return_value = {'access_token': 'SECRET', 'expires_in': 3600}
        with patch.object(provider.jwt, 'encode', return_value='ASSERTION') as encode, patch.object(provider.requests, 'post', return_value=r) as post:
            config = provider.configuration()
            self.assertEqual(provider.access_token(config), 'SECRET')
            self.assertEqual(provider.access_token(config), 'SECRET')
            post.assert_called_once()
            self.assertEqual(encode.call_args.args[0]['scope'], 'signature impersonation aow_manage')
        with patch.dict(os.environ, {'DS_AUTH_SERVER': 'account.docusign.com'}):
            self.assertEqual(self.client.get('/docusign/workflows').status_code, 503)
