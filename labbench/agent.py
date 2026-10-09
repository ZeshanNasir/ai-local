"""Run one bounded OpenCode session against a disposable copy of the coding task and score the outcome.

OpenCode is pointed at the local Ollama endpoint through a throwaway config that contains no remote tool
servers, and runs in a temporary directory that holds only the synthetic project."""
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from . import netcheck
from .scoring import run_tests
from .workloads import DATA

TASK = ("The unit tests in this project fail. Fix the bug with the smallest change that makes them pass. "
        "Do not edit the tests. Run the tests with `python3 -m unittest -q` to check your work.")


def run(model, *, timeout=900, watch_network=True):
    # LABBENCH_WORKDIR: parent for the disposable workspace (default: the system temp directory)
    with tempfile.TemporaryDirectory(dir=os.environ.get("LABBENCH_WORKDIR")) as tmp:
        work = Path(tmp) / "repo"
        shutil.copytree(DATA / "coding" / "repo", work)
        for cmd in (["git", "init", "-q"], ["git", "add", "-A"], ["git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base"]):
            subprocess.run(cmd, cwd=work, capture_output=True)
        cfg = Path(tmp) / "opencode.json"
        cfg.write_text(json.dumps({"$schema": "https://opencode.ai/config.json", "model": f"ollama/{model}",
                                   "provider": {"ollama": {"npm": "@ai-sdk/openai-compatible", "options": {"baseURL": "http://127.0.0.1:11434/v1"},
                                                           "models": {model: {}}}}}))
        env = {**os.environ, "OPENCODE_CONFIG": str(cfg), "PWD": str(work)}  # OpenCode reads PWD, not the process cwd
        net, stop = {}, threading.Event()

        def observe():
            while not stop.is_set():
                for proc, counts in netcheck.snapshot(["opencode", "bun", "ollama"]).items():
                    for k, v in counts.items():
                        net.setdefault(proc, {})[k] = max(net.get(proc, {}).get(k, 0), v)
                stop.wait(2)
        t = threading.Thread(target=observe, daemon=True)
        if watch_network:
            t.start()
        start = time.perf_counter()
        error = ""
        events = []
        try:
            p = subprocess.run(["opencode", "run", "-m", f"ollama/{model}", "--format", "json", TASK], cwd=work, env=env,
                               capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)
            for line in p.stdout.splitlines():
                try:
                    events.append(json.loads(line))
                except ValueError:
                    pass
            if p.returncode:
                error = f"exit {p.returncode}: {p.stderr[-200:]}"
        except subprocess.TimeoutExpired:
            error = f"timeout after {timeout}s"
        wall = time.perf_counter() - start
        stop.set()
        ok, _ = run_tests(work)
        diff = [d for d in subprocess.run(["git", "diff", "--name-only"], cwd=work, capture_output=True, text=True).stdout.split() if "__pycache__" not in d]
        kinds = {}
        for e in events:
            kinds[e.get("type", "?")] = kinds.get(e.get("type", "?"), 0) + 1
        tools = [e.get("part", {}).get("tool") or e.get("tool") for e in events if "tool" in json.dumps(e)[:400]]
        texts = [e.get("part", {}).get("text", "") for e in events if e.get("type") == "text"]
        return {"final_text": (texts[-1] if texts else "")[:400], "model": model, "harness": "opencode", "tests_pass_after": ok, "files_changed": diff,
                "edited_tests": any(d.startswith("tests/") for d in diff), "wall_s": round(wall, 1), "error": error,
                "event_count": len(events), "event_types": kinds, "tool_events": len([x for x in tools if x]),
                "network_endpoint_classes_seen": net}
