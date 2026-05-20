#!/bin/bash
# battery_drain_test.sh -- Systematically test battery drain per app
# Run app in isolation, measure drain rate, identify culprits
# Usage: ./battery_drain_test.sh com.app.package

APP="${1:?Usage: $0 <package.name>}"

echo "🔋 Battery Drain Test — $APP"
echo "=========================================="

adb shell "settings put secure aod_tap_to_show_screen 1"  # AOD on for visibility
sleep 2

# Get initial battery level
INITIAL=$(adb shell "dumpsys battery | grep 'level:' | awk '{print $2}'")
INITIAL_TEMP=$(adb shell "cat /sys/class/thermal/thermal_zone0/temp")

echo "Initial battery: ${INITIAL}%"
echo "Initial temp: ${INITIAL_TEMP}°C"

# Start app
echo "▶️  Launching $APP for 120 seconds..."
adb shell "am start -n $APP/.MainActivity" 2>/dev/null || adb shell "monkey -p $APP 1" >/dev/null 2>&1

# Monitor for 2 minutes
for i in {1..12}; do
  sleep 10
  LEVEL=$(adb shell "dumpsys battery | grep 'level:' | awk '{print $2}'")
  TEMP=$(adb shell "cat /sys/class/thermal/thermal_zone0/temp")
  RATE=$((INITIAL - LEVEL))
  echo "  [$(($i*10))s] Level: ${LEVEL}% (↓${RATE}%) | Temp: ${TEMP}°C"
done

# Force stop
adb shell "am force-stop $APP"
sleep 5

# Final measurement
FINAL=$(adb shell "dumpsys battery | grep 'level:' | awk '{print $2}'")
FINAL_TEMP=$(adb shell "cat /sys/class/thermal/thermal_zone0/temp")

echo ""
echo "Final battery: ${FINAL}%"
echo "Final temp: ${FINAL_TEMP}°C"
echo ""
DRAIN=$((INITIAL - FINAL))
DRAIN_RATE=$(echo "scale=2; $DRAIN / 2" | bc)  # per minute

if (( DRAIN > 5 )); then
  echo "🔴 HIGH DRAIN: ${DRAIN}% in 2min (${DRAIN_RATE}%/min)"
elif (( DRAIN > 2 )); then
  echo "🟡 MODERATE: ${DRAIN}% in 2min"
else
  echo "✅ LOW DRAIN: ${DRAIN}% in 2min"
fi
