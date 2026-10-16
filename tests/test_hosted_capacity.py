"""Session-allocation regressions; no domain policy is exercised by this harness.

The capacity unit harness replaces seeding/workspace creation only, allowing
bounded-session behavior to be tested without rebuilding the synthetic history.
Actual workspace isolation remains covered by DEMO6.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from aura_app.hosted import HostedDemo


class HostedCapacity(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        with patch("aura_app.hosted.prepare"):
            self.host = HostedDemo(self.directory.name, secure_cookie=False, max_sessions=1)
        app = FastAPI()

        @app.get("/demo/scenarios")
        @app.get("/patients/fixture/status")
        def fixture():
            return {"fixture": True}

        self.workspace = patch.object(self.host, "_workspace", return_value=(
            app, Path(self.directory.name) / "unit-workspace.sqlite3")).start()
        self.addCleanup(patch.stopall)
        self.client = TestClient(self.host)
        self.addCleanup(self.client.close)

    def test_capacity1_shell_assets_probes_do_not_allocate(self):
        for _ in range(20):
            for path, code in [("/", 200), ("/assets/app.js", 200),
                               ("/assets/README.md", 404), ("/favicon.ico", 404),
                               ("/docs", 404), ("/health", 200)]:
                response = self.client.get(path)
                self.assertEqual(response.status_code, code)
                self.assertNotIn("set-cookie", response.headers)
        self.assertEqual(len(self.host.sessions), 0)
        self.workspace.assert_not_called()

    def test_capacity1b_every_response_names_the_serving_node(self):
        # Blue/green: the public URL must reveal which server answered, and nothing more.
        with patch.dict("os.environ", {"AURA_NODE_NAME": "blue", "AURA_NODE_LABEL": "Tencent Cloud Lighthouse"}):
            health = self.client.get("/health")
            self.assertEqual((health.json()["node"], health.json()["node_label"]), ("blue", "Tencent Cloud Lighthouse"))
            for path in ("/health", "/", "/demo/scenarios", "/nowhere"):
                self.assertEqual(self.client.get(path).headers.get("x-aura-node"), "blue", path)
        self.assertEqual(self.client.get("/health").json()["node"], "local")

    def test_capacity2_only_bootstrap_allocates_and_cookie_reuses(self):
        self.assertEqual(self.client.get("/demo/scenarios").status_code, 200)
        for _ in range(10):
            self.assertEqual(self.client.get("/patients/fixture/status").status_code, 200)
            self.client.get("/assets/styles.css")
        self.workspace.assert_called_once()
        self.assertEqual(len(self.host.sessions), 1)

    def test_capacity3_missing_cookie_api_cannot_exhaust_slots(self):
        for _ in range(20):
            response = self.client.get("/patients/fixture/status")
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json()["error"]["code"], "DEMO_SESSION_REQUIRED")
        self.workspace.assert_not_called()
        self.assertEqual(len(self.host.sessions), 0)

    def test_capacity4_full_capacity_preserves_existing_and_serves_shell(self):
        self.client.get("/demo/scenarios")
        previous = tuple(self.host.sessions)
        with TestClient(self.host) as other:
            response = other.get("/demo/scenarios")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response.headers["retry-after"], "60")
            self.assertEqual(response.json()["error"]["code"], "DEMO_BUSY")
            self.assertEqual(other.get("/").status_code, 200)
            self.assertEqual(other.get("/assets/app.js").status_code, 200)
        self.assertEqual(self.client.get("/patients/fixture/status").status_code, 200)
        self.assertEqual(tuple(self.host.sessions), previous)
        self.workspace.assert_called_once()

    def test_capacity5_secure_cookie_rejection_does_not_allocate_per_api(self):
        self.host.secure_cookie = True
        response = self.client.get("/demo/scenarios")
        self.assertIn("; Secure", response.headers["set-cookie"])
        for _ in range(20):
            self.assertEqual(self.client.get("/patients/fixture/status").status_code, 409)
        self.workspace.assert_called_once()

    def test_capacity6_expired_cookie_requires_bootstrap(self):
        self.client.get("/demo/scenarios")
        with patch("aura_app.hosted.monotonic", return_value=10**12):
            self.assertEqual(self.client.get("/patients/fixture/status").status_code, 409)
            self.assertEqual(len(self.host.sessions), 0)
            self.assertEqual(self.client.get("/demo/scenarios").status_code, 200)
        self.assertEqual(self.workspace.call_count, 2)

    def test_cookie7_explicit_lan_ip_retains_session_on_http(self):
        self.host.secure_cookie = True
        self.host.http_demo_hosts = frozenset({"192.168.80.193"})
        with TestClient(self.host, base_url="http://192.168.80.193:8017") as browser:
            response = browser.get("/demo/scenarios")
            self.assertNotIn("; Secure", response.headers["set-cookie"])
            self.assertIn("HttpOnly", response.headers["set-cookie"])
            self.assertIn("SameSite=Strict", response.headers["set-cookie"])
            self.assertEqual(browser.get("/patients/fixture/status").status_code, 200)
        self.workspace.assert_called_once()

    def test_cookie8_public_hostname_keeps_secure_despite_forwarded_headers(self):
        self.host.secure_cookie = True
        self.host.http_demo_hosts = frozenset({"192.168.80.193"})
        with TestClient(self.host, base_url="http://demo.example") as browser:
            response = browser.get("/demo/scenarios", headers={
                "X-Forwarded-Host":"192.168.80.193", "X-Forwarded-Proto":"http"})
            self.assertIn("; Secure", response.headers["set-cookie"])
            self.assertEqual(browser.get("/patients/fixture/status").status_code, 409)

    def test_cookie9_https_even_on_allowed_ip_keeps_secure(self):
        self.host.secure_cookie = True
        self.host.http_demo_hosts = frozenset({"192.168.80.193"})
        with TestClient(self.host, base_url="https://192.168.80.193") as browser:
            response = browser.get("/demo/scenarios")
            self.assertIn("; Secure", response.headers["set-cookie"])
            self.assertEqual(browser.get("/patients/fixture/status").status_code, 200)

    def test_cookie10_unconfigured_private_ip_keeps_secure(self):
        self.host.secure_cookie = True
        self.host.http_demo_hosts = frozenset({"192.168.80.193"})
        with TestClient(self.host, base_url="http://192.168.80.194") as browser:
            response = browser.get("/demo/scenarios")
            self.assertIn("; Secure", response.headers["set-cookie"])

    def test_cookie11_public_wildcard_or_unspecified_configuration_rejected(self):
        with patch("aura_app.hosted.prepare"):
            for host in ("8.8.8.8", "demo.example", "*", "0.0.0.0", "::"):
                with self.subTest(host=host), self.assertRaises(ValueError):
                    HostedDemo(self.directory.name, http_demo_hosts=(host,))
