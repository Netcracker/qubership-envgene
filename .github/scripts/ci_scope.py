import json
import os
from pathlib import Path
import subprocess


def skip_tests_and_build(event_name, event):
    if event_name == "pull_request":
        head = event.get("pull_request", {}).get("head", {}).get("sha")
        if not head:
            return False
        try:
            message = subprocess.check_output(
                ["git", "log", "-1", "--format=%B", head, "--"],
                encoding="utf-8", errors="replace", stderr=subprocess.PIPE,
            )
        except (OSError, subprocess.CalledProcessError):
            print("::warning::Cannot read PR head commit. Running normal CI.")
            return False
        return message.startswith("docs:")
    if event_name != "push":
        return False
    message = (event.get("head_commit") or {}).get("message", "")
    if message.startswith("docs:"):
        return True
    base, head = event.get("before"), event.get("after")
    if not base or not head or base == "0" * 40 or head == "0" * 40:
        return False
    try:
        changed_paths = subprocess.check_output(
            ["git", "diff", "--no-renames", "--name-only", "-z", base, head, "--"],
            stderr=subprocess.PIPE,
        ).split(b"\0")[:-1]
    except (OSError, subprocess.CalledProcessError):
        print("::warning::Cannot read the complete diff. Running normal CI.")
        return False
    return bool(changed_paths) and all(path.startswith(b"docs/") for path in changed_paths)


def dev_build_jobs(event_name, event, skip):
    inputs = event.get("inputs") or {}
    message = (event.get("head_commit") or {}).get("message", "").lower()
    push_build = event_name == "push" and any(
        keyword in message for keyword in ("feat:", "fix:", "breaking change")
    )
    manual = event_name == "workflow_dispatch"
    skip = skip or (manual and inputs.get("docs-check-only") == "true")
    return {
        "skip_tests_and_build": skip,
        "run_tests": not skip,
        "build_envgene": not skip and (push_build or (
            manual and inputs.get("build-envgene") == "true" and inputs.get("tests-only") == "false"
        )),
        "build_gsf_instance": not skip and (
            push_build or (manual and inputs.get("build-gsf-instance") == "true")
        ),
        "build_gsf_discovery": not skip and (
            push_build or (manual and inputs.get("build-gsf-discovery") == "true")
        ),
    }


if __name__ == "__main__":
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    try:
        event = json.loads(Path(os.environ.get("GITHUB_EVENT_PATH", "")).read_text())
    except (OSError, ValueError):
        print("::warning::Cannot read the event payload. Running normal CI.")
        event = {}
        skip = False
    else:
        skip = skip_tests_and_build(event_name, event)
    outputs = dev_build_jobs(event_name, event, skip)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output_file:
        for name, value in outputs.items():
            output = f"{name}={str(value).lower()}"
            output_file.write(output + "\n")
            print(output)
