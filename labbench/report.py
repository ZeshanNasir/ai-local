"""Turn result files into the Markdown tables used in the README, so numbers are never typed by hand."""
import json
from pathlib import Path


def _load(directory, kind):
    files = [json.loads(p.read_text()) for p in sorted(Path(directory).glob(f"*.{kind}.json"))]
    return {d["model"]: d for d in files}


def _ladders(directory):
    """Ladder results may be split over several files (e.g. a later, larger step); merge steps per model."""
    merged = {}
    for p in sorted(Path(directory).glob("*.ladder*.json")):
        d = json.loads(p.read_text())
        merged.setdefault(d["model"], {"model": d["model"], "steps": []})["steps"] += d["steps"]
    for d in merged.values():
        d["steps"].sort(key=lambda s: s["prompt_tokens"])
    return merged


def tables(directory):
    th, wl, ld = _load(directory, "throughput"), _load(directory, "workloads"), _ladders(directory)
    out = ["### Throughput (warm, about 1,000-token prompt, 256-token cap, median of 5 runs)", "",
           "| Model | Cold load | Time to first token | Prompt tok/s | Decode tok/s | Decode spread |", "| :--- | ---: | ---: | ---: | ---: | ---: |"]
    for m, d in th.items():
        w = d["warm_summary"]
        out.append(f"| `{m}` | {d['runs'][0]['load_s']:.1f} s | {w['ttft_s']['median']:.2f} s | {w['prompt_tok_s']['median']:.0f} | "
                   f"{w['decode_tok_s']['median']:.1f} | {d['decode_spread_pct']:.0f}% |")
    out += ["", "### Workloads (3 repeats per case, temperature 0)", "", "| Model | Logs (6 cases) | Documents (8) | Code (1) | Median wall time per case |", "| :--- | ---: | ---: | ---: | ---: |"]
    for m, d in wl.items():
        s = d["summary"]
        out.append(f"| `{m}` | {s['logs']} | {s['docs']} | {s['code']} | {d['median_wall_s']['median']:.1f} s |")
    out += ["", "### Context ladder (fact hidden mid-prompt; stops at the first unsafe step)", "",
            "| Model | Prompt tokens | Recalled | Prompt tok/s | Time to first token | Server-reported memory | Lowest free memory | Swap growth |",
            "| :--- | ---: | :---: | ---: | ---: | ---: | ---: | ---: |"]
    for m, d in ld.items():
        for s in d["steps"]:
            out.append(f"| `{m}` | {s['prompt_tokens']:,} | {'yes' if s['recalled_fact'] and s.get('size_ok') else 'no'}{' (error)' if s['error'] else ''} | {s['prompt_tok_s']:.0f} | "
                       f"{s['ttft_s']:.0f} s | {s['server_reported_gb']:.1f} GB | {s['min_free_pct']}% | {(s['swap_growth_mb'] or 0):.0f} MB |"
                       f"{' **stopped: unsafe**' if s.get('stopped_here') else ''}")
    return "\n".join(out)
