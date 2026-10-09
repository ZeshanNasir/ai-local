"""Collect the machine and runtime conditions that make a measurement interpretable.

No serial numbers, hostnames, usernames or account identifiers are recorded.
"""
import json
import platform
import re
import subprocess
import threading
import time

from . import ollama


def _run(*cmd, timeout=15):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout).stdout.strip()
    except Exception:
        return ""


def memory_free_pct():
    """System-wide free memory percentage from `memory_pressure` (macOS), or None."""
    m = re.search(r"free percentage: (\d+)%", _run("memory_pressure"))
    return int(m.group(1)) if m else None


def swap_used_mb():
    m = re.search(r"used = ([\d.]+)M", _run("sysctl", "-n", "vm.swapusage"))
    return float(m.group(1)) if m else None


def snapshot():
    batt = _run("pmset", "-g", "batt")
    try:
        models = [{"name": m["name"], "size_gb": round(m["size"] / 1e9, 1),
                   "digest": m["digest"][:12], **{k: m.get("details", {}).get(k) for k in ("family", "parameter_size", "quantization_level")}}
                  for m in ollama.get("/api/tags")["models"]]
        version = ollama.get("/api/version")["version"]
    except Exception as e:
        models, version = [], f"unavailable ({type(e).__name__})"
    return {
        "macos": platform.mac_ver()[0],
        "hardware_model": _run("sysctl", "-n", "hw.model"),
        "chip": _run("sysctl", "-n", "machdep.cpu.brand_string"),
        "memory_gib": round(int(_run("sysctl", "-n", "hw.memsize") or 0) / 2**30),
        "gpu_wired_limit_mb": _run("sysctl", "-n", "iogpu.wired_limit_mb"),  # 0 = macOS default
        "power": "AC" if "AC Power" in batt else "battery" if batt else "unknown",
        "python": platform.python_version(),
        "ollama_version": version,
        "installed_models": models,
        "memory_free_pct": memory_free_pct(),
        "swap_used_mb": swap_used_mb(),
    }


class Sampler(threading.Thread):
    """Samples memory headroom and swap while a measurement runs, to catch pressure that
    a before/after reading would miss."""

    def __init__(self, interval=3.0):
        super().__init__(daemon=True)
        self.interval, self._stop_flag, self.free, self.swap = interval, threading.Event(), [], []

    def run(self):
        while not self._stop_flag.is_set():
            f, s = memory_free_pct(), swap_used_mb()
            if f is not None:
                self.free.append(f)
            if s is not None:
                self.swap.append(s)
            self._stop_flag.wait(self.interval)

    def result(self):
        self._stop_flag.set()
        self.join(timeout=10)
        return {"min_free_pct": min(self.free) if self.free else None,
                "max_swap_mb": max(self.swap) if self.swap else None,
                "swap_growth_mb": (max(self.swap) - self.swap[0]) if self.swap else None,
                "samples": len(self.free)}


def main():
    print(json.dumps(snapshot(), indent=2))
