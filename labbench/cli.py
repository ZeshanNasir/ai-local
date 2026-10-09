import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import bench, cost, embed, env, netcheck, ollama, report, workloads
from .stats import summarize


def _environment_for(model):
    """Environment snapshot that names only the model under test; other installed models are counted, not listed."""
    snap = env.snapshot()
    models = snap.pop("installed_models")
    snap["installed_models"] = [m for m in models if m["name"] == model]
    snap["other_models_installed"] = len(models) - len(snap["installed_models"])
    return snap


def _write(path, payload):
    payload = {"recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "environment": _environment_for(payload.get("model")), **payload}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, indent=1) + "\n")
    print(f"wrote {path}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="labbench", description="Measure local AI inference on an engineering workstation.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("env", help="print the environment snapshot")
    p = sub.add_parser("throughput", help="cold start plus warm throughput runs")
    p.add_argument("model"); p.add_argument("--runs", type=int, default=3); p.add_argument("--out")
    p = sub.add_parser("workloads", help="run the synthetic log, document and coding tasks")
    p.add_argument("model"); p.add_argument("--repeats", type=int, default=1); p.add_argument("--think", action="store_true"); p.add_argument("--out")
    p = sub.add_parser("ladder", help="context ladder with a recall check; stops at the first unsafe step")
    p.add_argument("model"); p.add_argument("--sizes", default="4096,8192,16384,32768"); p.add_argument("--out")
    p = sub.add_parser("retrieval", help="embedding model versus a lexical baseline")
    p.add_argument("model"); p.add_argument("--out")
    p = sub.add_parser("net", help="observe network endpoint classes of named processes for a window")
    p.add_argument("--processes", default="ollama"); p.add_argument("--seconds", type=int, default=30)
    p = sub.add_parser("report", help="print Markdown tables from a results directory")
    p.add_argument("directory")
    p = sub.add_parser("agent", help="one bounded OpenCode session on the coding task, scored by the tests")
    p.add_argument("model"); p.add_argument("--timeout", type=int, default=900); p.add_argument("--repeats", type=int, default=1); p.add_argument("--out")
    p = sub.add_parser("cost", help="break-even arithmetic from an assumptions file")
    p.add_argument("assumptions")
    args = ap.parse_args(argv)

    if args.cmd == "env":
        env.main()
    elif args.cmd == "throughput":
        r = bench.throughput(args.model, runs=args.runs)
        print(json.dumps(r["warm_summary"], indent=1))
        if args.out:
            _write(args.out, {"kind": "throughput", **r})
    elif args.cmd == "workloads":
        rows = workloads.run_workloads(args.model, think=args.think, repeats=args.repeats)
        by = {}
        for r in rows:
            by.setdefault(r["workload"], []).append(r["passed"])
        summary = {k: f"{sum(v)}/{len(v)}" for k, v in by.items()}
        print(summary)
        if args.out:
            _write(args.out, {"kind": "workloads", "model": args.model, "think": args.think, "summary": summary, "cases": rows,
                              "median_wall_s": summarize([r["wall_s"] for r in rows])})
    elif args.cmd == "ladder":
        r = bench.ladder(args.model, [int(x) for x in args.sizes.split(",")])
        for s in r["steps"]:
            print(s)
        if args.out:
            _write(args.out, {"kind": "ladder", **r})
    elif args.cmd == "retrieval":
        r = embed.evaluate(args.model)
        print(json.dumps(r, indent=1))
        if args.out:
            _write(args.out, {"kind": "retrieval", **r})
    elif args.cmd == "net":
        print(json.dumps(netcheck.watch(args.processes.split(","), args.seconds), indent=1))
    elif args.cmd == "report":
        print(report.tables(args.directory))
    elif args.cmd == "agent":
        from . import agent
        runs = [agent.run(args.model, timeout=args.timeout) for _ in range(args.repeats)]
        summary = f"{sum(r['tests_pass_after'] and not r['edited_tests'] for r in runs)}/{len(runs)} fixed without editing tests"
        print(summary)
        if args.out:
            _write(args.out, {"kind": "agent", "model": args.model, "harness": "opencode", "summary": summary, "runs": runs})
    elif args.cmd == "cost":
        a = json.loads(Path(args.assumptions).read_text())
        print(json.dumps({"result": cost.evaluate(a), "net_per_seat_by_success_rate": cost.sensitivity(a)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
