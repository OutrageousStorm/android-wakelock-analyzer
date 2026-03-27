#!/usr/bin/env python3
"""
analyze.py -- Android bugreport battery drain analyzer
Usage: python3 analyze.py bugreport.zip [--top 15] [--csv out.csv]
"""
import sys, re, csv, zipfile, argparse
from pathlib import Path
from collections import defaultdict

def extract_batterystats(zip_path):
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        # Find the batterystats file
        candidates = [n for n in names if "batterystats" in n.lower() or "bugreport" in n.lower()]
        for name in candidates:
            with z.open(name) as f:
                content = f.read().decode("utf-8", errors="ignore")
                if "uid" in content.lower() and "wakelock" in content.lower():
                    return content
    return None

def parse_uid_map(content):
    uid_map = {}
    for line in content.splitlines():
        m = re.search(r"UID u0a(\d+).*?=\s*(\S+)", line)
        if m:
            uid_map[f"u0a{m.group(1)}"] = m.group(2)
        m2 = re.search(r'"(\S+)".*?uid=(\d+)', line)
        if m2:
            uid_map[m2.group(2)] = m2.group(1)
    return uid_map

def parse_wakelocks(content):
    wakelocks = defaultdict(float)
    # Pattern: Uid u0aXXX: wl=NAME time=XXXms
    for line in content.splitlines():
        m = re.search(r"(u0a\d+|uid \d+).*?wl=([^,\s]+).*?(\d+)ms", line, re.IGNORECASE)
        if m:
            uid = m.group(1).replace("uid ", "")
            name = m.group(2)
            ms = float(m.group(3))
            wakelocks[uid] += ms
    return wakelocks

def parse_cpu(content):
    cpu_usage = defaultdict(float)
    for line in content.splitlines():
        # e.g. "  u0a123: 123s 456ms usr + 789ms krn"
        m = re.search(r"(u0a\d+|\d+):\s+(\d+)(?:s\s+)?(\d+)ms\s+usr", line)
        if m:
            uid = m.group(1)
            secs = float(m.group(2)) if m.group(2) else 0
            ms = float(m.group(3))
            cpu_usage[uid] += secs * 1000 + ms
    return cpu_usage

def parse_network(content):
    net = defaultdict(lambda: {"sent": 0, "recv": 0})
    for line in content.splitlines():
        # Network stats lines
        m = re.search(r"(u0a\d+|\d+).*?(\d+)B\s+sent.*?(\d+)B\s+recv", line, re.IGNORECASE)
        if m:
            uid = m.group(1)
            net[uid]["sent"] += int(m.group(2))
            net[uid]["recv"] += int(m.group(3))
    return net

def ms_to_human(ms):
    if ms < 1000: return f"{ms:.0f}ms"
    if ms < 60000: return f"{ms/1000:.1f}s"
    if ms < 3600000: return f"{ms/60000:.1f}min"
    return f"{ms/3600000:.1f}h"

def bytes_to_human(b):
    if b < 1024: return f"{b}B"
    if b < 1024**2: return f"{b/1024:.1f}KB"
    return f"{b/1024**2:.1f}MB"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("bugreport", help="Path to bugreport.zip")
    parser.add_argument("--top", type=int, default=15)
    parser.add_argument("--csv", help="Export to CSV")
    args = parser.parse_args()

    print(f"\n🔋 Android Wakelock Analyzer")
    print(f"Parsing {args.bugreport}...")

    content = extract_batterystats(args.bugreport)
    if not content:
        print("Could not find batterystats in bugreport. Try: adb bugreport bugreport.zip")
        sys.exit(1)

    uid_map = parse_uid_map(content)
    wakelocks = parse_wakelocks(content)
    cpu = parse_cpu(content)
    network = parse_network(content)

    # Merge all UIDs
    all_uids = set(list(wakelocks.keys()) + list(cpu.keys()) + list(network.keys()))

    rows = []
    for uid in all_uids:
        pkg = uid_map.get(uid, uid)
        wl_ms = wakelocks.get(uid, 0)
        cpu_ms = cpu.get(uid, 0)
        net_s = network.get(uid, {}).get("sent", 0)
        net_r = network.get(uid, {}).get("recv", 0)
        rows.append((pkg, uid, wl_ms, cpu_ms, net_s, net_r))

    # Sort by wakelock time
    rows.sort(key=lambda x: x[2], reverse=True)
    top = rows[:args.top]

    print(f"\n{'Package':<45} {'Wakelock':<12} {'CPU':<12} {'Net Sent':<12} {'Net Recv'}")
    print("─" * 100)
    for pkg, uid, wl, cpu_t, ns, nr in top:
        print(f"{pkg:<45} {ms_to_human(wl):<12} {ms_to_human(cpu_t):<12} {bytes_to_human(ns):<12} {bytes_to_human(nr)}")

    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Package", "UID", "Wakelock_ms", "CPU_ms", "Net_Sent_B", "Net_Recv_B"])
            for row in rows:
                w.writerow(row)
        print(f"\nExported to {args.csv}")

    print(f"\nTotal packages analyzed: {len(rows)}")

if __name__ == "__main__":
    main()
