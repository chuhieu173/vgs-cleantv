#!/usr/bin/env bash
set -euo pipefail

TV_IP="${1:-192.168.10.14:5555}"
APK_PATH="$(cd "$(dirname "$0")/.." && pwd)/SonyKeepAlive.apk"
SVC="zone.vgs.cleantv.keepalive/zone.vgs.keepalive.KeepAliveService"

echo "1. Kết nối tới TV ($TV_IP)..."
adb connect "$TV_IP" || true

echo "2. Cài đặt SonyKeepAlive.apk (8 KB)..."
adb -s "$TV_IP" install -r "$APK_PATH"

echo "3. Tự động bật dịch vụ Trợ năng KeepAliveService..."
CUR="$(adb -s "$TV_IP" shell settings get secure enabled_accessibility_services | tr -d '\r\n')"
if [[ -z "$CUR" || "$CUR" == "null" ]]; then
    NEW="$SVC"
elif [[ ":$CUR:" == *":$SVC:"* ]]; then
    NEW="$CUR"
else
    NEW="$CUR:$SVC"
fi
adb -s "$TV_IP" shell "settings put secure enabled_accessibility_services '$NEW' && settings put secure accessibility_enabled 1"

sleep 2
echo "4. Kiểm tra WakeLock trên TV:"
adb -s "$TV_IP" shell "dumpsys power | grep -A 8 'Wake Locks:'"
