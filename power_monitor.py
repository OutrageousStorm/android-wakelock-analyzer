#!/usr/bin/env python3
"""
power_monitor.py -- Real-time power consumption monitor
Shows: CPU freq/usage, temp, battery drain rate, per-app battery %
Usage: python3 power_monitor.py [--interval 2]
"""
import subprocess, re, time, argparse
from datetime import datetime

def adb(cmd):
    return subprocess.run(f"adb shell {cmd}", shell=True, capture_output=True, text=True).stdout.strip()

def get_cpu_freq():
    """CPU frequency in MHz"""
    try:
        freq_hz = int(adb("cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq"))
        return freq_hz // 1000
    except:
        return 0

def get_cpu_usage():
    """Rough CPU usage %"""
    try:
        raw = adb("cat /proc/stat | head -1")
        return raw
    except:
        return "N/A"

def get_temp():
    """Temperature in Celsius"""
    try:
        temp_mc = int(adb("cat /sys/class/thermal/thermal_zone0/temp"))
        return temp_mc // 1000
    except:
        return "?"

def get_battery():
    """Battery level, temp, voltage"""
    raw = adb("dumpsys battery")
    data = {}
    for line in raw.splitlines():
        if "level:" in line:
            data['level'] = line.split(":")[-1].strip()
        elif "temperature:" in line:
            data['temp'] = line.split(":")[-1].strip()
        elif "voltage:" in line:
            data['voltage'] = line.split(":")[-1].strip()
        elif "charge counter:" in line:
            data['counter'] = line.split(":")[-1].strip()
    return data

def get_per_app_usage():
    """Top battery drains from dumpsys"""
    raw = adb("dumpsys batterystats --statistics")
    apps = []
    for line in raw.splitlines():
        if "uid" in line and "%" in line:
            m = re.search(r'uid[\s:]+(\S+).*?([\d.]+)%', line)
            if m:
                apps.append((m.group(1), m.group(2)))
    return sorted(apps, key=lambda x: float(x[1]), reverse=True)[:5]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval", type=int, default=2)
    args = parser.parse_args()

    print("\n⚡ Power Monitor — press Ctrl+C to stop\n")
    try:
        while True:
            ts = datetime.now().strftime("%H:%M:%S")
            freq = get_cpu_freq()
            temp = get_temp()
            bat = get_battery()
            apps = get_per_app_usage()

            print(f"[{ts}]")
            print(f"  CPU: {freq} MHz | Temp: {temp}°C")
            print(f"  Battery: {bat.get('level','?')}% | {bat.get('temp','?')}°C | {bat.get('voltage','?')}mV")
            if apps:
                print(f"  Top drain: {apps[0][0]} ({apps[0][1]}%)")
            print()
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("Stopped.")

if __name__ == "__main__":
    main()
