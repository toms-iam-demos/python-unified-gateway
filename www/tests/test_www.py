import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import bcrypt
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pug_www.app import create_app
from pug_www.models import Profile
from pug_www.settings import Settings
from pug_www import presentations

EXAMPLE = {"uid":"ff1e215e-57cf-5734-8ddb-b604b73725aa","id":"ex-000042","example_code":"EX-000042","business_process":"Provider agreement management","scenario":"Reimbursement amendment review","summary":"Inspect a controlling source.","industries":["Healthcare"],"capabilities":["Iris"],"status":"preview","updated":"2026-11-02"}

class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.htpasswd = self.root / "operators"
        self.htpasswd.write_text("operator:" + bcrypt.hashpw(b"test-password", bcrypt.gensalt(rounds=4)).decode())
        self.client = TestClient(create_app(Settings(htpasswd_file=self.htpasswd)))
        self.headers = {"Authorization":"Basic " + base64.b64encode(b"operator:test-password").decode()}
    def tearDown(self):
        self.tmp.cleanup()
    def custom(self, content, **settings):
        path = self.root / "profile.json"; path.write_text(json.dumps(content))
        return TestClient(create_app(Settings(htpasswd_file=self.htpasswd, profile_file=path, **settings)))
    def test_every_surface_requires_login(self):
        for path in ["/", "/catalog", "/demos", "/demos/data-studio", "/demos/ex-000042/", "/static/www/site.js", "/api/v1/www/catalog", "/brand/unknown", "/api/demos/ex-000042/runtime/replay"]:
            self.assertEqual(self.client.get(path).status_code, 401, path)
        self.assertEqual(self.client.get("/", auth=("operator","wrong")).status_code, 401)
    def test_authentication_fails_closed(self):
        self.assertEqual(TestClient(create_app(Settings())).get("/").status_code, 503)
    def test_pages_and_example_sections_render(self):
        for path in ["/", "/catalog", "/demos", "/demos/ex-000042/", "/demos/ex-000042/runs/", "/demos/ex-000042/materials/", "/demos/ex-000042/implementation/", "/workspaces/mcp", "/demos/data-studio"]:
            response = self.client.get(path, headers=self.headers)
            self.assertEqual(response.status_code, 200, path)
        self.assertEqual(self.client.get("/catalog/missing", headers=self.headers).status_code, 404)
        self.assertEqual(self.client.get("/api/missing", headers=self.headers).status_code, 404)
    def test_registry_drives_processes_filters_and_identity(self):
        data = self.client.get("/api/v1/www/catalog", headers=self.headers).json()
        self.assertEqual(data["schema_version"], 2)
        page = self.client.get("/catalog", headers=self.headers).text
        for entry in data["entries"]:
            for field in ["scenario", "business_process"]:
                self.assertIn(entry[field], page)
        codes = {e["example_code"]:e["uid"] for e in data["entries"] if e["example_code"]}
        self.assertEqual(codes["EX-000042"], "ff1e215e-57cf-5734-8ddb-b604b73725aa")
        self.assertEqual(codes["EX-000043"], "15e6b74c-8af3-4990-9041-cf492ad29833")
        self.assertEqual(codes["EX-000044"], "56cc1737-3eff-4b30-a82f-086e6d904446")
    def test_legacy_alias_resolves_to_canonical_example(self):
        response = self.client.get("/catalog/provider-agreement-hierarchy?session=reference", headers=self.headers, follow_redirects=False)
        self.assertEqual(response.status_code, 307)
        self.assertEqual(response.headers["location"], "/demos/ex-000042/?session=reference")
        self.assertEqual(self.client.get("/demos/EX-000042/", headers=self.headers, follow_redirects=False).headers["location"], "/demos/ex-000042/")
    def test_profile_branding_does_not_change_example_identity(self):
        entry = {**EXAMPLE,"scenario":"<script>unsafe</script>","organization_profile":"healthcare"}
        client = self.custom({"name":"Custom Platform","organizations":{"healthcare":{"name":"EDU"}},"entries":[entry]})
        page = client.get("/demos/ex-000042/", headers=self.headers).text
        self.assertIn("Custom Platform",page);self.assertIn("EDU",page)
        self.assertNotIn("<script>unsafe</script>",page)
        self.assertIn("&lt;script&gt;unsafe&lt;/script&gt;",page)
        self.assertIn(EXAMPLE["uid"],page)
    def test_identity_alias_and_profile_validation(self):
        for value in [
            {"entries":[{**EXAMPLE,"id":"customer-name"}]},
            {"entries":[EXAMPLE,EXAMPLE]},
            {"entries":[{**EXAMPLE,"organization_profile":"missing"}]},
            {"entries":[{**EXAMPLE,"experiences":{"presentation":"javascript:alert(1)"}}]},
        ]:
            with self.assertRaises(ValidationError):Profile.model_validate(value)
        with self.assertRaises(ValueError):
            self.custom({"entries":[{**EXAMPLE,"business_process":"Uncontrolled label"}]})
    def test_asset_allowlist_prevents_path_escape(self):
        folder=self.root/"assets";folder.mkdir();(folder/"logo.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>');(self.root/"secret.svg").write_text("private")
        client=self.custom({"assets":{"product":"logo.svg","escape":"../secret.svg"}},asset_directory=folder)
        self.assertEqual(client.get("/brand/product",headers=self.headers).status_code,200)
        self.assertEqual(client.get("/brand/escape",headers=self.headers).status_code,404)
        self.assertEqual(client.get("/brand/unlisted",headers=self.headers).status_code,404)
    def test_presentation_preserves_style_with_canonical_routes(self):
        (self.root/"presentation.html").write_text('<html><body class="original"><a href="/summit/profile">Original</a><link href="/assets/summit/presentation.css"></body></html>')
        (self.root/"presentation.css").write_text(':root{--violet:#5424f5}body{background:#f6f3fa}')
        profile={"entries":[EXAMPLE],"presentations":{"ex-000042":{"html_file":"presentation.html","runtime_namespace":"profile","assets":{"presentation.css":"presentation.css"}}}}
        client=self.custom(profile,presentation_directory=self.root)
        page=client.get("/demos/ex-000042/presentation/",headers=self.headers)
        self.assertEqual(page.status_code,200)
        self.assertIn('class="original"',page.text)
        self.assertIn('data-runtime-namespace="profile"',page.text)
        self.assertIn('/demos/ex-000042/assets/presentation.css',page.text)
        self.assertNotIn('/static/www/theme.css',page.text)
        css=client.get('/demos/ex-000042/assets/presentation.css',headers=self.headers)
        self.assertEqual(css.text,':root{--violet:#5424f5}body{background:#f6f3fa}')
        self.assertEqual(client.get('/demos/ex-000042/assets/unknown.pdf',headers=self.headers).status_code,404)
    def test_preview_commands_never_reach_provider(self):
        with patch.object(presentations.httpx,'AsyncClient') as transport:
            response=self.client.post('/api/demos/ex-000042/runtime/sessions/any/commands',headers=self.headers,json={"action":"reset"})
            self.assertEqual(response.status_code,403);transport.assert_not_called()
    def test_security_headers_and_unknown_routes(self):
        response=self.client.get('/catalog',headers=self.headers)
        self.assertIn("frame-ancestors 'none'",response.headers['content-security-policy'])
        self.assertEqual(response.headers['cache-control'],'no-store')
        self.assertEqual(self.client.post('/catalog',headers=self.headers).status_code,405)
        self.assertEqual(self.client.get('/openapi.json',headers=self.headers).status_code,404)
        self.assertEqual(self.client.get('/',headers={**self.headers,'Host':'untrusted.example'}).status_code,400)
    def test_home_is_root_and_legacy_overview_returns_to_root(self):
        response=self.client.get('/',headers=self.headers)
        self.assertIn('Every agreement.',response.text)
        self.assertIn('class="hero-geometry"',response.text)
        self.assertIn('href="/"',response.text)
        redirect=self.client.get('/catalog?area=overview',headers=self.headers,follow_redirects=False)
        self.assertEqual(redirect.headers['location'],'/')
    def test_app_center_placeholders_and_connected_stripe_boundary(self):
        from html.parser import HTMLParser
        class Cards(HTMLParser):
            def __init__(self):super().__init__();self.disabled=0;self.links=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if a.get('aria-disabled')=='true':self.disabled+=1
                if tag=='a':self.links.append(a.get('href',''))
        response=self.client.get('/catalog?area=extensions',headers=self.headers)
        cards=Cards();cards.feed(response.text)
        self.assertEqual(cards.disabled,104)
        self.assertIn('Zendesk',response.text);self.assertIn('HubSpot',response.text)
        self.assertNotIn('Microsoft',response.text)
        entry={**EXAMPLE,'id':'stripe-consulting-deposit','example_code':None,'availability':'hosted'}
        client=self.custom({'entries':[entry]})
        cards=Cards();cards.feed(client.get('/catalog?area=extensions',headers=self.headers).text)
        self.assertEqual(cards.disabled,103)
        self.assertIn('/demos/stripe-consulting-deposit/',cards.links)
    def test_invitation_is_single_example_draft_with_no_send_endpoint(self):
        response=self.client.get('/catalog?area=workups',headers=self.headers)
        self.assertIn('Invite someone',response.text)
        self.assertIn('value="/demos/ex-000042/"',response.text)
        self.assertIn('does not grant access or send an email',response.text)
        self.assertNotIn('Signed. Paid.',response.text)
        self.assertEqual(self.client.post('/catalog?area=workups',headers=self.headers,json={'email':'guest@example.com'}).status_code,405)
    def test_product_copy_contains_no_em_dash(self):
        import pug_www
        for path in Path(pug_www.__file__).parent.rglob('*'):
            if path.suffix in {'.py','.js','.css','.html','.json'}:
                for token in ['\u2014','&mdash;','&#8212;','&#x2014;']:
                    self.assertNotIn(token,path.read_text(),str(path))

if __name__ == '__main__':unittest.main()
