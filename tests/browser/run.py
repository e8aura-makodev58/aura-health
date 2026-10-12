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
    parser.add_argument("--suite", nargs="+", choices=["milestone6.cjs", "milestone7.cjs", "settings.cjs", "redesign.cjs", "dual_view.cjs", "agent.cjs", "registry.cjs", "workflows.cjs", "impression.cjs", "story_charts.cjs", "cards.cjs", "final_dash.cjs", "final_dash_polish.cjs", "plain_language.cjs"], default=["milestone6.cjs"])
    parser.add_argument("--hosted", action="store_true", help="isolated local hosted synthetic session server")
    args = parser.parse_args()
    base = f"http://127.0.0.1:{args.port}"
    with TemporaryDirectory(prefix="aura-m6-browser-") as temporary:
        db = Path(temporary) / ("baseline.sqlite3" if args.hosted else "synthetic.sqlite3")
        print("Preparing fresh accepted synthetic checkpoints…", flush=True)
        prepare(db)
        environment = {**os.environ, "AURA_DEMO_DB": str(db), "AURA_BROWSER_URL": base,
                       "AURA_BROWSER_ARTIFACTS": args.artifacts,
                       "AURA_DEMO_ROOT": temporary, "AURA_SECURE_COOKIE":"false"}
        with (Path(temporary) / "server.log").open("w+") as log:
            entry = "aura_app.hosted:create_hosted_app" if args.hosted else "aura_app.demo:create_demo_app"
            server = subprocess.Popen([sys.executable, "-m", "uvicorn", entry,
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
                for suite in args.suite:
                    result = subprocess.run(["node", f"tests/browser/{suite}"], cwd=ROOT, env=environment)
                    if result.returncode:
                        return result.returncode
                return 0
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


if __name__ == "__main__":
    sys.exit(main())
