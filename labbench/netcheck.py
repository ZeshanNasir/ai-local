"""Observe which network endpoints named processes use. Records classes of endpoint, not addresses."""
import ipaddress
import re
import subprocess
import time


def _classify(addr):
    host = addr.rsplit(":", 1)[0].strip("[]")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return "other"
    if ip.is_loopback:
        return "loopback"
    return "private" if ip.is_private else "other"


def snapshot(process_names):
    """Established or connecting TCP sockets for the named processes, as {process: {class: count}}."""
    result = {}
    for name in process_names:
        out = subprocess.run(["lsof", "-nP", "-iTCP", "-a", "-c", name], capture_output=True, text=True).stdout
        counts = {}
        for line in out.splitlines()[1:]:
            m = re.search(r"->(\S+)", line)
            if m and ("ESTABLISHED" in line or "SYN_SENT" in line):
                counts[_classify(m.group(1))] = counts.get(_classify(m.group(1)), 0) + 1
        result[name] = counts
    return result


def watch(process_names, seconds, interval=1.0):
    """Union of endpoint classes seen over a window. Short windows miss short connections."""
    seen = {n: {} for n in process_names}
    end = time.time() + seconds
    while time.time() < end:
        for name, counts in snapshot(process_names).items():
            for k, v in counts.items():
                seen[name][k] = max(seen[name].get(k, 0), v)
        time.sleep(interval)
    return seen
