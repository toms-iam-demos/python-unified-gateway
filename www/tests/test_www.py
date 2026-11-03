import base64
import json
import tempfile
import unittest
from pathlib import Path
import bcrypt
from fastapi.testclient import TestClient
from pydantic import ValidationError
from pug_www.app import create_app
from pug_www.models import Profile
from pug_www.settings import Settings

class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.htpasswd = self.root / "operators"
        self.htpasswd.write_text("operator:" + bcrypt.hashpw(b"test-password", bcrypt.gensalt(rounds=4)).decode())
        self.settings = Settings(htpasswd_file=self.htpasswd)
        self.client = TestClient(create_app(self.settings))
        self.headers = {"Authorization": "Basic " + base64.b64encode(b"operator:test-password").decode()}
    def tearDown(self):
        self.tmp.cleanup()
    def test_every_surface_requires_login(self):
        for path in ["/", "/catalog", "/demos", "/demos/data-studio", "/static/www/site.js", "/api/v1/www/catalog", "/brand/unknown"]:
            self.assertEqual(self.client.get(path).status_code, 401, path)
        self.assertEqual(self.client.get("/", auth=("operator", "wrong")).status_code, 401)
    def test_unconfigured_authentication_fails_closed(self):
        client = TestClient(create_app(Settings()))
        self.assertEqual(client.get("/").status_code, 503)
    def test_home_catalog_and_nested_pages_render(self):
        for path in ["/", "/catalog", "/demos", "/catalog/municipal-classification", "/workspaces/mcp", "/demos/data-studio"]:
            response = self.client.get(path, headers=self.headers)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn("Python Unified Gateway", response.text)
        self.assertEqual(self.client.get("/catalog/missing", headers=self.headers).status_code, 404)
        self.assertEqual(self.client.get("/api/missing", headers=self.headers).status_code, 404)
    def test_content_drives_categories_and_cards(self):
        catalog = self.client.get("/api/v1/www/catalog", headers=self.headers).json()["entries"]
        page = self.client.get("/catalog", headers=self.headers).text
        for entry in catalog:
            self.assertIn(entry["title"], page)
            self.assertIn(entry["category"], page)
    def test_external_profile_changes_all_surfaces_and_escapes_content(self):
        file = self.root / "profile.json"
        file.write_text(json.dumps({"name":"Custom Platform","entries":[{"id":"custom-example","title":"<script>unsafe</script>","organization":"EDU","summary":"A private deployment profile.","category":"Education","capability":"Workflow","status":"preview","updated":"2026-11-02"}]}))
        client = TestClient(create_app(Settings(htpasswd_file=self.htpasswd, profile_file=file)))
        for path in ["/", "/catalog", "/catalog/custom-example"]:
            text = client.get(path, headers=self.headers).text
            self.assertIn("Custom Platform", text)
            self.assertNotIn("<script>unsafe</script>", text)
            self.assertIn("&lt;script&gt;unsafe&lt;/script&gt;", text)
    def test_private_asset_allowlist_and_traversal(self):
        assets = self.root / "assets"; assets.mkdir()
        (assets / "logo.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
        secret = self.root / "secret.svg"; secret.write_text("private")
        file = self.root / "profile.json"
        file.write_text(json.dumps({"assets":{"product":"logo.svg","escape":"../secret.svg"}}))
        client = TestClient(create_app(Settings(htpasswd_file=self.htpasswd, profile_file=file, asset_directory=assets)))
        self.assertEqual(client.get("/brand/product", headers=self.headers).status_code, 200)
        self.assertEqual(client.get("/brand/escape", headers=self.headers).status_code, 404)
        self.assertEqual(client.get("/brand/unlisted", headers=self.headers).status_code, 404)
    def test_unsafe_links_and_duplicate_catalog_ids_are_rejected(self):
        entry = {"id":"example","title":"Example","organization":"NFP","summary":"Review","category":"Operations","capability":"Workflow","status":"preview","updated":"2026-11-02"}
        with self.assertRaises(ValidationError):
            Profile.model_validate({"entries":[{**entry,"launch_url":"javascript:alert(1)"}]})
        with self.assertRaises(ValidationError):
            Profile.model_validate({"entries":[entry,entry]})
    def test_security_headers_and_no_provider_writes(self):
        response = self.client.get("/catalog", headers=self.headers)
        self.assertIn("frame-ancestors 'none'", response.headers["content-security-policy"])
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(self.client.post("/catalog", headers=self.headers).status_code, 405)
        self.assertEqual(self.client.get("/openapi.json", headers=self.headers).status_code, 404)
        self.assertEqual(self.client.get("/", headers={**self.headers,"Host":"untrusted.example"}).status_code, 400)
    def test_product_copy_contains_no_em_dash(self):
        import pug_www
        root = Path(pug_www.__file__).parent
        for path in root.rglob("*"):
            if path.suffix in {".py", ".js", ".css", ".html", ".json"}:
                text = path.read_text()
                for token in ["\u2014", "&mdash;", "&#8212;", "&#x2014;"]:
                    self.assertNotIn(token, text, str(path))

if __name__ == "__main__":
    unittest.main()
