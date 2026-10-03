"""Own a fresh synthetic DB/server for the optional Playwright acceptance suite."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from aura_app.demo import prepare


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8016)
    parser.add_argument("--artifacts", default="/tmp/aura-m6-browser-artifacts")
    args = parser.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    with TemporaryDirectory(prefix="aura-m6-browser-") as temporary:
        db = Path(temporary) / "synthetic.sqlite3"
        print("Preparing fresh accepted synthetic checkpoints…", flush=True)
        prepare(db)
        environment = {**os.environ, "AURA_DEMO_DB": str(db), "AURA_BROWSER_URL": base,
                       "AURA_BROWSER_ARTIFACTS": args.artifacts}
        with (Path(temporary) / "server.log").open("w+") as log:
            server = subprocess.Popen([sys.executable, "-m", "uvicorn", "aura_app.demo:create_demo_app",
                                       "--factory", "--host", "127.0.0.1", "--port", str(args.port)],
                                      cwd=ROOT, env=environment, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    if server.poll() is not None:
                        log.seek(0)
                        raise RuntimeError(log.read())
                    try:
                        with urlopen(base + "/health", timeout=1) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(.1)
                else:
                    raise RuntimeError("Local demo server did not become ready")
                result = subprocess.run(["node", "tests/browser/milestone6.cjs"], cwd=ROOT, env=environment)
                return result.returncode
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


if __name__ == "__main__":
    sys.exit(main())
