#!/usr/bin/env python3
"""Real-time Android performance monitor — tracks battery drain, CPU/GPU load per app"""
import subprocess, time, argparse, curses, threading

def adb(cmd):
    r = subprocess.run(['adb', 'shell'] + cmd.split(), capture_output=True, text=True)
    return r.stdout.strip()

def get_battery():
    raw = adb('dumpsys battery')
    for line in raw.splitlines():
        if 'level:' in line: return int(line.split(':')[1].strip())
    return 0

def get_top_apps_by_cpu():
    raw = adb('top -n 1')
    apps = []
    for line in raw.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 9 and parts[0].isdigit():
            apps.append({'pid': parts[0], 'cpu': parts[2], 'mem': parts[4]})
    return apps

def get_top_apps_by_memory():
    raw = adb('dumpsys meminfo | head -20')
    return raw

def monitor(interval=2, duration=60):
    start_bat = get_battery()
    print(f"🔋 Starting battery: {start_bat}%")
    print(f"📊 Monitor running for {duration}s (updates every {interval}s)\n")
    
    samples = []
    for i in range(duration // interval):
        bat = get_battery()
        drain = start_bat - bat
        top_apps = get_top_apps_by_cpu()
        
        samples.append({'time': i, 'battery': bat, 'drain': drain, 'apps': top_apps[:3]})
        
        print(f"[{i*interval:3d}s] Battery: {bat}% ({drain:+d}%) | Top apps: ", end='')
        for app in top_apps[:2]:
            print(f"{app['pid']} ({app['cpu']}%) ", end='')
        print()
        
        time.sleep(interval)
    
    if drain > 0:
        drain_rate = drain / (duration / 60)
        print(f"\nTotal drain: {drain}% in {duration}s ({drain_rate:.1f}%/min)")
        print("High drain detected — run: adb shell dumpsys batterystats --reset")

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=int, default=60, help='Monitor duration in seconds')
    parser.add_argument('--interval', type=int, default=2, help='Update interval')
    args = parser.parse_args()
    monitor(args.interval, args.duration)
