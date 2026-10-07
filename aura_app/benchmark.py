"""Small synthetic demo timing diagnostic; not clinical-performance evaluation."""

import argparse
import json
from pathlib import Path
from statistics import median
from tempfile import TemporaryDirectory
from time import perf_counter
from uuid import uuid4

from fastapi.testclient import TestClient
from .hosted import HostedDemo


def run(root):
    started=perf_counter(); app=HostedDemo(root,secure_cookie=False)
    startup=perf_counter()-started
    samples=[]; ingestion={}
    client = TestClient(app)
    try:
        for _ in range(10):
            before=perf_counter(); response=client.get("/patients/demo-B-7/status"); response.raise_for_status()
            samples.append((perf_counter()-before)*1000)
        for label,patient in (("short_history","demo-stable-7"),("long_history","demo-B-7")):
            value=str(uuid4()); before=perf_counter()
            response=client.post(f"/patients/{patient}/events",json={"event_id":value,"correlation_id":value,
                "idempotency_key":value,"event_type":"PATIENT_CHECKIN","occurred_at":"2026-01-21T12:00:00+00:00",
                "source":"patient","payload":{"state":"Good"}}); response.raise_for_status()
            ingestion[label]=round((perf_counter()-before)*1000,3)
        before=perf_counter(); client.post("/demo/reset",json={"confirm":"RESET_SYNTHETIC_SESSION"}).raise_for_status()
        reset_ms=(perf_counter()-before)*1000
    finally:
        client.close()
    return {"synthetic_only":True,"initial_prepare_seconds":round(startup,3),
            "status_samples":len(samples),"status_median_ms":round(median(samples),3),
            "status_max_ms":round(max(samples),3),"event_ingestion_ms":ingestion,
            "session_reset_ms":round(reset_ms,3),"live_model_tested":False}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path); parser.add_argument("--save",type=Path)
    args=parser.parse_args()
    if args.root: result=run(args.root)
    else:
        with TemporaryDirectory(prefix="aura-benchmark-") as temporary: result=run(temporary)
    print(json.dumps(result,indent=2))
    if args.save: args.save.write_text(json.dumps(result,indent=2)+"\n")


if __name__ == "__main__": main()
