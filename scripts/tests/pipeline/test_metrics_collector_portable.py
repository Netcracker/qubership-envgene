import json
import os
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def test_copied_client_runs_both_jobs_without_full_pipeline_package(monkeypatch, tmp_path):
    events = []

    class Collector(BaseHTTPRequestHandler):
        def do_POST(self):
            assert self.path == "/api/v1/activity"
            assert self.headers["Content-Type"] == "application/cloudevents+json"
            events.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self.send_response(202)
            self.end_headers()

        def log_message(self, *args):
            pass

    job1 = tmp_path / "prepare"
    client = job1 / ".metrics-collector-client"
    (client / "pipeline").mkdir(parents=True)
    source = Path(__file__).resolve().parents[2] / "pipeline"
    for name in ("__init__", "metrics_collector_activity", "metrics_collector_cli"):
        shutil.copy2(source / f"{name}.py", client / "pipeline" / f"{name}.py")

    monkeypatch.delenv("METRICS_COLLECTOR_RESULTS_ROOT", raising=False)
    monkeypatch.delenv("METRICS_COLLECTOR_TRACE_ID", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    monkeypatch.delenv("CURL_CA_BUNDLE", raising=False)
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    monkeypatch.setenv("CI_PIPELINE_ID", "pipeline-1")
    monkeypatch.setenv("CI_PROJECT_ID", "project-1")
    monkeypatch.setenv("CI_PROJECT_DIR", str(job1))
    monkeypatch.setenv("CI_JOB_ID", "prepare")
    monkeypatch.setenv("envgen_image", "env-generator:1.2.3")

    prefix = """
import os, sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, sys.argv[1])
from pipeline.metrics_collector_activity import MetricsCollectorActivity
from pipeline.metrics_collector_cli import main
"""

    def run_client(root, script):
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(str(Path(path).resolve())
                                          for path in env.get("PYTHONPATH", "").split(os.pathsep) if path)
        result = subprocess.run(
            [sys.executable, "-c", prefix + script, str(root / ".metrics-collector-client")],
            cwd=root, env=env, capture_output=True, text=True, timeout=20,
        )
        assert result.returncode == 0, result.stderr

    with ThreadingHTTPServer(("127.0.0.1", 0), Collector) as server:
        monkeypatch.setenv("METRICS_COLLECTOR_URL", f"http://127.0.0.1:{server.server_port}")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            run_client(job1, """
main(["trace-id"])
Path(".metrics-collector-trace-id").write_text(os.environ["METRICS_COLLECTOR_TRACE_ID"])
main(["start"])
ctx = SimpleNamespace(params={"ENV_NAMES": "cluster/env", "SECRET": "hidden"}, sensitive_params=["SECRET"])
activity = MetricsCollectorActivity(ctx)
activity.send_running()
steps = [SimpleNamespace(name="env_build", status="SUCCESS", duration_ms=10)]
activity.record_completion("SUCCESS", steps)
activity.send_running(results=steps)
os.environ["CI_JOB_STATUS"] = "success"
main(["running"])
main(["stop"])
main(["stop"])
assert list(Path(".metrics-collector-client/state").glob("*/*.json"))
""")
            job2 = tmp_path / "sync"
            shutil.copytree(client, job2 / ".metrics-collector-client")
            shutil.copy2(job1 / ".metrics-collector-trace-id", job2 / ".metrics-collector-trace-id")
            monkeypatch.setenv("CI_PROJECT_DIR", str(job2))
            monkeypatch.setenv("CI_JOB_ID", "sync")
            monkeypatch.delenv("envgen_image")
            run_client(job2, """
class RejectPipelineDependencies:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "envgenehelper" or fullname == "pipeline.pipeline_parameters":
            raise AssertionError("Sync must use saved results without importing the full pipeline")
sys.meta_path.insert(0, RejectPipelineDependencies())
os.environ["METRICS_COLLECTOR_TRACE_ID"] = Path(".metrics-collector-trace-id").read_text()
os.environ["CI_JOB_STATUS"] = "running"
main(["running"])
os.environ["CI_JOB_STATUS"] = "success"
main(["stop"])
main(["stop"])
assert Path(".metrics-collector-client/state").exists()
""")
        finally:
            server.shutdown()
            thread.join(timeout=5)

    assert [event["type"] for event in events] == [
        "start", "running", "running", "running", "stop", "running", "stop",
    ]
    assert len({event["traceid"] for event in events}) == 1
    assert events[-1]["status"] == "SUCCESS"
    assert events[-1]["data"]["envgeneVersion"] == "1.2.3"
    assert all("steps" not in event["data"] for event in events[-2:])
    assert events[-1]["data"]["inputParameters"] == {"ENV_NAMES": "cluster/env"}
    assert "SECRET" not in events[-1]["data"]["inputParameters"]
