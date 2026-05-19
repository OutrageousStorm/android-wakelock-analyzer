#!/usr/bin/env python3
"""
wakelockd.py — Background daemon that monitors wakelock activity
and alerts when an app is draining battery via excessive wakelocks

Usage:
  python3 wakelockd.py               # monitor continuously
  python3 wakelockd.py --threshold 5 # alert if wakelock held > 5 min
  python3 wakelockd.py --report      # print current state and exit
  python3 wakelockd.py --export log.csv
"""
import subprocess, time, re, argparse, csv, json
from datetime import datetime
from collections import defaultdict

WAKELOCK_RE = re.compile(r"Wake lock u\d+\s+(.+?):\s+(.+)")
HELD_RE = re.compile(r"PARTIAL_WAKE_LOCK\s+'(.+?)'\s+(.+?) acquired=(.+?) held=(.+?) flags=")

def adb(cmd):
    r = subprocess.run(['adb', 'shell'] + cmd.split(), capture_output=True, text=True)
    return r.stdout.strip()

def parse_wakelocks():
    raw = adb('dumpsys power')
    locks = []
    for line in raw.splitlines():
        line = line.strip()
        if 'PARTIAL_WAKE_LOCK' in line:
            m = re.search(r"'([^']+)'.*?held=(\d+)ms", line)
            if m:
                name = m.group(1)
                held_ms = int(m.group(2))
                pkg = name.split(':')[0] if ':' in name else name
                locks.append({'name': name, 'package': pkg, 'held_ms': held_ms})
    return locks

def get_screen_state():
    raw = adb('dumpsys power')
    if 'mWakefulness=Awake' in raw: return 'awake'
    if 'mWakefulness=Asleep' in raw: return 'asleep'
    return 'unknown'

def summarize(locks):
    by_pkg = defaultdict(int)
    for lock in locks:
        by_pkg[lock['package']] += lock['held_ms']
    return sorted(by_pkg.items(), key=lambda x: x[1], reverse=True)

def format_duration(ms):
    s = ms // 1000
    if s < 60: return f"{s}s"
    m = s // 60
    if m < 60: return f"{m}m {s%60}s"
    return f"{m//60}h {m%60}m"

def report():
    locks = parse_wakelocks()
    summary = summarize(locks)
    screen = get_screen_state()
    print(f"\n📱 Screen: {screen.upper()} | {datetime.now().strftime('%H:%M:%S')}")
    print(f"🔒 Active wakelocks: {len(locks)}\n")
    for pkg, held_ms in summary[:15]:
        bar_len = min(30, held_ms // 60000)
        bar = '█' * bar_len
        flag = ' ⚠️' if held_ms > 300000 else ''  # warn if > 5 min
        print(f"  {bar:<30} {format_duration(held_ms):>8}  {pkg}{flag}")
    return locks, summary

def monitor(threshold_min=5, interval=30, export_file=None):
    print(f"🔍 wakelockd started — alerting on wakelocks > {threshold_min} min | polling every {interval}s")
    print("Press Ctrl+C to stop\n")
    
    csv_out = None
    if export_file:
        csv_out = open(export_file, 'w', newline='')
        writer = csv.writer(csv_out)
        writer.writerow(['timestamp', 'package', 'held_ms', 'held_fmt'])
    
    seen_alerts = set()
    threshold_ms = threshold_min * 60 * 1000
    
    try:
        while True:
            locks, summary = report()
            ts = datetime.now().isoformat()
            
            for pkg, held_ms in summary:
                if held_ms > threshold_ms and pkg not in seen_alerts:
                    print(f"\n⚠️  ALERT: {pkg} has held wakelock for {format_duration(held_ms)}!")
                    seen_alerts.add(pkg)
                elif held_ms <= threshold_ms and pkg in seen_alerts:
                    seen_alerts.discard(pkg)
                
                if csv_out:
                    writer.writerow([ts, pkg, held_ms, format_duration(held_ms)])
                    csv_out.flush()
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nwakelockd stopped.")
        if csv_out: csv_out.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Android wakelock monitoring daemon')
    parser.add_argument('--threshold', type=int, default=5, help='Alert threshold in minutes (default: 5)')
    parser.add_argument('--interval', type=int, default=30, help='Poll interval in seconds (default: 30)')
    parser.add_argument('--report', action='store_true', help='Print once and exit')
    parser.add_argument('--export', metavar='FILE', help='Export log to CSV file')
    args = parser.parse_args()
    
    if args.report:
        report()
    else:
        monitor(threshold_min=args.threshold, interval=args.interval, export_file=args.export)
