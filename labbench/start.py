"""Guided first run (`./lab`): check the machine, pick a measured model, run a short safe benchmark, save a report.

Never installs software, never pulls a model without a yes, never talks to a non-loopback server.
"""
import json
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import env, ollama, report

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "benchmarks" / "results" / "2026-10-09"
BASELINE_GIB = 48
OLLAMA_DOWNLOAD = "https://ollama.com/download"


def measured_models(directory=EVIDENCE):
    """Models with saved throughput evidence, fastest decode first: (name, size_gb, decode_tok_s)."""
    rows = []
    for p in sorted(Path(directory).glob("*.throughput.json")):
        d = json.loads(p.read_text())
        size = next((m["size_gb"] for m in d["environment"]["installed_models"] if m["name"] == d["model"]), None)
        rows.append((d["model"], size, d["warm_summary"]["decode_tok_s"]["median"]))
    return sorted(rows, key=lambda r: -r[2])


def preflight():
    """Problems that stop the run, as plain sentences. Empty means go."""
    if sys.platform != "darwin" or platform.machine() != "arm64":
        return [f"ai-local supports macOS on Apple Silicon only (this is {sys.platform}/{platform.machine()})."]
    if not ollama.is_loopback():
        return [f"OLLAMA_HOST points at {ollama.base_url()}, which is not this machine. "
                "ai-local measures local inference only; unset OLLAMA_HOST or point it at 127.0.0.1."]
    if not shutil.which("ollama"):
        return [f"Ollama is not installed. Install it from {OLLAMA_DOWNLOAD}, open it once, then run ./lab again."]
    try:
        ollama.get("/api/version", timeout=3)
    except Exception:
        return ["Ollama is installed but its server is not answering on this machine. Open the Ollama app (or run `ollama serve`), then run ./lab again."]
    return []


def _ask(question, default=False):
    if not sys.stdin.isatty():
        return default
    answer = input(f"{question} [{'Y/n' if default else 'y/N'}] ").strip().lower()
    return default if not answer else answer in ("y", "yes")


def choose(models, installed, preset=None):
    if preset:
        return preset
    print("\nModels with published measurements (M4 Pro, 48 GB):")
    for i, (name, size, tok_s) in enumerate(models, 1):
        print(f"  {i}. {name:<18} {size or '?':>5} GB  {tok_s:5.1f} tok/s decode   {'installed' if name in installed else 'not installed'}")
    default = next((i for i, m in enumerate(models, 1) if m[0] in installed), 1)
    if not sys.stdin.isatty():
        return models[default - 1][0]
    pick = input(f"Choose a model [{default}]: ").strip() or str(default)
    if not pick.isdigit() or not 1 <= int(pick) <= len(models):
        sys.exit(f"No model numbered {pick}.")
    return models[int(pick) - 1][0]


def run(model=None, yes=False, out_root=ROOT / "results"):
    problems = preflight()
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    snap = env.snapshot()
    print(f"{snap['chip']}, {snap['memory_gib']} GB, macOS {snap['macos']}, Ollama {snap['ollama_version']}, power: {snap['power']}")
    if snap["memory_gib"] != BASELINE_GIB:
        print(f"Note: the published results come from a {BASELINE_GIB} GB machine. This configuration is untested; treat results as your own first measurement.")
    if (snap["memory_free_pct"] or 100) < 25:
        print(f"Free memory is {snap['memory_free_pct']}%. Close heavy applications for cleaner numbers.")

    models = measured_models()
    installed = {m["name"] for m in snap["installed_models"]}
    model = choose(models, installed, model)
    if model not in installed:
        size = next((s for n, s, _ in models if n == model), None)
        print(f"{model} is not installed. Downloading it uses about {size or 'an unknown number of'} GB of disk.")
        if not (yes or _ask(f"Run `ollama pull {model}` now?")):
            print("Nothing downloaded. Pull the model yourself or choose an installed one.")
            return 1
        if subprocess.run(["ollama", "pull", model]).returncode != 0:
            return 1

    from .cli import _write
    from . import bench, workloads
    from .stats import summarize
    out = out_root / datetime.now().strftime("%Y-%m-%dT%H%M")
    slug = model.replace(":", "_").replace("/", "_")
    print(f"\nShort benchmark of {model}: 3 warm throughput runs, then 15 synthetic tasks once. About a minute on the baseline machine after the model is loaded.")
    r = bench.throughput(model, runs=3)
    _write(out / f"{slug}.throughput.json", {"kind": "throughput", **r})
    rows = workloads.run_workloads(model)
    by = {}
    for row in rows:
        by.setdefault(row["workload"], []).append(row["passed"])
    summary = {k: f"{sum(v)}/{len(v)}" for k, v in by.items()}
    _write(out / f"{slug}.workloads.json", {"kind": "workloads", "model": model, "think": False, "summary": summary,
                                           "cases": rows, "median_wall_s": summarize([row["wall_s"] for row in rows])})
    text = (f"# ai-local run: {model}\n\n{snap['chip']}, {snap['memory_gib']} GB, macOS {snap['macos']}, "
            f"Ollama {snap['ollama_version']}, power: {snap['power']}, free memory at start: {snap['memory_free_pct']}%.\n"
            "Thinking off, temperature 0. Throughput is the median of 3 warm runs; each task ran once.\n\n"
            + report.tables(out).replace("median of 5 runs", "median of 3 runs").replace("3 repeats per case", "1 run per case")
            .split("\n### Context ladder")[0] + "\n")
    (out / "report.md").write_text(text)
    print(f"\n{text}\nSaved: {out.relative_to(ROOT)}/")
    return 0
