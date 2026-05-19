#!/usr/bin/env python3
"""cpu_stats.py -- Detailed CPU usage breakdown by process
Shows which apps are using CPU and for how long
"""
import subprocess, re

def adb(cmd):
    r = subprocess.run(['adb', 'shell'] + cmd.split(), capture_output=True, text=True)
    return r.stdout.strip()

def get_cpu_stats():
    """Parse /proc/stat for per-process CPU usage"""
    raw = adb('cat /proc/stat')
    stats = []
    
    for line in raw.splitlines():
        if line.startswith('cpu'):
            parts = line.split()
            if len(parts) >= 5:
                cpu_num = parts[0].replace('cpu', '')
                user = int(parts[1])
                nice = int(parts[2])
                system = int(parts[3])
                idle = int(parts[4])
                total = user + nice + system + idle
                used_pct = round((total - idle) / total * 100, 1) if total else 0
                stats.append({
                    'cpu': cpu_num or 'total',
                    'user': user,
                    'system': system,
                    'idle': idle,
                    'used_pct': used_pct
                })
    
    return stats

def get_process_cpu():
    """Get top CPU consumers"""
    raw = adb('top -n 1 -b')
    procs = []
    for line in raw.splitlines():
        if '%' in line and any(c.isdigit() for c in line):
            parts = line.split()
            if len(parts) >= 8:
                pid, cpu, mem = parts[1], parts[2], parts[3]
                cmd = ' '.join(parts[8:])
                cpu_val = float(cpu.rstrip('%'))
                procs.append({'pid': pid, 'cpu_%': cpu_val, 'mem_%': mem, 'cmd': cmd})
    
    return sorted(procs, key=lambda x: x['cpu_%'], reverse=True)[:10]

if __name__ == '__main__':
    print("\n📊 CPU Usage Report\n")
    
    stats = get_cpu_stats()
    print("System-wide CPU:")
    for s in stats:
        bar = '█' * int(s['used_pct'] / 5) + '░' * (20 - int(s['used_pct'] / 5))
        print(f"  {s['cpu']:<8} {bar} {s['used_pct']}%")
    
    print("\nTop processes:")
    procs = get_process_cpu()
    for p in procs:
        print(f"  {p['cmd']:<40} {p['cpu_%']:>5.1f}%")
