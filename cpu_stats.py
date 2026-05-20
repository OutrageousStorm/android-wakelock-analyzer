#!/usr/bin/env python3
"""Per-process CPU time breakdown"""
import subprocess, re

def adb(cmd):
    return subprocess.run(['adb', 'shell'] + cmd.split(),
                         capture_output=True, text=True).stdout.strip()

raw = adb('cat /proc/stat')
total = sum(int(x) for x in raw.split()[1:8])

print("\nPer-process CPU usage:\n")
for line in adb('top -n 1 -o %CPU').splitlines()[1:6]:
    parts = line.split()
    if len(parts) > 0:
        print(f"  {parts[-1]:<40} {parts[0]:>6}")
