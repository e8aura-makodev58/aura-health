import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from aura_app.api import create_app


class UiMediaRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.client = TestClient(create_app(db_path=Path(cls.temp.name) / "media.sqlite3"))

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        cls.temp.cleanup()

    def test_media_serves_allowed_art_with_type_and_csp(self):
        response = self.client.get("/assets/media/aura-mark.svg")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/svg+xml")
        self.assertIn("script-src 'self'", response.headers["content-security-policy"])

    def test_media_rejects_other_types_paths_and_names(self):
        for path in ("/assets/media/README.md", "/assets/media/missing.svg",
                     "/assets/media/..%2Fapp.js", "/assets/media/../index.html",
                     "/assets/media/Aura-Mark.svg", "/assets/media/aura-mark.svg.md",
                     "/assets/media/.hidden.svg", "/assets/media/sub/x.svg"):
            self.assertEqual(self.client.get(path).status_code, 404, path)


if __name__ == "__main__":
    unittest.main()
