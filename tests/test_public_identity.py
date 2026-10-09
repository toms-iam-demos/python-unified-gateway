import hashlib
import struct
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("identity_guard", Path(__file__).resolve().parents[1] / "tools/check_public_identity.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class PublicationIdentityTests(unittest.TestCase):
    def setUp(self):
        self.blocked = {hashlib.sha256(b"sample institution").hexdigest()}

    def test_text_filename_and_encoded_variants(self):
        for text in ["Sample Institution", "assets/sample-institution/logo.svg", "SAMPLE_INSTITUTION", "sample%20institution", "sample&#32;institution"]:
            with self.subTest(text=text):
                self.assertTrue(guard.has_identity(text, self.blocked))

    def test_technical_names_and_generic_profiles_are_allowed(self):
        self.assertFalse(guard.has_identity("PUG docusign Oracle NFP Museum Municipal EDU", self.blocked))

    def test_near_match_is_not_blocked(self):
        self.assertFalse(guard.has_identity("sample institutional", self.blocked))

    def test_utf16_font_metadata_is_scanned(self):
        raw = "Sample Institution".encode("utf-16-be")
        table = struct.pack(">HHH", 0, 1, 18) + struct.pack(">HHHHHH", 3, 1, 0, 1, len(raw), 0) + raw
        font = struct.pack(">IHHHH", 65536, 1, 0, 0, 0) + struct.pack(">4sIII", b"name", 0, 28, len(table)) + table
        self.assertTrue(guard.has_identity(guard.font_names(font), self.blocked))

    def test_truncated_font_fails_closed(self):
        with self.assertRaises((ValueError, struct.error)):
            guard.font_names(b"bad")
