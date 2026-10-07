"""Operator settings and native transports; mock-only, no keys/spend in test output."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient
import httpx

from aura_app.system_settings import SystemSettings, SyntheticSettingsProvider, settings_api
from aura_app.api import create_app
from aura_app.hosted import HostedDemo
from aura_communication.vendor import VendorProvider
from aura_communication.domain import CommunicationPurpose
from aura_communication.provider import ProviderUnavailable
from aura_app.models import AppError

KEY="synthetic-test-key-not-a-real-secret"
CANDIDATE={"candidate_id":"synthetic-test","message":"Synthetic connection check.",
           "acknowledged_facts":[],"question_intent":None,"cta_type":None}


class OperatorSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.root=Path(self.temp.name)
        self.requests=[]
        def reply(request):
            self.requests.append(request)
            if request.method=="GET": return httpx.Response(200,json={"data":[{"id":"fixture-text"},{"id":"embedding-fixture"}]})
            payload=json.loads(request.content)
            contract=json.loads(payload["messages"][1]["content"])
            selected=contract["request"]["candidates"][-1]
            return httpx.Response(200,json={"choices":[{"finish_reason":"stop","message":{"content":json.dumps(selected)}}]})
        self.transport=httpx.MockTransport(reply)
        self.settings=SystemSettings(self.root/"system",transport=self.transport)
        self.client=TestClient(settings_api(self.settings),base_url="https://demo.test")
        self.headers={"Origin":"https://demo.test","Authorization":"Bearer "+self.settings._admin}

    def tearDown(self): self.client.close();self.temp.cleanup()
    def post(self,action,body,headers=None):
        return self.client.post("/system/settings/"+action,json=body,headers=self.headers if headers is None else headers)

    def configure(self,provider="openai",enabled=True):
        self.assertEqual(self.post("credential",{"provider":provider,"api_key":KEY}).status_code,200)
        variant=self.settings.snapshot()["models"][provider]["variant"]
        response=self.post("save",{"provider":provider,"model":"fixture-text","variant":variant,"enabled":enabled})
        self.assertEqual(response.status_code,200);return response

    def test_settings1_admin_and_secure_origin_required(self):
        self.assertEqual(self.post("read",{},{}).status_code,403)
        self.assertEqual(self.post("read",{},{"Origin":"https://demo.test"}).status_code,401)
        self.assertEqual(self.post("read",{},{**self.headers,"Origin":"https://attacker.invalid"}).status_code,403)
        self.assertEqual(self.post("read",{},{**self.headers,"Origin":"http://demo.test"}).status_code,403)
        self.assertEqual(self.post("read",{}).status_code,200)

    def test_settings2_four_providers_keys_write_only_and_private_files(self):
        for provider in ("openrouter","openai","deepseek","tencent"):
            response=self.post("credential",{"provider":provider,"api_key":KEY})
            self.assertEqual(response.status_code,200);self.assertNotIn(KEY,response.text)
        self.assertEqual(len(self.post("read",{}).json()["providers"]),4)
        self.assertNotIn(KEY,self.client.get("/system/status").text)
        for name in ("admin.token","provider-credentials.json","provider-settings.json"):
            self.assertEqual((self.settings.root/name).stat().st_mode&0o777,0o600)
        self.assertEqual(self.settings.root.stat().st_mode&0o777,0o700)

    def test_settings3_persistence_and_credential_removal(self):
        self.configure("deepseek")
        loaded=SystemSettings(self.settings.root)
        self.assertTrue(loaded.public_status()["live_enabled"])
        prior=loaded.state["revision"]
        self.assertEqual(self.post("remove-key",{"provider":"deepseek"}).status_code,200)
        self.assertFalse(self.settings.public_status()["live_enabled"])
        self.assertNotEqual(prior,self.settings.state["revision"])

    def test_settings4_invalid_input_never_echoes_key(self):
        for action,body in (("credential",{"provider":[],"api_key":KEY}),
                            ("credential",{"provider":"openai","api_key":KEY,"unexpected":KEY}),
                            ("save",{"provider":"openai","model":"https://private.invalid","variant":"bad","enabled":True})):
            response=self.post(action,body);self.assertEqual(response.status_code,400);self.assertNotIn(KEY,response.text)
        self.assertEqual(self.post("save",{"provider":"openai","model":"fixture","variant":"default","enabled":True}).status_code,400)

    def test_settings5_model_discovery_and_explicit_paid_test(self):
        self.configure()
        discovered=self.post("models",{"provider":"openai","variant":"default"}).json()
        self.assertEqual(discovered["models"],["fixture-text"])
        self.assertEqual(self.post("test",{"confirm":"not-confirmed"}).status_code,400)
        self.assertEqual(self.post("test",{"confirm":"SYNTHETIC_TEST_MAY_COST"}).json()["status"],"PASS")
        self.assertNotIn(KEY,str(json.loads(self.requests[-1].content)))

    def test_settings6_native_transport_for_each_vendor_and_fixed_host(self):
        hosts={"openai":"api.openai.com","openrouter":"openrouter.ai","deepseek":"api.deepseek.com","tencent":"tokenhub-intl.tencentcloudmaas.com"}
        for provider,host in hosts.items():
            result=VendorProvider(provider,"fixture-text",KEY,transport=self.transport).generate({"instructions":"Return JSON","request":{"candidates":[CANDIDATE]}})
            self.assertEqual(result,CANDIDATE);self.assertEqual(self.requests[-1].url.host,host)
            self.assertEqual(self.requests[-1].headers["authorization"],"Bearer "+KEY)
        with self.assertRaises(KeyError): VendorProvider("tencent","fixture-text",KEY,variant="http://private.invalid")

    def test_settings7_rejects_redirect_truncated_invalid_oversize_and_timeout(self):
        payloads=[httpx.Response(302,headers={"location":"https://attacker.invalid"}),
                  httpx.Response(200,json={"choices":[{"finish_reason":"length","message":{"content":"{}"}}]}),
                  httpx.Response(200,json={"choices":[{"finish_reason":"stop","message":{"content":"not JSON"}}]}),
                  httpx.Response(200,content=b"x"*20000)]
        for response in payloads:
            with self.assertRaises(ProviderUnavailable): VendorProvider("openai","fixture-text",KEY,transport=httpx.MockTransport(lambda _r:response)).generate({"instructions":"JSON","request":{}})
        def timeout(_request):raise httpx.ReadTimeout("mock only")
        with self.assertRaises(TimeoutError): VendorProvider("openai","fixture-text",KEY,transport=httpx.MockTransport(timeout)).generate({"instructions":"JSON","request":{}})

    def test_settings8_disable_and_budget_fail_to_existing_fallback(self):
        provider=SyntheticSettingsProvider(self.settings)
        with self.assertRaises(ProviderUnavailable): provider.generate({})
        self.configure()
        self.settings.hour=0
        with self.assertRaises(ProviderUnavailable): provider.generate({"instructions":"JSON","request":{}})
        self.assertEqual(self.requests,[])

    def test_settings9_real_api_not_enabled_by_settings(self):
        self.configure()
        app=create_app(self.root/"ordinary.sqlite3")
        self.assertEqual(app.state.communication_service.provider.model_id,"disabled")


class HostedLiveBoundaryTests(unittest.TestCase):
    def test_settings10_synthetic_live_boundary_and_static_safety(self):
        with TemporaryDirectory() as temporary:
            root=Path(temporary);calls=[]
            def reply(request):
                contract=json.loads(json.loads(request.content)["messages"][1]["content"]);calls.append(contract)
                selected=contract["request"]["candidates"][-1]
                return httpx.Response(200,json={"choices":[{"finish_reason":"stop","message":{"content":json.dumps(selected)}}]})
            settings=SystemSettings(root/"system",transport=httpx.MockTransport(reply))
            host=HostedDemo(root/"demo",secure_cookie=False,settings=settings)
            client=TestClient(host)
            settings.credential({"provider":"openai","api_key":KEY})
            settings.update({"provider":"openai","model":"fixture-text","variant":"default","enabled":True})
            client.get("/demo/scenarios")
            app=next(iter(host.sessions.values()))["app"];service=app.state.communication_service
            view=client.get("/patients/demo-B-7/view").json()
            result=service.render("demo-B-7",view["latest_event_id"],purpose=CommunicationPurpose.EXPLAIN_OBSERVATION)
            self.assertTrue(result["generation_used"]);self.assertEqual(len(calls),1)
            self.assertIn("synthetic demo",view["privacy_notice"])
            self.assertNotIn(KEY,json.dumps(result))
            safety=client.get("/patients/demo-F-7/view").json()
            result=service.render("demo-F-7",safety["latest_event_id"])
            self.assertFalse(result["generation_used"]);self.assertEqual(len(calls),1)
            settings.remove({"provider":"openai"})
            revised=service.render("demo-B-7",view["latest_event_id"],purpose=CommunicationPurpose.EXPLAIN_OBSERVATION)
            self.assertFalse(revised["generation_used"]);self.assertEqual(len(calls),1)
            client.close()


if __name__=="__main__":unittest.main()
