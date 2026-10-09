"""./lab: which local model should I use on this Mac?

Tests the models already installed in Ollama for speed and accuracy, prints one table and saves it.
Never installs or downloads anything, and never talks to a server other than this machine.
"""
import json
import platform
import shutil
import sys
from datetime import datetime
from pathlib import Path

from . import bench, env, ollama, workloads

ROOT = Path(__file__).resolve().parent.parent
FAST_TOK_S = 40
SUGGESTED = "gemma4:26b-mlx"  # about 18 GB; measured in RESULTS.md


def preflight():
    """The first problem that stops a run, as a plain sentence, or None."""
    if sys.platform != "darwin" or platform.machine() != "arm64":
        return f"ai-local runs on macOS with Apple Silicon only (this is {sys.platform}/{platform.machine()})."
    if not ollama.is_loopback():
        return f"OLLAMA_HOST points at {ollama.base_url()}, not this Mac. Unset it to test local models."
    if not shutil.which("ollama"):
        return "Ollama is not installed. Get it from https://ollama.com/download, open it once, then run ./lab again."
    try:
        ollama.get("/api/version", timeout=3)
    except Exception:
        return "Ollama is installed but not running. Open the Ollama app, then run ./lab again."
    return None


def chat_models(installed):
    return [m["name"] for m in installed if "embed" not in m["name"].lower() and "embed" not in (m.get("family") or "").lower()]


def test(model):
    speed = bench.throughput(model, runs=3)
    tasks = workloads.run_workloads(model)
    ollama.unload_all()
    return {"model": model, "decode_tok_s": speed["warm_summary"]["decode_tok_s"]["median"],
            "passed": sum(t["passed"] for t in tasks), "total": len(tasks),
            "missed": [t["workload"] for t in tasks if not t["passed"]], "throughput": speed, "tasks": tasks}


def verdict(r):
    speed = "fast" if (r["decode_tok_s"] or 0) >= FAST_TOK_S else "slow"
    if not r["missed"]:
        return f"{speed}, all tasks passed"
    parts = [f"{r['missed'].count(w)} {name}{'s' if r['missed'].count(w) > 1 else ''}"
             for w, name in (("logs", "log task"), ("docs", "document task")) if w in r["missed"]]
    if "code" in r["missed"]:
        parts.append("code fix")
    return f"{speed}, missed {', '.join(parts)}"


def table(results):
    rows = [("Model", "Speed", "Accuracy", "Verdict")] + [
        (r["model"], f"{r['decode_tok_s'] or 0:.0f} tok/s", f"{r['passed']}/{r['total']}", verdict(r)) for r in results]
    width = [max(len(row[i]) for row in rows) for i in range(3)]
    return "\n".join(f"{a:<{width[0]}}  {b:>{width[1]}}  {c:>{width[2]}}  {d}" for a, b, c, d in rows)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] in (["-h"], ["--help"]):
        print("usage: ./lab [MODEL ...]\n\nTests installed Ollama models (or only the named ones) for speed and accuracy.")
        return 0
    problem = preflight()
    if problem:
        print(problem, file=sys.stderr)
        return 1
    snap = env.snapshot()
    installed = chat_models(snap["installed_models"])
    models = argv or installed
    missing = [m for m in models if m not in installed]
    if not models or missing:
        print(f"{'Not installed: ' + ', '.join(missing) if missing else 'No models installed.'}\n"
              f"Install one yourself, then run ./lab again, for example:\n  ollama pull {SUGGESTED}   # about 18 GB", file=sys.stderr)
        return 1

    machine = f"{snap['chip']}, {snap['memory_gib']} GB, macOS {snap['macos']}, Ollama {snap['ollama_version']}"
    print(machine)
    results = []
    for model in models:
        print(f"Testing {model} (about a minute)...", flush=True)
        results.append(test(model))

    text = table(results)
    out = ROOT / "results" / datetime.now().strftime("%Y-%m-%dT%H%M")
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(f"# ai-local\n\n{machine}\n\n```\n{text}\n```\n")
    (out / "results.json").write_text(json.dumps({"environment": snap, "results": results}, indent=1) + "\n")
    print(f"\n{text}\n\nSaved: {out.relative_to(ROOT)}/")
    return 0
