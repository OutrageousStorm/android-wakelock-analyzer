# 🔋 Android Wakelock Analyzer

Parse Android bugreports and find what is draining your battery.

## Usage

```bash
# Collect bugreport (takes ~30 seconds)
adb bugreport bugreport.zip

# Analyze
python3 analyze.py bugreport.zip

# Top 20 wakelock holders
python3 analyze.py bugreport.zip --top 20

# Export to CSV
python3 analyze.py bugreport.zip --csv results.csv
```

## What it finds
- Top wakelock holders by time
- Per-app CPU usage
- Per-app network usage (sent/received)
- Alarm wakeups per app
- Total screen-off time vs wakelocked time


## Also includes
- `battery_historian.py` — Generate HTML battery drain report (merged from pixel-battery-historian)
